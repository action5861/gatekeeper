# app.py
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, cast
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError
import httpx
import logging
import os

# ----------------------------- 로깅 -----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("api-gateway")

# ----------------------------- 앱/미들웨어 -----------------------------
app = FastAPI(title="API Gateway", version="1.1.0")

# CORS: 배포에서는 반드시 명시적 오리진만 허용
_allow_origins_env = os.getenv("CORS_ALLOW_ORIGINS")
allow_origins = (
    [o.strip() for o in _allow_origins_env.split(",") if o.strip()]
    if _allow_origins_env
    else ["http://localhost:3000"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------- 보안/JWT -----------------------------
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "환경변수 JWT_SECRET_KEY 가 설정되지 않았습니다. 배포/개발 환경 변수로 반드시 주입하세요."
    )

# 타입 체커를 위한 명시적 캐스팅
SECRET_KEY = cast(str, SECRET_KEY)

ALGORITHM = os.getenv("JWT_ALG", "HS256")
JWT_ISSUER = os.getenv("JWT_ISSUER")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE")
security = HTTPBearer(auto_error=True)


class ErrorResponse(BaseModel):
    detail: str
    error_code: str


def _mask(s: Optional[str]) -> str:
    if not s:
        return ""
    return s[:6] + "..." + s[-4:] if len(s) > 12 else "***"


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """
    JWT 토큰 검증 (exp 필수, 선택적으로 iss/aud 검증)
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            cast(str, SECRET_KEY),  # 명시적 타입 캐스팅
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE if JWT_AUDIENCE else None,
            issuer=JWT_ISSUER if JWT_ISSUER else None,
            options={
                "require_exp": True,
                "verify_aud": bool(JWT_AUDIENCE),
                "verify_iss": bool(JWT_ISSUER),
            },
        )
        return payload
    except ExpiredSignatureError:
        logger.info("토큰 만료: %s", _mask(token))
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        logger.info("토큰 오류: %s", _mask(token))
        raise HTTPException(status_code=401, detail="Invalid token")


async def optional_auth(request: Request) -> Optional[dict]:
    """
    인증이 선택적인 경우에 사용 (현재 파일에서는 미사용이지만 필요 시 종속성으로 활용)
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return None
    token = auth_header.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(
            token,
            cast(str, SECRET_KEY),  # 명시적 타입 캐스팅
            algorithms=[ALGORITHM],
            audience=JWT_AUDIENCE if JWT_AUDIENCE else None,
            issuer=JWT_ISSUER if JWT_ISSUER else None,
            options={
                "require_exp": True,
                "verify_aud": bool(JWT_AUDIENCE),
                "verify_iss": bool(JWT_ISSUER),
            },
        )
        return payload
    except Exception:
        return None


# ----------------------------- 서비스 URL -----------------------------
SERVICE_URLS = {
    "user": os.getenv("USER_SERVICE_URL", "http://localhost:8005"),
    "advertiser": os.getenv("ADVERTISER_SERVICE_URL", "http://localhost:8007"),
    "auction": os.getenv("AUCTION_SERVICE_URL", "http://localhost:8002"),
    "payment": os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8003"),
    "settlement": os.getenv("SETTLEMENT_SERVICE_URL", "http://localhost:8008"),
    "quality": os.getenv("QUALITY_SERVICE_URL", "http://localhost:8006"),
    "analysis": os.getenv("ANALYSIS_SERVICE_URL", "http://localhost:8001"),
    "verification": os.getenv("VERIFICATION_SERVICE_URL", "http://localhost:8004"),
}


# ----------------------------- 프록시 공통 -----------------------------
# RFC7230 hop-by-hop 헤더 (게이트웨이가 전달 금지)
HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "trailers",
    "transfer-encoding",
    "upgrade",
    "content-length",
}

IDEMPOTENT_METHODS = {"GET", "HEAD", "OPTIONS"}


def _collect_forward_headers(
    request: Optional[Request], auth_required: bool
) -> Dict[str, str]:
    """
    업스트림으로 전달할 헤더를 선별 수집.
    - 보존: Authorization(필요시), Accept, Accept-Language, User-Agent, Content-Type, Cookie
    - 추적: X-Request-ID, traceparent 등 있으면 전달
    """
    headers: Dict[str, str] = {}
    if not request:
        return headers

    # 공통
    for k in ("accept", "accept-language", "user-agent", "content-type", "cookie"):
        v = request.headers.get(k)
        if v:
            headers[k] = v

    # 인증
    if auth_required:
        auth = request.headers.get("authorization")
        if auth:
            headers["authorization"] = auth

    # 추적 헤더
    for k in (
        "x-request-id",
        "traceparent",
        "tracestate",
        "x-b3-traceid",
        "x-b3-spanid",
    ):
        v = request.headers.get(k)
        if v:
            headers[k] = v

    return headers


async def proxy_request(
    service_name: str,
    path: str,
    method: str = "GET",
    data: Optional[dict] = None,
    auth_required: bool = True,
    request: Optional[Request] = None,
) -> Response:
    """
    요청을 해당 마이크로서비스로 전달하고, 원 응답을 최대한 보존하여 반환
    - 쿼리스트링 전달(params)
    - 원본 content-type/Set-Cookie 보존
    - hop-by-hop 헤더 제거
    - GET 등 아이들포턴트 메서드 1회 재시도
    """
    if service_name not in SERVICE_URLS:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    base = SERVICE_URLS[service_name].rstrip("/")
    url = f"{base}{path}"

    headers = _collect_forward_headers(request, auth_required=auth_required)
    params = dict(request.query_params) if request else None

    timeout = httpx.Timeout(connect=5.0, read=15.0, write=15.0, pool=5.0)
    attempts = 2 if method.upper() in IDEMPOTENT_METHODS else 1

    last_exc: Optional[Exception] = None
    async with httpx.AsyncClient(timeout=timeout) as client:
        for attempt in range(1, attempts + 1):
            try:
                req_kwargs: Dict[str, Any] = {"headers": headers, "params": params}
                upper = method.upper()
                if upper in {"POST", "PUT", "PATCH"}:
                    req_kwargs["json"] = data if data is not None else {}

                resp = await client.request(upper, url, **req_kwargs)

                # 응답 가공
                media_type = resp.headers.get("content-type")
                # hop-by-hop 제거 및 set-cookie 분리
                out_headers = {
                    k: v
                    for k, v in resp.headers.items()
                    if k.lower() not in HOP_BY_HOP and k.lower() != "set-cookie"
                }

                # 원본 바이트 그대로 전달
                out = Response(
                    content=resp.content,
                    status_code=resp.status_code,
                    media_type=media_type,
                    headers=out_headers,
                )

                # Set-Cookie 복수 헤더 보존
                try:
                    for cookie in resp.headers.get_list("set-cookie"):
                        out.headers.append("set-cookie", cookie)
                except Exception:
                    # httpx 버전별 get_list 미지원 시 보수 처리
                    sc = resp.headers.get("set-cookie")
                    if sc:
                        out.headers.append("set-cookie", sc)

                return out

            except httpx.RequestError as e:
                last_exc = e
                logger.error(
                    "업스트림 서비스 연결 오류 (service=%s, url=%s, attempt=%d/%d): %s",
                    service_name,
                    url,
                    attempt,
                    attempts,
                    repr(e),
                )
                if attempt >= attempts:
                    raise HTTPException(
                        status_code=503, detail=f"Service {service_name} is unavailable"
                    ) from e

            except Exception as e:
                logger.exception(
                    "프록시 처리 중 예외 (service=%s, url=%s): %s",
                    service_name,
                    url,
                    repr(e),
                )
                raise HTTPException(
                    status_code=500, detail="Internal server error"
                ) from e

    # 논리적으로 도달 불가
    raise HTTPException(status_code=500, detail="Internal proxy error")


# ----------------------------- 라우트 정의 -----------------------------
# 사용자 서비스
@app.post("/api/auth/register")
async def register_user(request: Request):
    body = await request.json()

    # Check if this is an advertiser registration
    if body.get("userType") == "advertiser":
        # Transform the data for advertiser service
        import re

        email_username = body["email"].replace("@", "_at_")
        email_username = re.sub(r"[^a-zA-Z0-9_가-힣]", "_", email_username)

        # Convert categories to numeric if they are strings
        business_setup = body.get("businessSetup", {})
        categories = business_setup.get("categories", [])
        numeric_categories = [int(c) if isinstance(c, str) else c for c in categories]

        transformed_body = {
            "username": email_username,
            "email": body["email"],
            "password": body["password"],
            "company_name": body["companyName"],
            "business_setup": {
                **business_setup,
                "categories": numeric_categories,
            },
        }

        return await proxy_request(
            "advertiser",
            "/register",
            "POST",
            data=transformed_body,
            auth_required=False,
            request=request,
        )
    else:
        return await proxy_request(
            "user", "/register", "POST", data=body, auth_required=False, request=request
        )


@app.post("/api/auth/login")
async def login_user(request: Request):
    body = await request.json()
    return await proxy_request(
        "user", "/login", "POST", data=body, auth_required=False, request=request
    )


@app.post("/api/user/update-daily-submission", dependencies=[Depends(verify_token)])
async def update_daily_submission(request: Request):
    body = await request.json()
    return await proxy_request(
        "user",
        "/update-daily-submission",
        "POST",
        data=body,
        auth_required=True,
        request=request,
    )


@app.get("/api/user/dashboard", dependencies=[Depends(verify_token)])
async def get_user_dashboard(request: Request):
    return await proxy_request(
        "user", "/dashboard", "GET", auth_required=True, request=request
    )


@app.post("/api/user/earnings", dependencies=[Depends(verify_token)])
async def update_user_earnings(request: Request):
    body = await request.json()
    return await proxy_request(
        "user",
        "/api/user/earnings",
        "POST",
        data=body,
        auth_required=True,
        request=request,
    )


# 광고주 서비스
@app.post("/api/advertiser/register")
async def register_advertiser(request: Request):
    body = await request.json()
    return await proxy_request(
        "advertiser",
        "/register",
        "POST",
        data=body,
        auth_required=False,
        request=request,
    )


@app.post("/api/advertiser/login")
async def login_advertiser(request: Request):
    body = await request.json()
    return await proxy_request(
        "advertiser", "/login", "POST", data=body, auth_required=False, request=request
    )


@app.get("/api/advertiser/dashboard", dependencies=[Depends(verify_token)])
async def get_advertiser_dashboard(request: Request):
    return await proxy_request(
        "advertiser", "/dashboard", "GET", auth_required=True, request=request
    )


@app.get("/api/advertiser/status", dependencies=[Depends(verify_token)])
async def get_advertiser_status(request: Request):
    return await proxy_request(
        "advertiser", "/status", "GET", auth_required=True, request=request
    )


@app.get("/api/advertiser/ai-suggestions", dependencies=[Depends(verify_token)])
async def get_ai_suggestions(request: Request):
    return await proxy_request(
        "advertiser", "/ai-suggestions", "GET", auth_required=True, request=request
    )


@app.post("/api/advertiser/confirm-suggestions", dependencies=[Depends(verify_token)])
async def confirm_suggestions(request: Request):
    body = await request.json()
    return await proxy_request(
        "advertiser",
        "/confirm-suggestions",
        "POST",
        data=body,
        auth_required=True,
        request=request,
    )


# 경매 서비스
@app.post("/api/auction/start", dependencies=[Depends(verify_token)])
async def start_auction(request: Request):
    body = await request.json()
    return await proxy_request(
        "auction", "/start", "POST", data=body, auth_required=True, request=request
    )


@app.get("/api/auction/{search_id}", dependencies=[Depends(verify_token)])
async def get_auction_status(search_id: str, request: Request):
    return await proxy_request(
        "auction", f"/{search_id}", "GET", auth_required=True, request=request
    )


@app.get("/api/auction/search/{search_id}", dependencies=[Depends(verify_token)])
async def get_search_query(search_id: str, request: Request):
    return await proxy_request(
        "auction", f"/search/{search_id}", "GET", auth_required=True, request=request
    )


@app.post("/api/auction/select", dependencies=[Depends(verify_token)])
async def select_bid(request: Request):
    body = await request.json()
    return await proxy_request(
        "auction", "/select", "POST", data=body, auth_required=True, request=request
    )


@app.get("/api/auction/bid/{bid_id}", dependencies=[Depends(verify_token)])
async def get_bid_info(bid_id: str, request: Request):
    return await proxy_request(
        "auction", f"/bid/{bid_id}", "GET", auth_required=True, request=request
    )


# 결제 서비스
@app.post("/api/payment/reward", dependencies=[Depends(verify_token)])
async def process_reward(request: Request):
    body = await request.json()
    return await proxy_request(
        "payment", "/reward", "POST", data=body, auth_required=True, request=request
    )


@app.get("/api/redirect/{bid_id}")
async def redirect_click(bid_id: str, request: Request, sig: str):
    """
    클릭 리다이렉트 엔드포인트 - 검증 → 적립 → 302 리다이렉트
    """
    from fastapi.responses import RedirectResponse
    import httpx
    import os

    logger.info(f"🔄 Redirect click received for bid_id: {bid_id}, sig: {sig}")

    try:
        # 1) 검증 서비스에서 클릭 검증
        verify_url = f"{SERVICE_URLS['verification']}/verify-click"
        async with httpx.AsyncClient(timeout=5.0) as client:
            verify_response = await client.post(
                verify_url, json={"bidId": bid_id, "sig": sig}
            )

        if verify_response.status_code != 200:
            logger.error(f"Click verification failed: {verify_response.status_code}")
            raise HTTPException(status_code=400, detail="Invalid click")

        verify_data = verify_response.json()
        logger.info(f"✅ Click verified: {verify_data}")

        # 2) 적립 처리 (payment 서비스)
        award_url = f"{SERVICE_URLS['payment']}/award"
        try:
            auth = request.headers.get("Authorization")
            headers = {"Authorization": auth} if auth else None

            async with httpx.AsyncClient(timeout=5.0) as client:
                award_response = await client.post(
                    award_url,
                    json={
                        "userId": verify_data["userId"],
                        "bidId": bid_id,
                        "type": verify_data["type"],
                        "amount": verify_data["payout"],
                        "reason": "click",
                    },
                    headers=headers,
                )

            if award_response.status_code == 200:
                logger.info(f"✅ Award successful: {award_response.json()}")
            else:
                logger.error(f"Award failed: {award_response.status_code}")

        except Exception as e:
            logger.error(f"Award failed: {e}")
            # 적립 실패해도 리다이렉트는 진행 (UX 보장)

        # 3) 최종 이동
        destination = verify_data["destination"]
        logger.info(f"🔄 Redirecting to: {destination}")
        return RedirectResponse(url=destination, status_code=302)

    except Exception as e:
        logger.exception(f"Redirect error: {e}")
        # 오류 발생 시 기본 URL로 리다이렉트
        return RedirectResponse(url="https://www.google.com", status_code=302)


# 품질 서비스
@app.post("/api/quality/calculate-limit", dependencies=[Depends(verify_token)])
async def calculate_submission_limit(request: Request):
    body = await request.json()
    return await proxy_request(
        "quality",
        "/calculate-limit",
        "POST",
        data=body,
        auth_required=True,
        request=request,
    )


# 분석 서비스
@app.post("/api/analysis/evaluate", dependencies=[Depends(verify_token)])
async def evaluate_quality(request: Request):
    body = await request.json()
    return await proxy_request(
        "analysis", "/evaluate", "POST", data=body, auth_required=True, request=request
    )


# 품질 평가 전용 엔드포인트 (인증 없음)
@app.post("/api/analysis/evaluate-quality")
async def evaluate_quality_no_auth(request: Request):
    body = await request.json()
    return await proxy_request(
        "analysis", "/evaluate", "POST", data=body, auth_required=False, request=request
    )


# 검증 서비스
@app.post("/api/verify", dependencies=[Depends(verify_token)])
async def verify_user(request: Request):
    body = await request.json()
    return await proxy_request(
        "verification",
        "/verify",
        "POST",
        data=body,
        auth_required=True,
        request=request,
    )


@app.post("/api/verify/claim", dependencies=[Depends(verify_token)])
async def claim_reward(request: Request):
    body = await request.json()
    return await proxy_request(
        "verification", "/claim", "POST", data=body, auth_required=True, request=request
    )


@app.post("/api/verification/verify-delivery", dependencies=[Depends(verify_token)])
async def verify_delivery(request: Request):
    """SLA 검증 요청을 Verification Service로 전달"""
    body = await request.json()
    return await proxy_request(
        "verification",
        "/verify-delivery",
        "POST",
        data=body,
        auth_required=True,
        request=request,
    )


@app.post("/api/verification/update-pending-return")
async def update_pending_return(request: Request):
    """1차 평가: PENDING_RETURN 상태 업데이트 (내부 서비스간 통신용)"""
    body = await request.json()
    return await proxy_request(
        "verification",
        "/update-pending-return",
        "POST",
        data=body,
        auth_required=False,  # 서비스간 통신
        request=request,
    )


@app.post("/api/verification/verify-return", dependencies=[Depends(verify_token)])
async def verify_return(request: Request):
    """2차 평가: 사용자 복귀 시 체류 시간 기반 최종 평가"""
    body = await request.json()
    return await proxy_request(
        "verification",
        "/verify-return",
        "POST",
        data=body,
        auth_required=True,
        request=request,
    )


# Settlement Service
@app.post("/api/settlement/settle-trade")
async def settle_trade(request: Request):
    """정산 요청을 Settlement Service로 전달 (내부 서비스간 통신용)"""
    body = await request.json()
    return await proxy_request(
        "settlement",
        "/settle-trade",
        "POST",
        data=body,
        auth_required=False,  # 서비스간 통신
        request=request,
    )


# [LIVE] Dashboard metrics endpoints
from fastapi import APIRouter, Depends, HTTPException
from jose import jwt, JWTError
from databases import Database
from datetime import datetime, timedelta, timezone


# Database connection (assuming it's available)
async def get_db():
    # This should be replaced with actual database connection
    # For now, we'll use the existing proxy pattern
    pass


KST = timezone(timedelta(hours=9))


def get_user_id_from_token(auth_header: str) -> int:
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.get_unverified_claims(token)
        # 토큰에 포함된 user_id/email 등 프로젝트 규격에 맞춰 수정
        return int(payload.get("user_id") or payload.get("sub_id") or 1)
    except JWTError:  # 필요 시 검증용 키 적용
        raise HTTPException(status_code=401, detail="Invalid token")


# [LIVE] 테이블 존재 체크
async def has_table(db: Database, table: str) -> bool:
    row = await db.fetch_one(
        """
      SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema='public' AND table_name=:t
      ) AS ok
    """,
        {"t": table},
    )
    return bool(row and row["ok"])


@app.get("/api/dashboard/summary")
async def get_dashboard_summary(request: Request):
    """대시보드 요약 정보 - 평균 품질 점수, 성공률, 오늘의 입찰/보상 정보"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header required")
    user_id = get_user_id_from_token(auth_header)

    # User service로 프록시 (실제 DB 쿼리는 user service에서 처리)
    return await proxy_request(
        "user", "/dashboard/summary", "GET", auth_required=True, request=request
    )


@app.get("/api/dashboard/quality-history")
async def get_quality_history(request: Request):
    """품질 이력 데이터 - 최근 14일 일자별 평균 품질"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await proxy_request(
        "user", "/dashboard/quality-history", "GET", auth_required=True, request=request
    )


@app.get("/api/dashboard/transactions")
async def get_transactions(request: Request):
    """거래 내역 - 최근 50개 트랜잭션"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await proxy_request(
        "user", "/dashboard/transactions", "GET", auth_required=True, request=request
    )


@app.get("/api/dashboard/realtime")
async def get_realtime(request: Request):
    """실시간 통계 - 최근 10분 활동"""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Authorization header required")
    return await proxy_request(
        "user", "/dashboard/realtime", "GET", auth_required=True, request=request
    )


# 헬스체크
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "api-gateway"}


# ----------------------------- 에러 핸들러 -----------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # 민감헤더 마스킹
    masked_auth = _mask(request.headers.get("authorization", ""))
    logger.info(
        "HTTPException %s %s -> %d (auth=%s)",
        request.method,
        request.url.path,
        exc.status_code,
        masked_auth,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=str(exc.detail), error_code=f"HTTP_{exc.status_code}"
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    masked_auth = _mask(request.headers.get("authorization", ""))
    logger.exception(
        "Unhandled exception %s %s (auth=%s): %r",
        request.method,
        request.url.path,
        masked_auth,
        exc,
    )
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            detail="Internal server error", error_code="INTERNAL_ERROR"
        ).model_dump(),
    )


# ----------------------------- 실행 -----------------------------
if __name__ == "__main__":
    import uvicorn

    # 환경에 맞게 포트/host 조정
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
