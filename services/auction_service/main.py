from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Any, Dict, List, Literal, Optional, Sequence
from datetime import datetime, timedelta, timezone


def _utc_naive(dt: datetime | None = None) -> datetime:
    """UTC tz-aware datetime을 tz-naive(UTC 기준)로 변환."""
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


from contextlib import asynccontextmanager
import random
import asyncio
from decimal import Decimal
import os
import json
import re
import jwt
from jwt import PyJWTError
import structlog
import time
from urllib.parse import urlparse
from collections import defaultdict

# HMAC 서명 import (패키지/스크립트 실행 모두 대응)
try:
    from utils.sign import sign_click  # type: ignore
except ImportError:  # pragma: no cover
    from services.auction_service.utils.sign import sign_click  # type: ignore

REDIRECT_BASE_URL = os.getenv("REDIRECT_BASE_URL", "http://api-gateway:8000")
PLATFORM_ADVERTISER_ID = int(os.getenv("PLATFORM_ADVERTISER_ID", "1"))

# JWT 설정
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production"
)
ALGORITHM = "HS256"
security = HTTPBearer()

# 구조적 로깅 설정
logger = structlog.get_logger()

# 간단한 레이트리밋 (IP + 쿼리 해시 기준)
_rate_limit_store: Dict[str, List[float]] = defaultdict(list)
_RATE_LIMIT_WINDOW = 10  # 10초
_RATE_LIMIT_MAX_REQUESTS = 3  # 최대 3회


async def check_rate_limit(client_ip: str, query: str) -> bool:
    """레이트리밋 확인 (IP + 쿼리 해시 기준)"""
    import hashlib

    query_hash = hashlib.md5(query.encode()).hexdigest()[:8]
    key = f"{client_ip}:{query_hash}"

    now = time.time()
    # 오래된 요청 제거
    _rate_limit_store[key] = [
        req_time
        for req_time in _rate_limit_store[key]
        if now - req_time < _RATE_LIMIT_WINDOW
    ]

    # 레이트리밋 확인
    if len(_rate_limit_store[key]) >= _RATE_LIMIT_MAX_REQUESTS:
        return False

    # 요청 시간 기록
    _rate_limit_store[key].append(now)
    return True


# 최적화된 매칭 로직 import
# OptimizedAdvertiserMatcher, OptimizedBidGenerator는 main.py에 통합됨

# Database import
try:
    from database import (
        database,
        SearchQuery,
        connect_to_database,
        disconnect_from_database,
    )

    logger.info("database_models_imported_successfully")
except ImportError as e:
    logger.error("database_import_failed", error=str(e))
    # Fallback: 기본 database 연결만 유지
    from databases import Database
    import os

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://admin:your_secure_password_123@postgres:5432/search_exchange_db",
    )
    database = Database(DATABASE_URL)

    async def connect_to_database():
        await database.connect()
        logger.info("database_connected", service="auction-service")

    async def disconnect_from_database():
        await database.disconnect()
        logger.info("database_disconnected", service="auction-service")


# === Tokenization & normalization utilities ===
def _normalize(s: str) -> str:
    """문자열을 소문자로 변환하고 모든 공백을 제거합니다."""
    return "".join(s.lower().split())


# === URL validation ===
def _validate_url(url: str | None) -> str | None:
    """URL 유효성 검증 (HTTPS만 허용)"""
    if not url:
        return None
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ["https"]:
            return None
        if not parsed.netloc:
            return None
        return url
    except Exception:
        return None


# JWT 인증 함수
async def get_user_id_from_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[int]:
    """JWT 토큰에서 사용자 ID 추출 (선택적 - 없으면 None 반환)"""
    if not credentials:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=os.getenv("JWT_AUDIENCE", "digisafe-client") or None,
            issuer=os.getenv("JWT_ISSUER", "digisafe-api") or None,
            options={
                "require_exp": True,
                "verify_aud": bool(os.getenv("JWT_AUDIENCE")),
                "verify_iss": bool(os.getenv("JWT_ISSUER")),
            },
        )
        email = payload.get("sub")
        if not email:
            return None

        # 이메일로 사용자 ID 조회
        user = await database.fetch_one(
            "SELECT id FROM users WHERE email = :email", {"email": email}
        )
        if not user:
            return None
        return user["id"]
    except (PyJWTError, Exception):
        return None


def build_tokens(q: str, *, max_tokens: int = 25) -> list[str]:
    """사용자 검색어로부터 매칭에 사용할 토큰 리스트를 생성합니다."""
    q_norm = _normalize(q)
    tokens = set()
    if q_norm:
        tokens.add(q_norm)  # (1) 정규화된 전체 쿼리
    tokens.update([t for t in q.lower().split() if t])  # (2) 공백 분리 토큰
    if any(ord(c) > 127 for c in q):  # (3) 한글 2-gram 및 3-gram
        for n in (2, 3):
            if len(q_norm) >= n:
                tokens.update([q_norm[i : i + n] for i in range(len(q_norm) - n + 1)])
    return list(tokens)[:max_tokens]


# Lifespan 이벤트 핸들러 정의
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 이벤트
    await connect_to_database()
    yield
    # 종료 이벤트
    await disconnect_from_database()


app = FastAPI(title="Auction Service", version="1.0.0", lifespan=lifespan)


# CORS 설정 (보안 강화)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("ALLOWED_ORIGIN", "https://app.intendex.com"),
        "http://localhost:3000",  # 개발 환경용
        "http://localhost:3001",  # 개발 환경용
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ✅ Pydantic 모델들 (API 응답용)
class BidResponse(BaseModel):
    id: str
    buyerName: str
    price: int
    bonus: str
    timestamp: datetime
    landingUrl: str
    clickUrl: str
    reasons: List[str] = []  # 매칭 근거 (키워드/카테고리 등)
    matchScore: float | None = None  # 매칭 점수(로깅용)
    advertiserId: int | None = (
        None  # 예산/정산을 위한 광고주 식별자 (플랫폼 폴백은 0 또는 None)
    )


class AuctionResponse(BaseModel):
    searchId: str
    query: str
    bids: List[BidResponse]
    status: Literal["active", "completed", "cancelled"]
    createdAt: datetime
    expiresAt: datetime


class StartAuctionRequest(BaseModel):
    query: str
    valueScore: int


class StartAuctionResponse(BaseModel):
    success: bool
    data: AuctionResponse
    message: str


class SelectBidRequest(BaseModel):
    searchId: str
    selectedBidId: str


class SelectBidResponse(BaseModel):
    success: bool
    data: dict
    message: str


class AuctionStatusResponse(BaseModel):
    success: bool
    data: dict
    message: str


# 실제 광고주 매칭 시스템
# 기존 하드코딩된 DATA_BUYERS 제거 - 이제 실제 DB에서 광고주 조회

# --- 1. 광고주 매칭 알고리즘 ---


# === Batched SQL queries for matching (EXACT/PHRASE/BROAD + CATEGORY) ===
EXACT_SQL = """
SELECT advertiser_id, keyword, priority, match_type
FROM advertiser_keywords
WHERE match_type = 'exact'
  AND lower(replace(keyword, ' ', '')) = ANY(:tokens_norm)
"""

# NOTE: PHRASE는 부분 문구 포함을 허용하도록 EXACT와 다르게 보강
PHRASE_SQL = """
SELECT advertiser_id, keyword, priority, match_type
FROM advertiser_keywords
WHERE match_type = 'phrase'
  AND (
        lower(replace(keyword, ' ', '')) = ANY(:tokens_norm)
     OR EXISTS (
          SELECT 1 FROM unnest(:tokens_norm::text[]) t(tok)
          WHERE lower(replace(keyword, ' ', '')) LIKE '%' || tok || '%'
             OR tok LIKE '%' || lower(replace(keyword, ' ', '')) || '%'
     )
  )
"""

BROAD_SQL = """
SELECT advertiser_id, keyword, priority, match_type
FROM advertiser_keywords
WHERE match_type = 'broad'
  AND lower(keyword) LIKE ANY(:tokens_like)
"""

CATEGORY_SQL = """
WITH matched_categories AS (
    SELECT DISTINCT path
    FROM business_categories
    WHERE is_active = true
      AND lower(name) LIKE ANY(:tokens_like)
)
SELECT ac.advertiser_id, ac.category_path, ac.is_primary
FROM advertiser_categories ac
JOIN matched_categories mc ON ac.category_path LIKE mc.path || '%'
"""

SCORES = {"exact": 1.0, "phrase": 0.85, "broad": 0.7}
SCORE_CAP = 3.0  # 최대 점수 상한


def _make_in_clause(
    column_expr: str, values: Sequence[Any], prefix: str
) -> tuple[str, dict]:
    """
    IN (:p0, :p1, ...) 동적 생성
    """
    params: Dict[str, Any] = {}
    parts: list[str] = []
    for i, v in enumerate(values):
        key = f"{prefix}{i}"
        parts.append(f":{key}")
        params[key] = v
    if not parts:
        return "FALSE", {}
    return f"{column_expr} IN (" + ", ".join(parts) + ")", params


def _make_like_clause(
    column_expr: str, tokens_like: list[str], prefix: str
) -> tuple[str, dict]:
    """
    (column LIKE :kw0 OR column LIKE :kw1 ...) 동적 생성
    """
    parts = []
    params = {}
    for i, tok in enumerate(tokens_like):
        key = f"{prefix}{i}"
        parts.append(f"{column_expr} LIKE :{key}")
        params[key] = tok
    if not parts:
        return "FALSE", {}
    return "(" + " OR ".join(parts) + ")", params


def _ensure_aggregator(agg: dict, adv_id: int):
    if adv_id not in agg:
        agg[adv_id] = {"score": 0.0, "reasons": [], "seen_keys": set()}


def _add_keyword_score(
    agg: dict, adv_id: int, match_type: str, priority: int, keyword: str
):
    _ensure_aggregator(agg, adv_id)
    seen_key = f"{match_type}:{keyword}"
    if seen_key in agg[adv_id]["seen_keys"]:
        return
    base_score = SCORES.get(match_type, 0.5)
    priority_weight = 1.0 + (min(max(priority or 1, 1), 5) / 10.0)  # 1.1~1.5
    increment = base_score * priority_weight
    agg[adv_id]["score"] = min(agg[adv_id]["score"] + increment, SCORE_CAP)
    agg[adv_id]["seen_keys"].add(seen_key)
    agg[adv_id]["reasons"].append(f"KW_{match_type.upper()}:{keyword}")


async def find_matching_advertisers(
    search_query: str, quality_score: int
) -> List[Dict[str, Any]]:
    """
    주어진 검색 쿼리에 대한 광고주 매칭(배치 쿼리, N+1 제거)
    """
    raw_tokens = build_tokens(search_query)
    if not raw_tokens:
        return []

    tokens_norm = list(
        set([_normalize(t) for t in raw_tokens] + [_normalize(search_query)])
    )
    tokens_like = list(set([f"%{t}%" for t in raw_tokens if len(t) >= 2]))

    log = logger.bind(service="auction-service")
    log.debug(
        "token_processing",
        raw_tokens=raw_tokens,
        tokens_norm=tokens_norm,
        tokens_like=tokens_like,
    )

    aggregator: Dict[int, Dict[str, Any]] = {}

    # === EXACT (동적 IN) ===
    exact_in, exact_params = _make_in_clause(
        "lower(replace(keyword, ' ', ''))", tokens_norm, "ex"
    )
    exact_sql_dynamic = f"""
        SELECT advertiser_id, keyword, priority, match_type
        FROM advertiser_keywords
        WHERE match_type = 'exact' AND {exact_in}
    """
    exact_rows = await database.fetch_all(exact_sql_dynamic, exact_params)

    # === PHRASE (동적 IN + 동적 LIKE) ===
    phrase_in, phrase_in_params = _make_in_clause(
        "lower(replace(keyword, ' ', ''))", tokens_norm, "ph"
    )
    phrase_like, phrase_like_params = _make_like_clause(
        "lower(replace(keyword, ' ', ''))", tokens_like, "pl"
    )
    # IN 또는 LIKE 중 하나만이라도 있으면 조건 생성
    if phrase_in != "FALSE" and phrase_like != "FALSE":
        phrase_cond = f"({phrase_in} OR {phrase_like})"
        phrase_params = {**phrase_in_params, **phrase_like_params}
    elif phrase_in != "FALSE":
        phrase_cond = phrase_in
        phrase_params = phrase_in_params
    elif phrase_like != "FALSE":
        phrase_cond = phrase_like
        phrase_params = phrase_like_params
    else:
        phrase_cond = "FALSE"
        phrase_params = {}

    phrase_sql_dynamic = f"""
        SELECT advertiser_id, keyword, priority, match_type
        FROM advertiser_keywords
        WHERE match_type = 'phrase' AND {phrase_cond}
    """
    phrase_rows = await database.fetch_all(phrase_sql_dynamic, phrase_params)

    # === BROAD (동적 LIKE) ===
    broad_like, broad_params = _make_like_clause("lower(keyword)", tokens_like, "br")
    broad_sql_dynamic = f"""
        SELECT advertiser_id, keyword, priority, match_type
        FROM advertiser_keywords
        WHERE match_type = 'broad' AND {broad_like}
    """
    broad_rows = (
        await database.fetch_all(broad_sql_dynamic, broad_params) if tokens_like else []
    )

    # 점수 반영
    for rows in (exact_rows, phrase_rows, broad_rows):
        for r in rows:
            _add_keyword_score(
                aggregator,
                r["advertiser_id"],
                r["match_type"],
                r["priority"],
                r["keyword"],
            )

    # === 카테고리 매칭 (동적 LIKE) ===
    if tokens_like:
        cat_like, cat_params = _make_like_clause("lower(name)", tokens_like, "cat")
        category_sql_dynamic = f"""
            WITH matched_categories AS (
                SELECT DISTINCT path
                FROM business_categories
                WHERE is_active = true
                  AND {cat_like}
            )
            SELECT ac.advertiser_id, ac.category_path, ac.is_primary
            FROM advertiser_categories ac
            JOIN matched_categories mc ON ac.category_path LIKE mc.path || '%'
        """
        rows_cat = await database.fetch_all(category_sql_dynamic, cat_params)
        for r in rows_cat:
            adv_id = r["advertiser_id"]
            _ensure_aggregator(aggregator, adv_id)
            cat_score = 0.6 * (1.2 if r["is_primary"] else 1.0)
            seen_key = f"CAT:{r['category_path']}"
            if seen_key not in aggregator[adv_id]["seen_keys"]:
                aggregator[adv_id]["score"] = min(
                    aggregator[adv_id]["score"] + cat_score, SCORE_CAP
                )
                aggregator[adv_id]["seen_keys"].add(seen_key)
                aggregator[adv_id]["reasons"].append(seen_key)

    if not aggregator:
        return []

    # 3) 자동 입찰 설정 일괄 조회
    advertiser_ids = list(aggregator.keys())
    abs_in_clause, abs_params = _make_in_clause("advertiser_id", advertiser_ids, "abs")
    abs_query = f"""
        SELECT advertiser_id, min_quality_score
        FROM auto_bid_settings
        WHERE is_enabled = true AND {abs_in_clause}
    """
    abs_rows = await database.fetch_all(abs_query, abs_params)
    abs_map = {r["advertiser_id"]: r for r in abs_rows}

    # 4) 정책 필터링 및 정렬
    final_advertisers = []
    for adv_id, data in aggregator.items():
        settings = abs_map.get(adv_id)
        if not settings:
            continue
        match_score = data["score"]
        passes = (match_score >= 0.8) or (
            quality_score >= settings["min_quality_score"]
        )
        if passes:
            final_advertisers.append(
                {
                    "advertiser_id": adv_id,
                    "match_score": match_score,
                    "reasons": data["reasons"],
                }
            )

    return sorted(final_advertisers, key=lambda x: x["match_score"], reverse=True)


# --- 2. 자동 입찰가 계산 알고리즘 ---


async def calculate_auto_bid_price(
    match_score: float, settings: Dict[str, Any], review: Dict[str, Any] | None
) -> int:
    """
    매칭 점수와 광고주 설정을 기반으로 최적 입찰가 계산 (DB 조회 없음)
    """
    if not settings:
        return 0
    base_bid = int(settings["max_bid_per_keyword"] * min(match_score, 1.0))
    final_bid = base_bid
    if review:
        final_bid = max(
            review.get("recommended_bid_min", 0),
            min(final_bid, review.get("recommended_bid_max", final_bid)),
        )
    return max(final_bid, 0)


# --- 3. 예산 확인 로직 ---


async def _reserve_budget_tx(advertiser_id: int, bid_amount: int) -> bool:
    """
    예산 예약 (트랜잭션 내부에서만 호출)
    KST 기준 일일 경계 사용: timezone('Asia/Seoul', now())::date
    """
    # KST 기준 오늘 날짜
    current_spend = await database.fetch_one(
        """
        SELECT amount FROM advertiser_daily_spend
        WHERE advertiser_id = :aid 
          AND spend_date = (timezone('Asia/Seoul', now()))::date
        FOR UPDATE
        """,
        {"aid": advertiser_id},
    )

    # 레코드가 없으면 생성
    if not current_spend:
        await database.execute(
            """
            INSERT INTO advertiser_daily_spend(advertiser_id, spend_date, amount)
            VALUES (:aid, (timezone('Asia/Seoul', now()))::date, 0)
            ON CONFLICT (advertiser_id, spend_date) DO NOTHING
            """,
            {"aid": advertiser_id},
        )
        # 다시 조회 (FOR UPDATE)
        current_spend = await database.fetch_one(
            """
            SELECT amount FROM advertiser_daily_spend
            WHERE advertiser_id = :aid 
              AND spend_date = (timezone('Asia/Seoul', now()))::date
            FOR UPDATE
            """,
            {"aid": advertiser_id},
        )
        if not current_spend:
            return False

    # 예산 설정 조회
    budget = await database.fetch_one(
        """
        SELECT daily_budget FROM auto_bid_settings 
        WHERE advertiser_id = :aid
        """,
        {"aid": advertiser_id},
    )
    if not budget:
        return False

    current_amount = int(current_spend["amount"] or 0)
    budget_limit = int(budget["daily_budget"] or 0)

    # 예산 초과 확인
    if (current_amount + bid_amount) > budget_limit:
        return False

    # 예산 업데이트
    await database.execute(
        """
        UPDATE advertiser_daily_spend
        SET amount = amount + :amt
        WHERE advertiser_id = :aid 
          AND spend_date = (timezone('Asia/Seoul', now()))::date
        """,
        {"aid": advertiser_id, "amt": bid_amount},
    )
    return True


async def reserve_and_insert_bid(
    auction_id: int, user_id: int, bid: BidResponse
) -> bool:
    """
    예산 예약과 bid 저장을 하나의 트랜잭션으로 처리
    """
    async with database.transaction():
        # 1) 예산 예약 (ADVERTISER만)
        if (
            not bid.id.startswith("platform_bid_")
            and bid.advertiserId
            and bid.advertiserId != PLATFORM_ADVERTISER_ID
        ):
            ok = await _reserve_budget_tx(bid.advertiserId, bid.price)
            if not ok:
                logger.warning(
                    "budget_insufficient",
                    advertiser_id=bid.advertiserId,
                    bid_price=bid.price,
                )
                return False

        # 2) bid 저장
        bid_type = "PLATFORM" if bid.id.startswith("platform_bid_") else "ADVERTISER"
        await database.execute(
            """
            INSERT INTO bids (
                id, auction_id, buyer_name, price, bonus_description, 
                landing_url, type, user_id, dest_url, advertiser_id, created_at
            )
            VALUES (
                :id, :auction_id, :buyer_name, :price, :bonus_description,
                :landing_url, :type, :user_id, :dest_url, :advertiser_id, NOW()
            )
            """,
            {
                "id": bid.id,
                "auction_id": auction_id,
                "buyer_name": bid.buyerName,
                "price": bid.price,
                "bonus_description": bid.bonus,
                "landing_url": bid.landingUrl,
                "type": bid_type,
                "user_id": user_id,
                "dest_url": bid.landingUrl,
                "advertiser_id": bid.advertiserId,
            },
        )
        return True


# --- 4. 실제 광고주 자동 입찰 생성 ---


async def generate_real_advertiser_bids(
    search_query: str, quality_score: int
) -> List[BidResponse]:
    """
    실제 광고주 자동 입찰 생성 (N+1 제거, 점수/사유 전달)
    """
    log = logger.bind(service="auction-service")
    log.info(
        "auction_matching_start",
        query=search_query,
        quality_score=quality_score,
    )

    matching_advertisers = await find_matching_advertisers(search_query, quality_score)
    if not matching_advertisers:
        log.warning("no_matching_advertisers", query=search_query)
        return generate_platform_fallback_bids(search_query, quality_score)

    advertiser_ids = [m["advertiser_id"] for m in matching_advertisers]
    details_in_clause, details_params = _make_in_clause("a.id", advertiser_ids, "adv")
    details_query = f"""
        SELECT 
            a.id as advertiser_id, a.company_name, a.website_url,
            abs.daily_budget, abs.max_bid_per_keyword,
            ar.recommended_bid_min, ar.recommended_bid_max
        FROM advertisers a
        LEFT JOIN auto_bid_settings abs ON a.id = abs.advertiser_id
        LEFT JOIN advertiser_reviews ar ON a.id = ar.advertiser_id AND ar.review_status = 'approved'
        WHERE abs.is_enabled = true AND {details_in_clause}
    """
    rows = await database.fetch_all(details_query, details_params)
    info_map = {r["advertiser_id"]: dict(r) for r in rows}

    real_bids: List[BidResponse] = []
    for m in matching_advertisers:
        adv_id = m["advertiser_id"]
        match_score = m["match_score"]
        reasons = m["reasons"]
        info = info_map.get(adv_id)
        if not info:
            continue

        settings = {
            "max_bid_per_keyword": info["max_bid_per_keyword"],
            "daily_budget": info["daily_budget"],
        }
        review = (
            {
                "recommended_bid_min": info.get("recommended_bid_min"),
                "recommended_bid_max": info.get("recommended_bid_max"),
            }
            if (
                info.get("recommended_bid_min") is not None
                or info.get("recommended_bid_max") is not None
            )
            else None
        )

        bid_price = await calculate_auto_bid_price(match_score, settings, review)
        if bid_price <= 0:
            continue

        # 예산 확인은 나중에 reserve_and_insert_bid에서 트랜잭션으로 처리
        # 여기서는 BidResponse만 생성

        import uuid

        bid_id = f"bid_real_{adv_id}_{int(datetime.now(timezone.utc).timestamp())}_{uuid.uuid4().hex[:8]}"
        sig = sign_click(bid_id, bid_price, "ADVERTISER")
        click_url = f"{REDIRECT_BASE_URL}/api/redirect/{bid_id}?sig={sig}"

        real_bids.append(
            BidResponse(
                id=bid_id,
                buyerName=info["company_name"],
                price=bid_price,
                bonus=generate_bonus_conditions_for_advertiser(
                    info, match_score, quality_score
                ),
                timestamp=datetime.now(timezone.utc),
                landingUrl=_validate_url(info.get("website_url"))
                or f"https://www.google.com/search?q={search_query}",
                clickUrl=click_url,
                reasons=reasons,
                matchScore=match_score,
                advertiserId=adv_id,
            )
        )
        log.debug(
            "advertiser_bid_created",
            advertiser_id=adv_id,
            company_name=info["company_name"],
            bid_price=bid_price,
            match_score=match_score,
        )

    if not real_bids:
        log.warning("no_valid_bids", query=search_query)
        return generate_platform_fallback_bids(search_query, quality_score)

    return sorted(real_bids, key=lambda x: x.price, reverse=True)


def generate_bonus_conditions_for_advertiser(
    advertiser_info: Dict[str, Any], match_score: float, quality_score: int
) -> str:
    """실제 광고주를 위한 보너스 조건 생성"""
    conditions = []

    if match_score >= 0.95:
        conditions.append("프리미엄 매칭 우선 제공")
    elif match_score >= 0.80:
        conditions.append("고품질 매칭 제공")

    if quality_score >= 80:
        conditions.append("프리미엄 데이터 우선 제공")
    elif quality_score >= 60:
        conditions.append("추가 분석 리포트 제공")

    if quality_score >= 70:
        conditions.append("전용 대시보드 제공")

    # 광고주별 맞춤 조건
    company_name = advertiser_info.get("company_name", "").lower()
    if any(keyword in company_name for keyword in ["마케팅", "광고"]):
        conditions.append("광고 효과 분석 포함")
    elif any(keyword in company_name for keyword in ["데이터", "분석"]):
        conditions.append("상세 통계 분석 포함")
    elif any(keyword in company_name for keyword in ["쇼핑", "커머스"]):
        conditions.append("구매 전환 분석 포함")

    return ", ".join(conditions) if conditions else "기본 서비스"


def generate_platform_fallback_bids(
    search_query: str, quality_score: int
) -> List[BidResponse]:
    """
    광고주 매칭이 실패했을 때 플랫폼 사업자들이 제공하는 고정 200원 적립 입찰을 생성합니다.
    """
    log = logger.bind(service="auction-service")
    log.info("platform_fallback_bids_creating")

    platform_buyers = [
        {
            "name": "쿠팡",
            "name_en": "coupang",
            "url": f"https://www.coupang.com/np/search?q={search_query}",
            "bonus": "로켓배송으로 바로 받기",
        },
        {
            "name": "네이버",
            "name_en": "naver",
            "url": f"https://search.naver.com/search.naver?where=web&query={search_query}",
            "bonus": "네이버쇼핑 최저가 비교",
        },
        {
            "name": "구글",
            "name_en": "google",
            "url": f"https://www.google.com/search?q={search_query}",
            "bonus": "가장 빠른 최신 정보",
        },
    ]

    fallback_bids = []
    now = datetime.now(timezone.utc)

    for i, buyer in enumerate(platform_buyers):
        import uuid

        bid_id = f"platform_bid_{buyer['name_en']}_{int(now.timestamp())}_{i}"

        # clickUrl 생성 (HMAC 서명 포함)
        bid_type = "PLATFORM"
        sig = sign_click(bid_id, 200, bid_type)
        click_url = f"{REDIRECT_BASE_URL}/api/redirect/{bid_id}?sig={sig}"

        fallback_bids.append(
            BidResponse(
                id=bid_id,
                buyerName="Intendex",
                price=200,  # 고정 200원 적립
                bonus=buyer["bonus"],
                timestamp=now,
                landingUrl=buyer["url"],
                clickUrl=click_url,
                advertiserId=PLATFORM_ADVERTISER_ID,
                matchScore=1.0,
                reasons=[f"PLATFORM:{buyer['name_en']}"],
            )
        )

    log.info("platform_fallback_bids_created", count=len(fallback_bids))
    return fallback_bids


def generate_bonus_conditions(buyer: dict, value_score: int) -> str:
    """기존 시뮬레이션용 보너스 조건 생성 (하위 호환성 유지)"""
    conditions = []

    if value_score >= 80:
        conditions.append("프리미엄 데이터 우선 제공")

    if value_score >= 60:
        conditions.append("추가 분석 리포트 제공")

    industry = buyer.get("industry", "")
    if industry == "광고/마케팅":
        conditions.append("광고 효과 분석 포함")
    elif industry == "디지털마케팅":
        conditions.append("소셜미디어 인사이트 제공")
    elif industry == "데이터분석":
        conditions.append("상세 통계 분석 포함")

    if value_score >= 70:
        conditions.append("전용 대시보드 제공")

    return ", ".join(conditions) if conditions else "기본 서비스"


async def start_reverse_auction(query: str, value_score: int) -> List[BidResponse]:
    """
    역경매를 시작합니다. (수정된 버전)
    """
    log = logger.bind(service="auction-service")
    log.info("reverse_auction_start", query=query, quality_score=value_score)

    # 실제 광고주 매칭 시도
    bids = await generate_real_advertiser_bids(query, value_score)

    # 혹시 모를 상황에 대비한 안전장치
    if not bids:
        log.error("no_bids_generated", query=query)
        bids = generate_platform_fallback_bids(query, value_score)

    # 자동 입찰 결과 DB에 기록
    await log_auto_bids(bids, query, value_score)

    log.info("reverse_auction_complete", bid_count=len(bids))
    for i, bid in enumerate(bids):
        log.debug("bid_detail", index=i + 1, buyer=bid.buyerName, price=bid.price)

    return bids


async def generate_simulation_bids(
    query: str, value_score: int, count: int
) -> List[BidResponse]:
    """시뮬레이션 입찰 생성 (실제 광고주 부족 시 보완용)"""
    now = datetime.now(timezone.utc)
    bids = []

    # 플랫폼별 검색 URL 생성
    search_urls = {
        "google": f"https://www.google.com/search?q={query}",
        "naver": f"https://search.naver.com/search.naver?where=web&query={query}",
        "coupang": f"https://www.coupang.com/np/search?q={query}",
        "amazon": f"https://www.amazon.com/s?k={query}",
        "gmarket": f"https://browse.gmarket.co.kr/search?keyword={query}",
        "elevenst": f"https://www.11st.co.kr/search?keyword={query}",
    }

    # 플랫폼별 입찰자 생성
    platform_buyers = [
        {
            "name": "Google",
            "url": search_urls["google"],
            "bonus": "가장 빠른 최신 정보",
        },
        {
            "name": "네이버",
            "url": search_urls["naver"],
            "bonus": "네이버쇼핑 최저가 비교",
        },
        {
            "name": "쿠팡",
            "url": search_urls["coupang"],
            "bonus": "로켓배송으로 바로 받기",
        },
        {
            "name": "Amazon",
            "url": search_urls["amazon"],
            "bonus": "해외 직구 & 빠른 배송",
        },
        {"name": "G마켓", "url": search_urls["gmarket"], "bonus": "G마켓 특가 상품"},
        {"name": "11번가", "url": search_urls["elevenst"], "bonus": "11번가 할인 혜택"},
    ]

    for i in range(count):
        price = random.randint(100, 1000)
        platform_buyer = platform_buyers[i % len(platform_buyers)]

        import uuid

        bid_id = f"bid_sim_{int(now.timestamp())}_{i}_{uuid.uuid4().hex[:8]}"

        # clickUrl 생성 (HMAC 서명 포함)
        bid_type = "ADVERTISER"
        sig = sign_click(bid_id, price, bid_type)
        click_url = f"{REDIRECT_BASE_URL}/api/redirect/{bid_id}?sig={sig}"

        bids.append(
            BidResponse(
                id=bid_id,
                buyerName=platform_buyer["name"],
                price=price,
                bonus=platform_buyer["bonus"],
                timestamp=now,
                landingUrl=platform_buyer["url"],
                clickUrl=click_url,
            )
        )

    return bids


# 쿼리 내 바인더(:name) 추출을 위한 정규식
_BIND_RE = re.compile(r":([a-zA-Z_][a-zA-Z0-9_]*)")


def _filter_params_for_query(sql: str, params: dict) -> dict:
    """SQL 쿼리에 실제로 존재하는 바인더만 파라미터 딕셔너리에서 필터링"""
    names = set(_BIND_RE.findall(sql))
    return {k: v for k, v in params.items() if k in names}


async def log_auto_bids(bids: List[BidResponse], query: str, value_score: int):
    """자동 입찰 결과를 로그 테이블에 기록 (reasons JSONB / matchScore 반영)"""
    log = logger.bind(service="auction-service")
    try:
        # 1차: reasons 포함 쿼리 (정상 케이스)
        sql_with_reasons = """
            INSERT INTO auto_bid_logs (
                advertiser_id, search_query, match_type, match_score,
                bid_amount, bid_result, quality_score, competitor_count,
                created_at, reasons
            ) VALUES (
                :advertiser_id, :search_query, :match_type, :match_score,
                :bid_amount, :bid_result, :quality_score, :competitor_count,
                :created_at, CAST(:reasons AS jsonb)
            )
        """

        # 2차 폴백: reasons 없이 (구버전 테이블 호환)
        sql_without_reasons = """
            INSERT INTO auto_bid_logs (
                advertiser_id, search_query, match_type, match_score,
                bid_amount, bid_result, quality_score, competitor_count,
                created_at
            ) VALUES (
                :advertiser_id, :search_query, :match_type, :match_score,
                :bid_amount, :bid_result, :quality_score, :competitor_count,
                :created_at
            )
        """

        for bid in bids:
            # BidResponse에 advertiserId가 지정되지 않았다면 NULL 로깅
            advertiser_id = bid.advertiserId if bid.advertiserId else None
            match_score = float(bid.matchScore or 0.0)
            reasons_value = bid.reasons or []

            # created_at은 tz-naive UTC로
            created_at = _utc_naive(bid.timestamp)

            # 기본 파라미터 준비 (reasons는 JSON 문자열로 직렬화)
            base_params = {
                "advertiser_id": advertiser_id,
                "search_query": query,
                "match_type": "complex",
                "match_score": match_score,
                "bid_amount": bid.price,
                "bid_result": ("won" if bid.price > 500 else "lost"),
                "quality_score": value_score,
                "competitor_count": len(bids),
                "created_at": created_at,
                "reasons": json.dumps(reasons_value),
            }

            try:
                # 1차 시도: reasons 포함
                params = _filter_params_for_query(sql_with_reasons, base_params)
                await database.execute(sql_with_reasons, params)
            except Exception as e1:
                log.warning("reasons_column_not_found_fallback", error=str(e1))
                # 2차 시도: reasons 제거 쿼리 (파라미터도 필터링하여 reasons 키 제거)
                params_fb = _filter_params_for_query(sql_without_reasons, base_params)
                await database.execute(sql_without_reasons, params_fb)

        log.info("auto_bid_logs_recorded", bid_count=len(bids))
    except Exception as e:
        log.error("auto_bid_logging_error", error=str(e), exc_info=True)


async def generate_fallback_bids(query: str, value_score: int) -> List[BidResponse]:
    """최소 보장용 폴백 입찰 생성"""
    now = datetime.now(timezone.utc)

    import uuid

    bid_id = f"bid_fallback_{int(now.timestamp())}_{uuid.uuid4().hex[:8]}"

    # clickUrl 생성 (HMAC 서명 포함)
    bid_type = "ADVERTISER"
    price = random.randint(100, 500)
    sig = sign_click(bid_id, price, bid_type)
    click_url = f"{REDIRECT_BASE_URL}/api/redirect/{bid_id}?sig={sig}"

    return [
        BidResponse(
            id=bid_id,
            buyerName="Google",
            price=price,
            bonus="기본 검색 결과",
            timestamp=now,
            landingUrl=f"https://www.google.com/search?q={query}",
            clickUrl=click_url,
        )
    ]


async def simulate_real_time_delay():
    """랜덤 지연 시간 시뮬레이션 (실시간 경매 효과)"""
    delay = random.uniform(0.5, 2.5)
    await asyncio.sleep(delay)


async def simulate_auction_update(auction_id: str) -> dict:
    """경매 상태 업데이트 시뮬레이션"""
    await asyncio.sleep(random.uniform(0.5, 1.5))
    return {"status": "active", "participants": random.randint(1, 10)}


@app.post("/start", response_model=StartAuctionResponse)
async def start_auction(
    request: StartAuctionRequest,
    http_request: Request,
    user_id: Optional[int] = Depends(get_user_id_from_token),
):
    """역경매를 시작합니다."""
    try:
        log = logger.bind(service="auction-service")

        # 레이트리밋 확인
        client_ip = http_request.client.host if http_request.client else "unknown"
        if not await check_rate_limit(client_ip, request.query):
            log.warning("rate_limit_exceeded", ip=client_ip, query=request.query)
            raise HTTPException(
                status_code=429,
                detail="너무 많은 요청입니다. 잠시 후 다시 시도해주세요.",
            )

        log.info(
            "auction_start",
            query=request.query,
            query_length=len(request.query),
            value_score=request.valueScore,
            user_id=user_id,
        )

        # 역경매 시작 (실제 광고주 매칭 시스템 사용)
        bids = await start_reverse_auction(request.query, request.valueScore)

        # 경매 정보 생성
        search_id = f"search_{int(datetime.now(timezone.utc).timestamp())}_{random.randint(1000, 9999)}"
        now = _utc_naive()
        expires_at = now + timedelta(minutes=30)  # 30분 후 만료

        # 경매 정보를 DB에 저장
        auction_query = """
            INSERT INTO auctions (search_id, query_text, user_id, status, expires_at, created_at)
            VALUES (:search_id, :query_text, :user_id, :status, :expires_at, :created_at)
            RETURNING id
        """

        try:
            auction_result = await database.fetch_one(
                auction_query,
                {
                    "search_id": search_id,
                    "query_text": request.query.strip(),
                    "user_id": (
                        user_id if user_id else 1
                    ),  # JWT에서 추출하거나 기본값 사용
                    "status": "active",
                    "expires_at": expires_at,
                    "created_at": now,
                },
            )
        except Exception as db_error:
            log.error(
                "auction_creation_error",
                error=str(db_error),
                exc_info=True,
            )
            raise HTTPException(
                status_code=500, detail=f"데이터베이스 오류: {str(db_error)}"
            )

        if not auction_result:
            raise HTTPException(status_code=500, detail="경매 생성에 실패했습니다.")

        auction_id = auction_result["id"]

        # 입찰 정보를 DB에 저장 (예산 예약과 함께 하나의 트랜잭션으로 처리)
        successful_bids = []
        for bid in bids:
            # 광고주 ID가 BidResponse에 없으면 bid_id에서 추출 시도
            if not bid.advertiserId and bid.id.startswith("bid_real_"):
                try:
                    parts = bid.id.split("_")
                    if len(parts) >= 3:
                        bid.advertiserId = int(parts[2])
                except (ValueError, IndexError):
                    pass

            # 예산 예약 + bid 저장 (트랜잭션으로 원자적 처리)
            success = await reserve_and_insert_bid(
                auction_id, user_id if user_id else 1, bid
            )
            if success:
                successful_bids.append(bid)
            else:
                logger.warning(
                    "bid_insert_failed",
                    bid_id=bid.id,
                    advertiser_id=bid.advertiserId,
                    reason="budget_insufficient_or_db_error",
                )

        # 최소한 하나의 bid라도 저장되어야 함 (없으면 플랫폼 폴백 처리)
        if not successful_bids:
            logger.error("no_bids_stored", auction_id=auction_id)
            # 모든 입찰이 실패했을 경우 빈 리스트 반환 또는 플랫폼 폴백 재생성
            bids = generate_platform_fallback_bids(request.query, request.valueScore)
            for bid in bids:
                await reserve_and_insert_bid(auction_id, user_id if user_id else 1, bid)

        # 성공적으로 저장된 bids만 반환 (또는 원본 bids - 클라이언트에는 모두 보여줌)
        auction = AuctionResponse(
            searchId=search_id,
            query=request.query.strip(),
            bids=bids,  # 원본 bids 반환 (클라이언트 표시용)
            status="active",
            createdAt=now,
            expiresAt=expires_at,
        )

        return StartAuctionResponse(
            success=True, data=auction, message="역경매가 성공적으로 시작되었습니다."
        )

    except Exception as e:
        logger.error("auction_service_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@app.post("/select", response_model=SelectBidResponse)
async def select_bid(request: SelectBidRequest):
    """사용자의 입찰 선택을 처리합니다."""
    try:
        # 입력값 유효성 검사
        if not request.searchId or not request.selectedBidId:
            raise HTTPException(status_code=400, detail="유효하지 않은 요청입니다.")

        # 경매 존재 확인 (DB에서 조회)
        auction_query = "SELECT * FROM auctions WHERE search_id = :search_id"
        auction = await database.fetch_one(
            auction_query, {"search_id": request.searchId}
        )

        if not auction:
            raise HTTPException(status_code=404, detail="경매를 찾을 수 없습니다.")

        # 선택된 입찰 정보 업데이트
        update_query = """
            UPDATE auctions 
            SET selected_bid_id = :selected_bid_id, status = 'completed'
            WHERE search_id = :search_id
        """
        await database.execute(
            update_query,
            {
                "selected_bid_id": request.selectedBidId,
                "search_id": request.searchId,
            },
        )

        # (시뮬레이션) 처리 지연
        await simulate_real_time_delay()

        # (시뮬레이션) 1차 보상 지급 성공
        reward_amount = random.randint(1000, 6000)

        return SelectBidResponse(
            success=True,
            data={
                "rewardAmount": reward_amount,
                "searchId": request.searchId,
                "selectedBidId": request.selectedBidId,
            },
            message="1차 보상이 지급되었습니다.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@app.get("/status/{search_id}", response_model=AuctionStatusResponse)
async def get_auction_status(search_id: str):
    """경매 상태를 조회합니다."""
    try:
        # DB에서 경매 정보 조회
        auction_query = "SELECT * FROM auctions WHERE search_id = :search_id"
        auction = await database.fetch_one(auction_query, {"search_id": search_id})

        if not auction:
            raise HTTPException(status_code=404, detail="경매를 찾을 수 없습니다.")

        # 입찰 정보 조회
        bids_query = "SELECT * FROM bids WHERE auction_id = :auction_id"
        bids = await database.fetch_all(bids_query, {"auction_id": auction["id"]})

        status_update = await simulate_auction_update(search_id)

        return AuctionStatusResponse(
            success=True,
            data={"auction": auction, "bids": bids, "status": status_update},
            message="경매 상태 조회가 완료되었습니다.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@app.get("/bid/{bid_id}")
async def get_bid_info(bid_id: str):
    """특정 입찰 정보를 조회합니다."""
    try:
        # DB에서 입찰 정보 조회
        bid_query = "SELECT * FROM bids WHERE id = :bid_id"
        bid = await database.fetch_one(bid_query, {"bid_id": bid_id})

        if not bid:
            raise HTTPException(status_code=404, detail="입찰 정보를 찾을 수 없습니다.")

        row = dict(bid)
        return {
            "id": row.get("id"),
            "auction_id": row.get("auction_id"),
            "buyer_name": row.get("buyer_name"),
            "price": row.get("price"),
            "bonus_description": row.get("bonus_description"),
            "landing_url": row.get("landing_url"),
            "advertiser_id": row.get("advertiser_id"),
            "type": row.get("type"),
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@app.get("/bids")
async def get_recent_bids():
    """최근 입찰 내역을 반환합니다."""
    try:
        # 시뮬레이션 데이터 반환
        recent_bids = []
        for i in range(5):
            recent_bids.append(
                {
                    "id": f"bid_{random.randint(1000, 9999)}",
                    "auctionId": f"auction_{random.randint(100, 999)}",
                    "amount": random.randint(1000, 5000),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": random.choice(["active", "won", "lost", "pending"]),
                    "highestBid": random.randint(1000, 5000),
                    "myBid": random.randint(1000, 5000),
                }
            )

        return {"success": True, "bids": recent_bids}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "auction-service", "database": "connected"}


@app.get("/system-status")
async def get_system_status():
    """실제 광고주 매칭 시스템 상태 확인 (성능 모니터링 포함)"""
    start_time = time.time()
    try:
        # DB 응답 시간 측정 (p95/p99 계산을 위한 샘플)
        db_start = time.time()
        advertiser_count_query = """
            SELECT COUNT(*) as count
            FROM advertisers a
            JOIN auto_bid_settings abs ON a.id = abs.advertiser_id
            WHERE abs.is_enabled = true
        """
        advertiser_count = await database.fetch_one(advertiser_count_query)
        db_response_time = (time.time() - db_start) * 1000  # ms

        approved_count_query = """
            SELECT COUNT(*) as count
            FROM advertisers a
            JOIN advertiser_reviews ar ON a.id = ar.advertiser_id
            JOIN auto_bid_settings abs ON a.id = abs.advertiser_id
            WHERE ar.review_status = 'approved' AND abs.is_enabled = true
        """
        approved_count = await database.fetch_one(approved_count_query)

        keyword_count_query = "SELECT COUNT(*) as count FROM advertiser_keywords"
        keyword_count = await database.fetch_one(keyword_count_query)

        category_count_query = "SELECT COUNT(*) as count FROM advertiser_categories"
        category_count = await database.fetch_one(category_count_query)

        # 최근 1시간 입찰 통계
        recent_bids_query = """
            SELECT 
                COUNT(*) as total_bids,
                AVG(price) as avg_bid_price,
                SUM(CASE WHEN type = 'ADVERTISER' THEN 1 ELSE 0 END) as advertiser_bids,
                SUM(CASE WHEN type = 'PLATFORM' THEN 1 ELSE 0 END) as platform_bids
            FROM bids
            WHERE created_at >= NOW() - INTERVAL '1 hour'
        """
        recent_bids_stats = await database.fetch_one(recent_bids_query)

        # 실제 광고주 매칭 성능 (최근 평균)
        matching_perf_query = """
            SELECT AVG(match_score) as avg_match_score
            FROM auto_bid_logs
            WHERE created_at >= NOW() - INTERVAL '1 hour'
              AND advertiser_id IS NOT NULL
        """
        matching_perf = await database.fetch_one(matching_perf_query)

        total_time = (time.time() - start_time) * 1000  # ms

        return {
            "status": "operational",
            "service": "auction-service",
            "real_advertiser_matching": "enabled",
            "statistics": {
                "total_advertisers": (
                    advertiser_count["count"] if advertiser_count else 0
                ),
                "approved_advertisers": (
                    approved_count["count"] if approved_count else 0
                ),
                "registered_keywords": keyword_count["count"] if keyword_count else 0,
                "registered_categories": (
                    category_count["count"] if category_count else 0
                ),
            },
            "performance": {
                "db_response_time_ms": round(db_response_time, 2),
                "api_response_time_ms": round(total_time, 2),
                "recent_bids_last_hour": {
                    "total": (
                        recent_bids_stats["total_bids"] if recent_bids_stats else 0
                    ),
                    "avg_price": (
                        round(float(recent_bids_stats["avg_bid_price"] or 0), 2)
                        if recent_bids_stats
                        else 0
                    ),
                    "advertiser_bids": (
                        recent_bids_stats["advertiser_bids"] if recent_bids_stats else 0
                    ),
                    "platform_bids": (
                        recent_bids_stats["platform_bids"] if recent_bids_stats else 0
                    ),
                },
                "matching_performance": {
                    "avg_match_score": (
                        round(float(matching_perf["avg_match_score"] or 0), 3)
                        if matching_perf
                        else 0
                    ),
                },
            },
            "features": {
                "real_advertiser_matching": True,
                "auto_bid_calculation": True,
                "budget_management": True,
                "category_matching": True,
                "simulation_fallback": True,
                "transactional_budget": True,
                "performance_monitoring": True,
            },
        }
    except Exception as e:
        logger.error("system_status_error", error=str(e), exc_info=True)
        return {
            "status": "error",
            "service": "auction-service",
            "error": str(e),
            "real_advertiser_matching": "disabled",
        }


@app.get("/search/{search_id}")
async def get_search_query(search_id: str):
    """searchId로 검색어를 조회합니다."""
    try:
        query = """
            SELECT query_text FROM auctions WHERE search_id = :search_id
        """
        result = await database.fetch_one(query, {"search_id": search_id})

        if result:
            return {"success": True, "query": result["query_text"]}
        else:
            raise HTTPException(status_code=404, detail="Search ID not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
