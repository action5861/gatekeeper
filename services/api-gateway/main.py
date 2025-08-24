from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import httpx
import os
from jose import jwt, JWTError, ExpiredSignatureError
from typing import Optional
from pydantic import BaseModel
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Gateway", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 보안 설정
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production"
)
ALGORITHM = "HS256"
security = HTTPBearer()

# 서비스 URL 설정 (실제 포트 매핑에 맞게 수정)
SERVICE_URLS = {
    "user": os.getenv("USER_SERVICE_URL", "http://localhost:8005"),
    "advertiser": os.getenv("ADVERTISER_SERVICE_URL", "http://localhost:8007"),
    "auction": os.getenv("AUCTION_SERVICE_URL", "http://localhost:8002"),
    "payment": os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8003"),
    "quality": os.getenv("QUALITY_SERVICE_URL", "http://localhost:8006"),
    "analysis": os.getenv("ANALYSIS_SERVICE_URL", "http://localhost:8001"),
    "verification": os.getenv("VERIFICATION_SERVICE_URL", "http://localhost:8004"),
}


# Pydantic 모델
class ErrorResponse(BaseModel):
    detail: str
    error_code: str


# JWT 토큰 검증 함수
async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """JWT 토큰을 검증하고 페이로드를 반환합니다."""
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        return payload
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# 인증이 필요한 엔드포인트용 의존성
async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """인증이 필요한 엔드포인트에서 사용하는 의존성"""
    return await verify_token(credentials)


# 인증이 선택적인 엔드포인트용 의존성
async def optional_auth(request: Request) -> Optional[dict]:
    """인증이 선택적인 엔드포인트에서 사용하는 의존성"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    try:
        token = auth_header.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        return None


# 프록시 함수
async def proxy_request(
    service_name: str,
    path: str,
    method: str = "GET",
    data: Optional[dict] = None,
    auth_required: bool = True,
    request: Optional[Request] = None,
) -> JSONResponse:
    """요청을 해당 서비스로 프록시합니다."""

    if service_name not in SERVICE_URLS:
        raise HTTPException(status_code=404, detail=f"Service {service_name} not found")

    service_url = SERVICE_URLS[service_name]
    target_url = f"{service_url}{path}"

    # 인증이 필요한 경우 토큰 검증
    headers = {}
    if auth_required and request:
        auth_header = request.headers.get("Authorization")
        if auth_header:
            headers["Authorization"] = auth_header

    # Content-Type 헤더 추가
    if data:
        headers["Content-Type"] = "application/json"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(target_url, headers=headers)
            elif method.upper() == "POST":
                response = await client.post(target_url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = await client.put(target_url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = await client.delete(target_url, headers=headers)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")

            return JSONResponse(
                content=(
                    response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else response.text
                ),
                status_code=response.status_code,
                headers=dict(response.headers),
            )

    except httpx.RequestError as e:
        logger.error(f"Service {service_name} connection error: {e}")
        raise HTTPException(
            status_code=503, detail=f"Service {service_name} is unavailable"
        )
    except Exception as e:
        logger.error(f"Proxy error for {service_name}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# 라우트 정의


# 사용자 서비스 라우트
@app.post("/api/auth/register")
async def register_user(request: Request):
    """사용자 등록 (인증 불필요)"""
    body = await request.json()
    return await proxy_request("user", "/register", "POST", body, auth_required=False)


@app.post("/api/user/update-daily-submission")
async def update_daily_submission(request: Request):
    """일일 제출 카운트 업데이트 (인증 필요)"""
    body = await request.json()
    return await proxy_request(
        "user",
        "/update-daily-submission",
        "POST",
        body,
        auth_required=True,
        request=request,
    )


@app.post("/api/auth/login")
async def login_user(request: Request):
    """사용자 로그인 (인증 불필요)"""
    body = await request.json()
    return await proxy_request("user", "/login", "POST", body, auth_required=False)


@app.get("/api/user/dashboard")
async def get_user_dashboard(request: Request):
    """사용자 대시보드 (인증 필요)"""
    return await proxy_request(
        "user", "/dashboard", "GET", auth_required=True, request=request
    )


# 광고주 서비스 라우트
@app.post("/api/advertiser/register")
async def register_advertiser(request: Request):
    """광고주 등록 (인증 불필요)"""
    body = await request.json()
    return await proxy_request(
        "advertiser", "/register", "POST", body, auth_required=False
    )


@app.post("/api/advertiser/login")
async def login_advertiser(request: Request):
    """광고주 로그인 (인증 불필요)"""
    body = await request.json()
    return await proxy_request(
        "advertiser", "/login", "POST", body, auth_required=False
    )


@app.get("/api/advertiser/dashboard")
async def get_advertiser_dashboard(request: Request):
    """광고주 대시보드 (인증 필요)"""
    return await proxy_request(
        "advertiser", "/dashboard", "GET", auth_required=True, request=request
    )


# 경매 서비스 라우트
@app.post("/api/auction/start")
async def start_auction(request: Request):
    """경매 시작 (인증 필요)"""
    body = await request.json()
    return await proxy_request(
        "auction", "/start", "POST", body, auth_required=True, request=request
    )


@app.get("/api/auction/{search_id}")
async def get_auction_status(search_id: str, request: Request):
    """경매 상태 조회 (인증 필요)"""
    return await proxy_request(
        "auction", f"/{search_id}", "GET", auth_required=True, request=request
    )


# 결제 서비스 라우트
@app.post("/api/payment/reward")
async def process_reward(request: Request):
    """보상 처리 (인증 필요)"""
    body = await request.json()
    return await proxy_request(
        "payment", "/reward", "POST", body, auth_required=True, request=request
    )


# 품질 서비스 라우트
@app.post("/api/quality/calculate-limit")
async def calculate_submission_limit(request: Request):
    """제출 한도 계산 (인증 필요)"""
    body = await request.json()
    return await proxy_request(
        "quality", "/calculate-limit", "POST", body, auth_required=True, request=request
    )


# 분석 서비스 라우트
@app.post("/api/analysis/evaluate")
async def evaluate_quality(request: Request):
    """품질 평가 (인증 필요)"""
    body = await request.json()
    return await proxy_request(
        "analysis", "/evaluate", "POST", body, auth_required=True, request=request
    )


# 검증 서비스 라우트
@app.post("/api/verify")
async def verify_user(request: Request):
    """사용자 검증 (인증 필요)"""
    body = await request.json()
    return await proxy_request(
        "verification", "/verify", "POST", body, auth_required=True, request=request
    )


@app.post("/api/verify/claim")
async def claim_reward(request: Request):
    """보상 청구 (인증 필요)"""
    body = await request.json()
    return await proxy_request(
        "verification", "/claim", "POST", body, auth_required=True, request=request
    )


# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """API Gateway 상태 확인"""
    return {"status": "healthy", "service": "api-gateway"}


# 에러 핸들러
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "error_code": f"HTTP_{exc.status_code}"},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
