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


# === Gemini SDK for Semantic Matching ===

try:

    from google import generativeai as genai  # type: ignore

except ImportError:

    genai = None  # type: ignore[assignment]


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""

SEMANTIC_ENABLED = bool(GEMINI_API_KEY and genai)


if SEMANTIC_ENABLED:

    try:

        genai.configure(api_key=GEMINI_API_KEY)  # type: ignore[union-attr]

        structlog.get_logger().info(
            "gemini_semantic_enabled", model="text-embedding-004"
        )

    except Exception as e:

        structlog.get_logger().error("gemini_config_error", error=str(e))

        SEMANTIC_ENABLED = False


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


def build_tokens(q: str, *, max_tokens: int = 30) -> list[str]:
    """

    사용자 검색어로부터 매칭에 사용할 토큰 리스트를 생성합니다.



    개선사항:

    - 공백 유지 토큰 추가 (구문 매칭용)

    - 연속 단어 조합 추가 (2어절, 3어절)

    - 영어/한글 혼용 지원

    """

    tokens = set()

    q_lower = q.lower().strip()

    q_norm = _normalize(q)  # 공백 제거 버전

    # (1) 정규화된 전체 쿼리 (공백 제거)

    if q_norm:

        tokens.add(q_norm)

    # (2) 공백 분리 개별 토큰

    words = [w for w in q_lower.split() if w]

    tokens.update(words)

    # (3) 연속 단어 조합 (2어절, 3어절) - 공백 유지 및 제거 버전 모두 추가

    for n in range(2, min(4, len(words) + 1)):

        for i in range(len(words) - n + 1):

            phrase = " ".join(words[i : i + n])

            tokens.add(phrase)  # 공백 유지 버전

            tokens.add(_normalize(phrase))  # 공백 제거 버전

    # (4) 한글 n-gram (공백 제거된 버전에서)

    if any(ord(c) > 127 for c in q):

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

  AND (

    lower(replace(keyword, ' ', '')) % :query_norm

    OR similarity(lower(replace(keyword, ' ', '')), :query_norm) > 0.3

    OR :query_norm % lower(replace(keyword, ' ', ''))

  )

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


SCORES = {"exact": 1.0, "phrase": 0.85, "broad": 0.7, "semantic": 1.0}

SCORE_CAP = 4.0  # 최대 점수 상한 (기존 3.0 → 4.0으로 확장)


# 매칭 임계값 (환경변수로 관리)

MATCH_THRESHOLD_HIGH = float(os.getenv("MATCH_THRESHOLD_HIGH", "1.8"))

MATCH_THRESHOLD_LOW = float(os.getenv("MATCH_THRESHOLD_LOW", "0.9"))

# 시멘틱-only 허용 최소 점수 (기본 2.2로 상향 조정, 과도하게 관대한 매칭 방지)

SEMANTIC_ONLY_THRESHOLD = float(os.getenv("SEMANTIC_ONLY_THRESHOLD", "2.2"))


# 🔹 품질이 낮은 Exact 매칭에 대해 "위험 할인"을 적용할 기준점 (기본 40점 이하를 저품질로 간주)

LOW_QUALITY_RISK_THRESHOLD = int(os.getenv("LOW_QUALITY_RISK_THRESHOLD", "40"))


# 🔹 리스크 할인율 (기본 0.7 = 70% 가격 적용)

RISK_DISCOUNT_FACTOR = float(os.getenv("RISK_DISCOUNT_FACTOR", "0.7"))


# === Hard Negative Rules (명백히 잘못된 조합 차단용) ===

# 검색어에 "positive" 단어가 포함되고, 광고 키워드에 "negative" 단어가 포함되면

# 시맨틱 매칭을 차단합니다.

HARD_NEGATIVE_RULES: dict[str, list[str]] = {
    # "명품 가방 구매" vs "짝퉁/가품/중고/렌탈"
    "명품": ["짝퉁", "가품", "위조", "복제", "모조", "중고", "렌탈", "대여"],
    # "케이스 구매" vs "수리/AS/매입"
    "케이스": ["수리", "as", "a/s", "수리센터", "매입", "매매"],
    # "아이폰 수리" vs "케이스/액세서리" (반대 방향도 존재하지만, 여기서는 보수적으로 사용)
    "수리": ["케이스", "액정필름", "필름", "악세서리", "케이스세트"],
    # "새 제품 구매" vs "중고/매입"
    "구매": ["중고", "매입", "매입전문", "헌제품"],
    # "여행 상품" vs "이민/비자/유학" 등 서로 다른 의도
    "여행": ["이민", "비자", "유학", "워킹홀리데이", "취업비자"],
    # "자동차 구매" vs "렌트/카쉐어링"
    "자동차": ["렌트", "렌터카", "카쉐어링", "장기렌트"],
}


def has_hard_negative(query: str, keyword: str) -> bool:
    """

    Hard Negative 룰을 사용하여, 명백히 잘못된 광고 매칭을 차단합니다.



    - query: 사용자 원본 검색어

    - keyword: 광고주가 등록한 키워드 (또는 시맨틱 매칭된 키워드)



    반환:

        True  -> 이 조합은 차단해야 함

        False -> 통과 가능

    """

    if not query or not keyword:

        return False

    q_norm = _normalize(query)

    k_norm = _normalize(keyword)

    for positive, negatives in HARD_NEGATIVE_RULES.items():

        if positive in q_norm:

            for neg in negatives:

                if neg and neg in k_norm:

                    logger.info(
                        "hard_negative_block",
                        query=query,
                        keyword=keyword,
                        positive=positive,
                        negative=neg,
                    )

                    return True

    return False


# === 시맨틱 매칭 설정 (pgvector + Gemini Embedding) ===

# - LIMIT: 후보군을 충분히 확보하기 위해 50으로 설정

# - SIM_THRESHOLD: 0.72로 상향 조정 (과도하게 관대한 매칭 방지)

# - WEIGHT: 3.0으로 하향 조정 (과도한 가중치 방지)

SEMANTIC_MATCH_LIMIT = int(os.getenv("SEMANTIC_MATCH_LIMIT", "50"))


_semantic_sim_raw = float(os.getenv("SEMANTIC_SIM_THRESHOLD", "0.72"))

# 0.4(너무 광범위) ~ 0.9(동작 안 함) 사이로 안전하게 제한

SEMANTIC_SIM_THRESHOLD = max(min(_semantic_sim_raw, 0.9), 0.4)


# 시맨틱 점수 가중치 (기본 3.0으로 하향 조정)

SEMANTIC_WEIGHT = float(os.getenv("SEMANTIC_WEIGHT", "3.0"))


# 시맨틱 Super Pass 설정: 유사도가 매우 높으면 텍스트 점수 없이도 고득점 보장

SEMANTIC_SUPER_PASS_SIM = float(os.getenv("SEMANTIC_SUPER_PASS_SIM", "0.75"))

SEMANTIC_SUPER_PASS_SCORE = float(os.getenv("SEMANTIC_SUPER_PASS_SCORE", "3.5"))


# 표준 비즈니스 카테고리 (광고주/웹사이트/경매 공통)

STANDARD_CATEGORIES: List[str] = [
    "전자제품",
    "패션/뷰티",
    "생활/건강",
    "식품/음료",
    "스포츠/레저/자동차",
    "유아/아동",
    "여행/문화",
    "반려동물",
    "디지털 콘텐츠",
    "부동산/인테리어",
    "의료/건강",
    "서비스",
    "교육/도서",
    "비영리/공공",
]


# 카테고리 Alias (Gemini 응답 정규화용)

CATEGORY_ALIASES: Dict[str, str] = {
    "가전/디지털": "전자제품",
    "가전": "전자제품",
    "전자/가전": "전자제품",
    "전자": "전자제품",
    "디지털": "전자제품",
    "의료": "의료/건강",
    "병원": "의료/건강",
    "클리닉": "의료/건강",
    "뷰티": "패션/뷰티",
    "화장품": "패션/뷰티",
    "미용": "패션/뷰티",
    "식품": "식품/음료",
    "음료": "식품/음료",
    "부동산": "부동산/인테리어",
    "인테리어": "부동산/인테리어",
    "리모델링": "부동산/인테리어",
    "금융": "서비스",
    "보험": "서비스",
    "대출": "서비스",
    "투자": "서비스",
    # 비영리/공공 별칭 필수
    "공공": "비영리/공공",
    "비영리": "비영리/공공",
    "정부": "비영리/공공",
    "지자체": "비영리/공공",
    "공공기관": "비영리/공공",
    "정책": "비영리/공공",
    "지원금": "비영리/공공",
    "보조금": "비영리/공공",
    "민원": "비영리/공공",
    "캠페인": "비영리/공공",
    "기부": "비영리/공공",
    "후원": "비영리/공공",
    "ngo": "비영리/공공",
}


# 카테고리 허용 목록 (Allowlist)

# SEMANTIC-only 매칭에서 "서비스"가 포함된 경우는 카테고리 가드에서 추가 필터링됨

CATEGORY_ALLOWLIST: Dict[str, set[str]] = {
    "전자제품": {"전자제품", "생활/건강"},  # "서비스" 제거: 금융/의료 광고주 방지
    "생활/건강": {"생활/건강", "전자제품"},  # "서비스" 제거: 너무 광범위한 매칭 방지
    "의료/건강": {"의료/건강", "서비스"},
    "패션/뷰티": {"패션/뷰티", "생활/건강"},
    "식품/음료": {"식품/음료"},
    "부동산/인테리어": {"부동산/인테리어", "서비스"},
    "교육/도서": {"교육/도서"},
    "비영리/공공": {"비영리/공공", "서비스", "교육/도서"},
    "스포츠/레저/자동차": {"스포츠/레저/자동차", "생활/건강", "서비스"},
    "유아/아동": {"유아/아동", "생활/건강"},
    "여행/문화": {"여행/문화", "서비스"},
    "반려동물": {"반려동물", "생활/건강"},
    "디지털 콘텐츠": {"디지털 콘텐츠", "서비스"},
    "서비스": {"서비스", "생활/건강", "비영리/공공"},
}


# pgvector 코사인 유사도 쿼리 (1 - distance = similarity)

SEMANTIC_MATCH_SQL = """

SELECT

    advertiser_id,

    keyword,

    priority,

    match_type,

    1 - (embedding <=> CAST(:query_embedding AS vector)) AS similarity

FROM advertiser_keywords

WHERE embedding IS NOT NULL

ORDER BY embedding <=> CAST(:query_embedding AS vector)

LIMIT :limit

"""


# Semantic-only 매칭 허용 여부 (기본: 1 = 활성화)

# 1로 설정 시 엄격한 조건 하에 허용, 0이면 무조건 차단

SEMANTIC_ONLY_ENABLED = bool(int(os.getenv("SEMANTIC_ONLY_ENABLED", "1")))


# Semantic-only 매칭에 대한 최소 유사도 임계값 (추가 필터용, 0.75로 상향 조정)

SEMANTIC_ONLY_MIN_SIM = float(os.getenv("SEMANTIC_ONLY_MIN_SIM", "0.75"))


def check_advertiser_passes(
    match_score: float, quality_score: int, min_quality_score: int, reasons: List[str]
) -> tuple[bool, str]:
    """

    광고주 매칭 통과 여부를 판정합니다.



    변경점:

    - Semantic-only 매칭을 완전 차단 대신, 엄격 조건 하에서 허용 (SEMANTIC_ONLY_ENABLED=1 일 때)

    - 나머지 Exact / 일반 케이스는 기존 HIGH/LOW threshold + 품질 조건 유지

    """

    is_exact = any(r.startswith("KW_EXACT") for r in reasons)

    has_keyword = any(r.startswith("KW_") for r in reasons)

    has_category = any(r.startswith("CAT:") for r in reasons)

    has_semantic = any(r.startswith("SEMANTIC:") for r in reasons)

    # 시멘틱만 있는 경우 (키워드/카테고리 매칭 없음)

    semantic_only = has_semantic and not (has_keyword or has_category)

    # 0단계: Semantic-only 필터링 (엄격 허용 모드)

    if semantic_only:

        if not SEMANTIC_ONLY_ENABLED:

            # 완전 차단 모드 (기본값 0)

            return False, "semantic_only_disabled"

        # 시멘틱-only 는 match_score가 충분히 높은 경우에만 허용

        if match_score < SEMANTIC_ONLY_THRESHOLD:

            return (
                False,
                f"semantic_only_low_score:{match_score:.2f}<{SEMANTIC_ONLY_THRESHOLD}",
            )

        # 품질 점수: min_quality_score와 60 중 더 높은 값을 요구

        required_quality = max(min_quality_score, 60)

        if quality_score < required_quality:

            return (
                False,
                f"semantic_only_low_quality:{quality_score}<{required_quality}",
            )

        return True, "SEMANTIC_ONLY_PASS"

    # 1단계: Exact 매칭 (품질 무시 통과, match_score만 충분하면)

    if is_exact and match_score >= MATCH_THRESHOLD_HIGH:

        return True, "EXACT_OVERRIDE"

    # 2단계: 높은 점수 (품질 무시 통과)

    if match_score >= MATCH_THRESHOLD_HIGH:

        return True, ""

    # 3단계: 중간 점수 (품질 체크)

    if match_score >= MATCH_THRESHOLD_LOW:

        if quality_score >= min_quality_score:

            return True, ""

        else:

            return False, f"low_quality:{quality_score}<{min_quality_score}"

    # 4단계: 점수 미달

    return False, f"low_score:{match_score:.2f}<{MATCH_THRESHOLD_LOW}"


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

    # priority: 1~5 범위로 클램프

    p = max(1, min(priority or 1, 5))

    # 🔹 1 → 1.0배, 3 → 약 2.5배, 5 → 약 4.0배 수준의 가중치

    priority_weight = 1.0 + (p**1.5) * 0.3

    increment = base_score * priority_weight

    agg[adv_id]["score"] = min(agg[adv_id]["score"] + increment, SCORE_CAP)

    agg[adv_id]["seen_keys"].add(seen_key)

    agg[adv_id]["reasons"].append(f"KW_{match_type.upper()}:{keyword}")


def _add_semantic_score(agg: dict, adv_id: int, keyword: str, similarity: float):
    """

    시맨틱 매칭 점수를 aggregator에 추가합니다.

    [변경 사항] 점수 누적 방지: 한 광고주에 대해 여러 시맨틱 키워드가 매칭되더라도

    '가장 유사도가 높은 하나'의 점수만 최종 점수에 반영합니다.

    """

    _ensure_aggregator(agg, adv_id)

    seen_key = f"semantic:{keyword}"

    if seen_key in agg[adv_id]["seen_keys"]:

        return

    # 이번 키워드의 기여도 계산

    base = similarity * SEMANTIC_WEIGHT

    # 현재까지 기록된 이 광고주의 '최고 시맨틱 점수' 확인

    current_best = float(agg[adv_id].get("semantic_best", 0.0))

    # 새로운 키워드가 기존 베스트보다 점수가 낮으면 반영 안 함 (Max 전략)

    if base <= current_best:

        # 로그/디버깅을 위해 reasons에는 남길 수 있으나 점수는 올리지 않음

        return

    # 기존 토탈 점수에서 이전 베스트 점수를 빼고, 새로운 베스트 점수를 더함

    non_semantic_score = float(agg[adv_id]["score"]) - current_best

    new_total = non_semantic_score + base

    # Semantic Super Pass: 유사도가 매우 높으면 텍스트 매칭이 없어도

    # 최소 SEMANTIC_SUPER_PASS_SCORE 이상을 보장

    if similarity >= SEMANTIC_SUPER_PASS_SIM:

        new_total = max(new_total, SEMANTIC_SUPER_PASS_SCORE)

    # 상태 업데이트

    agg[adv_id]["semantic_best"] = base

    agg[adv_id]["score"] = min(new_total, SCORE_CAP)

    agg[adv_id]["seen_keys"].add(seen_key)

    agg[adv_id]["reasons"].append(f"SEMANTIC:{keyword}({similarity:.2f})")


async def classify_query_categories(query: str) -> List[str]:
    """

    Gemini를 사용하여 사용자 검색어를 14개 표준 카테고리 중 1~2개로 분류합니다.



    강건화 개선사항:

    - Gemini Raw 응답 로깅

    - CATEGORY_ALIASES를 통한 정규화

    - STANDARD_CATEGORIES 검증

    - Fallback 규칙 기반 분류 (세탁기→전자제품, 성형→의료/건강, 지원금→비영리/공공)

    """

    log = logger.bind(service="auction-service")

    if not SEMANTIC_ENABLED:

        log.debug("query_category_classification_skipped", reason="semantic_disabled")

        return []

    std_list = ", ".join(STANDARD_CATEGORIES)

    prompt = f"""

You are a strict business category classifier for search ads.



Your task:

- Read the Korean user search query.

- Then choose the ONE or TWO most appropriate categories from the following STANDARD_CATEGORIES (in Korean):

  [{std_list}]



Rules:

- You MUST answer with 1 or 2 categories ONLY.

- Each category MUST be EXACTLY one of the STANDARD_CATEGORIES.

- If the query is clearly about insurance, banking, finance, loans, investment, or financial advisory,

  you should usually choose "서비스".

- If the query is about medical treatment, hospitals, clinics, medical services, insurance for medical expenses,

  or health-related services, you should consider "의료/건강" and/or "서비스".

- If the query is about fashion, clothing, shoes, bags, accessories, cosmetics, or beauty,

  choose "패션/뷰티".



User Query (Korean):

"{query}"



Output format:

- Respond with ONE LINE only.

- List 1 or 2 categories separated by a comma, for example:

  의료/건강

  서비스, 의료/건강

Do NOT add any explanations or extra words.

""".strip()

    try:

        model_name = os.getenv("GEMINI_MODEL", "models/gemini-flash-latest")

        model = genai.GenerativeModel(model_name)  # type: ignore[attr-defined]

        res = await asyncio.to_thread(model.generate_content, prompt)

        text_raw = (getattr(res, "text", "") or "").strip()

        # Gemini Raw 응답 로깅

        log.info(
            "query_category_gemini_raw_response", query=query, raw_response=text_raw
        )

        if not text_raw:

            log.warning("query_category_empty_response", query=query)

            # Fallback 규칙 적용

            return _apply_category_fallback_rules(query, log)

        # 응답 텍스트를 쉼표로 분리

        first_line = text_raw.splitlines()[0].strip()

        parts = [p.strip() for p in first_line.split(",")]

        cats: List[str] = []

        for p in parts:

            if not p:

                continue

            # 정규화: 공백/따옴표/괄호 제거

            normalized = p.strip().strip('"').strip("'").strip("(").strip(")").strip()

            if not normalized:

                continue

            # CATEGORY_ALIASES를 통해 표준명으로 변환

            standard_cat = CATEGORY_ALIASES.get(normalized, normalized)

            # STANDARD_CATEGORIES에 포함되는지 검증

            if standard_cat in STANDARD_CATEGORIES and standard_cat not in cats:

                cats.append(standard_cat)

                if len(cats) >= 2:

                    break

        # 결과가 비어있으면 Fallback 규칙 적용

        if not cats:

            log.warning(
                "query_category_parsing_failed", query=query, raw_response=text_raw
            )

            cats = _apply_category_fallback_rules(query, log)

        else:

            # 정규화 후 최종 query_categories 로깅

            log.info(
                "query_category_classified",
                query=query,
                categories=cats,
                raw_response=text_raw,
            )

        return cats

    except Exception as e:

        log.error(
            "query_category_classification_error",
            error=str(e),
            query=query,
            exc_info=True,
        )

        # 에러 발생 시 Fallback 규칙 적용

        return _apply_category_fallback_rules(query, log)


def _apply_category_fallback_rules(query: str, log) -> List[str]:
    """

    카테고리 분류 실패 시 규칙 기반 Fallback을 적용합니다.



    규칙:

    - "세탁기/냉장고/에어컨/TV" 등 → "전자제품"

    - "성형/병원/치과/피부과" 등 → "의료/건강"

    - "지원금/보조금/정부/기부" 등 → "비영리/공공"

    """

    query_lower = query.lower()

    cats: List[str] = []

    # 전자제품 관련 키워드

    electronics_keywords = [
        "세탁기",
        "냉장고",
        "에어컨",
        "tv",
        "텔레비전",
        "스마트폰",
        "노트북",
        "컴퓨터",
        "태블릿",
    ]

    if any(kw in query_lower for kw in electronics_keywords):

        cats.append("전자제품")

        log.info(
            "query_category_fallback_applied",
            query=query,
            category="전자제품",
            reason="electronics_keyword",
        )

        return cats

    # 의료/건강 관련 키워드

    medical_keywords = [
        "성형",
        "병원",
        "치과",
        "피부과",
        "의원",
        "클리닉",
        "진료",
        "수술",
        "치료",
    ]

    if any(kw in query_lower for kw in medical_keywords):

        cats.append("의료/건강")

        log.info(
            "query_category_fallback_applied",
            query=query,
            category="의료/건강",
            reason="medical_keyword",
        )

        return cats

    # 비영리/공공 관련 키워드

    public_keywords = [
        "지원금",
        "보조금",
        "정부",
        "기부",
        "후원",
        "공공",
        "민원",
        "정책",
        "ngo",
    ]

    if any(kw in query_lower for kw in public_keywords):

        cats.append("비영리/공공")

        log.info(
            "query_category_fallback_applied",
            query=query,
            category="비영리/공공",
            reason="public_keyword",
        )

        return cats

    # Fallback 규칙에도 매칭되지 않으면 빈 리스트 반환 (안전 모드 발동)

    log.warning("query_category_fallback_no_match", query=query)

    return []


def _pick_representative_keyword(reasons: list[str]) -> str:
    """

    매칭 근거(reasons) 리스트에서 AI에게 보여줄 '대표 키워드'를 추출.

    우선순위:

    1) KW_* 계열 (키워드 기반 매칭)

    2) SEMANTIC: 계열

    3) 그 외: 첫 번째 reason에서 텍스트 부분만 추출

    """

    if not reasons:

        return ""

    # 1순위: 키워드 기반 매칭

    for r in reasons:

        if r.startswith("KW_") and ":" in r:

            return r.split(":", 1)[1].split("(")[0].strip()

    # 2순위: 시맨틱 기반 매칭

    for r in reasons:

        if r.startswith("SEMANTIC:") and ":" in r:

            return r.split(":", 1)[1].split("(")[0].strip()

    # 3순위: 기타 이유 → 텍스트 부분만 추출

    r = reasons[0]

    if ":" in r:

        r = r.split(":", 1)[1]

    return r.split("(")[0].strip()


async def get_query_embedding(text: str) -> list[float]:
    """
    검색어에 대한 임베딩 벡터를 생성합니다 (Gemini text-embedding-004).

    Args:
        text: 검색어 텍스트

    Returns:
        768차원 임베딩 벡터. 실패 시 빈 리스트 반환.

    Note:
        - task_type='retrieval_query': 검색 쿼리용 임베딩
        - asyncio.to_thread로 동기 API를 논블로킹으로 실행
    """
    if not SEMANTIC_ENABLED:
        return []

    clean = (text or "").strip()
    if not clean:
        return []

    log = logger.bind(service="auction-service", func="get_query_embedding")

    def _embed_sync() -> list[float]:
        """동기 임베딩 함수 (스레드에서 실행됨)"""
        try:
            from typing import Any, cast

            embed_fn = getattr(cast(Any, genai), "embed_content", None)
            if not callable(embed_fn):
                log.error("embed_content_not_found")
                return []

            res = embed_fn(
                model="models/text-embedding-004",
                content=clean,
                task_type="retrieval_query",  # 검색 쿼리용
            )

            # 응답 구조 방어적 파싱
            embedding = None

            if isinstance(res, dict):
                emb = res.get("embedding")
                if isinstance(emb, dict) and "values" in emb:
                    embedding = emb["values"]
                elif isinstance(emb, list):
                    embedding = emb
                elif "values" in res:
                    embedding = res["values"]
            else:
                emb_obj = getattr(res, "embedding", None)
                if emb_obj is not None:
                    if isinstance(emb_obj, list):
                        embedding = emb_obj
                    else:
                        vals = getattr(emb_obj, "values", None)
                        if vals is not None:
                            embedding = vals

            if embedding is None:
                log.warning("embedding_not_found_in_response")
                return []

            return list(embedding)
        except Exception as e:
            log.error("embedding_sync_error", error=str(e))
            return []

    try:
        vector = await asyncio.to_thread(_embed_sync)
        if vector:
            log.debug("query_embedding_success", dim=len(vector), text=clean[:30])
        return vector
    except Exception as e:
        log.error("embedding_async_error", error=str(e))
        return []


# ============================================

# [New] LLM 기반 Intent 검증 (최종 Reranking용)

# ============================================


def _call_gemini_sync_for_intent(prompt: str) -> str:
    """

    Gemini를 동기 방식으로 호출하는 헬퍼 함수.

    - generate_content_async 대신, 기존 get_query_embedding처럼 to_thread 패턴 사용

    - 예외 발생 시 빈 문자열 반환

    """

    try:

        if not genai:

            logger.warning("ai_verification_skipped", reason="genai_not_available")

            return ""

        # 올바른 모델명 형식: "models/gemini-flash-latest" 또는 "models/gemini-1.5-flash"

        model_name = os.getenv("GEMINI_MODEL", "models/gemini-flash-latest")

        model = genai.GenerativeModel(model_name)

        res = model.generate_content(prompt)

        text = getattr(res, "text", "") or ""

        return text.strip()

    except Exception as e:

        logger.error(
            "ai_verification_failed_sync",
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )

        return ""


async def verify_intent_with_gemini(query: str, candidate_keyword: str) -> bool:
    """

    Gemini를 이용해 '사용자 검색어'와 '광고 키워드'의 의도 일치 여부를 판단.



    반환:

    - True  : 적절한 매칭 (통과)

    - False : 부적절한 매칭 (차단)

    - SEMANTIC_ENABLED == False 이거나 에러 시 → True (관대하게 통과, 서비스 중단 방지)

    """

    if not SEMANTIC_ENABLED:

        # 시맨틱 비활성화 환경에서는 검증을 건너뜀

        return True

    # 프롬프트: 매우 엄격한 심판 역할 부여 + 출력 형식 고정

    prompt = f"""

You are a strict search ad quality evaluator.



User Query: "{query}"

Ad Keyword: "{candidate_keyword}"



Task:

Determine if the Ad Keyword is relevant and appropriate for the User Query.



BLOCK (return FALSE) if:

1. User wants INSURANCE but Ad is CAR SALES (or vice versa).

2. User wants REPAIR/SERVICE but Ad is SALES.

3. User wants RENTAL but Ad is SALES.

4. User wants CHEAP/USED but Ad is LUXURY/NEW.

5. User intent and Ad intent are clearly different (e.g., 'car insurance' vs 'car purchase').

6. The PRODUCT CATEGORY of the Ad Keyword does NOT clearly match the PRODUCT CATEGORY implied by the User Query.

   - If the query is about GLASSES / EYEWEAR / VISION (e.g., reading glasses, blue light glasses, contact lenses)

     and the ad is about SHAMPOO, BEAUTY, COSMETICS, SUPPLEMENTS, or unrelated E-COMMERCE PRODUCTS, you MUST return FALSE.

   - Even if the query mentions GIFT or PRESENT, if the underlying product category is different

     (e.g., Query: "reading glasses for parents", Ad: "shampoo", "beauty", "vitamins", "general e-commerce"),

     you MUST treat it as MISMATCH and return FALSE.

   - Only return TRUE when both INTENT and PRODUCT CATEGORY are strongly aligned.



Output:

Return exactly ONE WORD in UPPERCASE:

- "TRUE"  if it is a good match.

- "FALSE" if it is a bad match.



Do NOT add any explanation.

"""

    try:

        # 동기 호출을 별도 스레드에서 실행하여 논블로킹 유지

        raw = await asyncio.to_thread(_call_gemini_sync_for_intent, prompt)

        result = (raw or "").strip().upper()

        # 방어적 파싱: 맨 앞 단어만 본다

        if result.startswith("FALSE"):

            return False

        if result.startswith("TRUE"):

            return True

        # 모호한 응답이면 차단 (False 반환)

        logger.warning(
            "ai_verification_ambiguous_response",
            query=query,
            candidate_keyword=candidate_keyword,
            raw_response=raw,
            result=result,
        )

        return False

    except Exception as e:

        logger.error(
            "ai_verification_failed",
            error=str(e),
            error_type=type(e).__name__,
            query=query,
            candidate_keyword=candidate_keyword,
            exc_info=True,
        )

        # 에러가 났다고 전체 매칭을 막지는 않는다.

        return True


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

    # --- 1-A. AI 작업을 백그라운드로 시작 (SEMANTIC_ENABLED일 때만) ---

    task_cat: asyncio.Task[List[str]] | None = None

    task_emb: asyncio.Task[List[float]] | None = None

    if SEMANTIC_ENABLED:

        task_cat = asyncio.create_task(classify_query_categories(search_query))

        task_emb = asyncio.create_task(get_query_embedding(search_query))

    aggregator: Dict[int, Dict[str, Any]] = {}

    # 카테고리 기반 화이트리스트 (있을 경우, 이 집합 안의 광고주만 최종 후보로 사용)

    category_whitelist: set[int] = set()

    # --- 1-B. 독립적인 텍스트 기반 DB 쿼리를 병렬 실행 ---

    # === EXACT (동적 IN) ===

    exact_in, exact_params = _make_in_clause(
        "lower(replace(keyword, ' ', ''))", tokens_norm, "ex"
    )

    exact_sql_dynamic = f"""

        SELECT advertiser_id, keyword, priority, match_type

        FROM advertiser_keywords

        WHERE match_type = 'exact' AND {exact_in}

    """

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

    # === BROAD (양방향 매칭: 검색어↔키워드 상호 포함) ===

    # pg_trgm 연산자 사용으로 인덱스 활용 (Full Scan 방지)

    query_norm_full = _normalize(search_query)

    broad_sql_dynamic = """

        SELECT advertiser_id, keyword, priority, match_type

        FROM advertiser_keywords

        WHERE match_type = 'broad'

          AND (

            lower(replace(keyword, ' ', '')) % :query_norm

            OR similarity(lower(replace(keyword, ' ', '')), :query_norm) > 0.3

            OR :query_norm % lower(replace(keyword, ' ', ''))

          )

    """

    # === CATEGORY (tokens_like가 있을 때만 실행) ===

    async def run_category_query() -> list[Any]:

        if not tokens_like:

            return []

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

        return await database.fetch_all(category_sql_dynamic, cat_params)

    # 병렬 실행: Exact, Phrase, Broad, Category

    exact_task = database.fetch_all(exact_sql_dynamic, exact_params)

    phrase_task = database.fetch_all(phrase_sql_dynamic, phrase_params)

    broad_task = database.fetch_all(broad_sql_dynamic, {"query_norm": query_norm_full})

    category_task = run_category_query()

    exact_rows, phrase_rows, broad_rows, rows_cat = await asyncio.gather(
        exact_task, phrase_task, broad_task, category_task
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

    # 카테고리 매칭 결과 처리
    for r in rows_cat:
        adv_id = r["advertiser_id"]
        # 카테고리 기반 화이트리스트 구성
        category_whitelist.add(int(adv_id))
        _ensure_aggregator(aggregator, adv_id)

        path = r["category_path"] or ""
        # 예: "전자/스마트폰/아이폰" → depth = 3
        depth = path.count("/") + 1

        base = 0.7
        depth_weight = 1 + 0.2 * min(depth, 4)  # depth 1~4 → 1.0~1.8
        primary_weight = 1.5 if r["is_primary"] else 1.0

        cat_score = base * depth_weight * primary_weight

        seen_key = f"CAT:{path}"
        if seen_key not in aggregator[adv_id]["seen_keys"]:
            aggregator[adv_id]["score"] = min(
                aggregator[adv_id]["score"] + cat_score, SCORE_CAP
            )
            aggregator[adv_id]["seen_keys"].add(seen_key)
            aggregator[adv_id]["reasons"].append(seen_key)

    # --- 1-C. AI 작업을 필요할 때만 await ---
    # task_cat은 advertiser.category whitelist 로직 직전에 await
    query_categories: List[str] = []
    advertiser_category_whitelist: set[int] = set()

    if task_cat is not None:
        query_categories = await task_cat
        if query_categories:
            try:
                rows = await database.fetch_all(
                    """
                    SELECT id
                    FROM advertisers
                    WHERE category = ANY(:cats)
                    """,
                    {"cats": query_categories},
                )
                advertiser_category_whitelist = {int(r["id"]) for r in rows}  # type: ignore[index]
                log.info(
                    "query_category_whitelist_built",
                    query=search_query,
                    query_categories=query_categories,
                    whitelist_size=len(advertiser_category_whitelist),
                )
            except Exception as e:
                log.error(
                    "query_category_whitelist_error",
                    error=str(e),
                    query=search_query,
                    query_categories=query_categories,
                    exc_info=True,
                )
                advertiser_category_whitelist = set()

    # === 시맨틱 매칭 (pgvector + Gemini Embedding) ===
    # task_emb는 semantic matching 로직 직전에 await
    if SEMANTIC_ENABLED and task_emb is not None:
        query_embedding = await task_emb
        if query_embedding:
            log.debug(
                "semantic_matching_start",
                query=search_query,
                embedding_dim=len(query_embedding),
            )
            try:
                # pgvector 코사인 유사도 검색
                # PostgreSQL 배열 형식으로 변환: [1.0,2.0,3.0]
                embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"

                semantic_rows = await database.fetch_all(
                    SEMANTIC_MATCH_SQL,
                    {
                        "query_embedding": embedding_str,
                        "limit": SEMANTIC_MATCH_LIMIT,
                    },
                )

                semantic_match_count = 0

                for r in semantic_rows:

                    keyword = r["keyword"]

                    similarity = float(r["similarity"])

                    # 1) Hard Negative 룰로 명백히 잘못된 조합 차단

                    if has_hard_negative(search_query, keyword):

                        log.info(
                            "semantic_hard_negative_skipped",
                            query=search_query,
                            keyword=keyword,
                            similarity=similarity,
                        )

                        continue

                    # 2) 유사도 임계값 필터링

                    if similarity >= SEMANTIC_SIM_THRESHOLD:

                        _add_semantic_score(
                            aggregator,
                            r["advertiser_id"],
                            keyword,
                            similarity,
                        )

                        semantic_match_count += 1

                log.info(
                    "semantic_matching_complete",
                    query=search_query,
                    total_candidates=len(semantic_rows),
                    matched_count=semantic_match_count,
                    threshold=SEMANTIC_SIM_THRESHOLD,
                )

            except Exception as e:

                log.error("semantic_matching_error", error=str(e), exc_info=True)

        else:

            log.debug("semantic_matching_skipped", reason="embedding_failed")

    else:

        log.debug("semantic_matching_disabled")

    # === 카테고리 우선 필터링 ===

    # 1) advertiser_categories 기반 화이트리스트 (검색어 토큰과 비즈니스 카테고리 매칭)

    if category_whitelist:

        before_cnt = len(aggregator)

        filtered = {
            adv_id: data
            for adv_id, data in aggregator.items()
            if adv_id in category_whitelist
        }

        after_cnt = len(filtered)

        # 카테고리로 걸러도 후보가 남아있을 때만 적용 (없으면 원래 aggregator 유지 = Fallback)

        if after_cnt > 0:

            aggregator = filtered

        log.info(
            "category_whitelist_applied",
            query=search_query,
            whitelist_size=len(category_whitelist),
            total_before=before_cnt,
            total_after=after_cnt,
        )

    # 2) advertisers.category 기반 화이트리스트 (쿼리 카테고리 분류 결과와 동일한 광고주만 사용)

    # 단, 키워드 매칭(KW_*)이 있는 광고주는 카테고리 불일치해도 유지 (정확한 키워드 매칭 우선)

    if advertiser_category_whitelist:

        before_cnt = len(aggregator)

        filtered = {}

        keyword_matched_kept = []

        for adv_id, data in aggregator.items():

            reasons = data.get("reasons", [])

            has_keyword_match = any(r.startswith("KW_") for r in reasons)

            # 키워드 매칭이 있으면 카테고리 불일치해도 유지

            if has_keyword_match:

                filtered[adv_id] = data

                keyword_matched_kept.append(adv_id)

            # 키워드 매칭이 없으면 카테고리 whitelist 체크

            elif adv_id in advertiser_category_whitelist:

                filtered[adv_id] = data

        after_cnt = len(filtered)

        # 필터링 결과가 있으면 적용, 없으면 기존 aggregator 유지

        if after_cnt > 0:

            aggregator = filtered

        log.info(
            "advertiser_category_whitelist_applied",
            query=search_query,
            query_categories=query_categories,
            whitelist_size=len(advertiser_category_whitelist),
            total_before=before_cnt,
            total_after=after_cnt,
            keyword_matched_kept=len(keyword_matched_kept),
        )

    if not aggregator:

        return []

    # === 카테고리 가드 적용 (query_categories 기반 필터링) ===

    # aggregator가 구성된 직후, 점수 계산 후, 최종 필터링 전에 적용

    dropped_adv_ids: List[int] = []

    dropped_reasons: List[str] = []

    if query_categories:

        # query_categories가 존재하는 경우: 첫 번째 카테고리의 Allowlist에 광고주 카테고리가 없으면 제거

        primary_query_category = query_categories[0]

        allowlist = CATEGORY_ALLOWLIST.get(primary_query_category, set())

        # 광고주 카테고리 일괄 조회 (N+1 방지)

        adv_ids_for_category_check = list(aggregator.keys())

        if adv_ids_for_category_check:

            adv_ids_in_clause, adv_ids_params = _make_in_clause(
                "id", adv_ids_for_category_check, "advcat"
            )

            advertiser_category_query = f"""

                SELECT id, category

                FROM advertisers

                WHERE {adv_ids_in_clause}

            """

            advertiser_category_rows = await database.fetch_all(
                advertiser_category_query, adv_ids_params
            )

            advertiser_category_map = {
                int(r["id"]): dict(r).get("category") for r in advertiser_category_rows
            }

            # 필터링: Allowlist에 없거나 NULL이면 제거

            # 단, 키워드 매칭(KW_*)이 있는 경우 카테고리 가드 완화 적용

            filtered_aggregator = {}

            for adv_id, data in aggregator.items():

                reasons = data.get("reasons", [])

                has_keyword_match = any(r.startswith("KW_") for r in reasons)

                has_category_match = any(r.startswith("CAT:") for r in reasons)

                has_semantic_only = any(
                    r.startswith("SEMANTIC:") for r in reasons
                ) and not (has_keyword_match or has_category_match)

                adv_category = advertiser_category_map.get(adv_id)

                # 키워드나 카테고리 매칭이 있는 경우: 카테고리 가드 완화

                # - 광고주 카테고리가 NULL이 아니고, allowlist에 없어도 키워드/카테고리 매칭이면 통과 허용

                if (
                    has_keyword_match or has_category_match
                ) and adv_category is not None:

                    # 키워드/카테고리 매칭이 있으면 카테고리가 allowlist에 없어도 통과

                    filtered_aggregator[adv_id] = data

                    log.debug(
                        "category_guard_bypassed_for_keyword_match",
                        advertiser_id=adv_id,
                        category=adv_category,
                        allowlist=list(allowlist),
                        reasons=reasons[:2],  # 처음 2개만 로깅
                    )

                    continue

                # SEMANTIC-only 매칭인 경우: 카테고리 가드를 엄격하게 적용

                # 단, 키워드 매칭이 있으면 NULL 카테고리도 허용 (정확한 키워드 매칭 우선)

                if adv_category is None:

                    if has_keyword_match or has_category_match:

                        # 키워드/카테고리 매칭이 있으면 NULL 카테고리도 통과

                        filtered_aggregator[adv_id] = data

                        log.debug(
                            "category_guard_bypassed_null_for_keyword_match",
                            advertiser_id=adv_id,
                            reasons=reasons[:2],
                        )

                        continue

                    else:

                        # SEMANTIC-only이고 NULL 카테고리면 차단

                        dropped_adv_ids.append(adv_id)

                        dropped_reasons.append(
                            "dropped_by_category_guard:null_category"
                        )

                        continue

                if adv_category not in allowlist:

                    dropped_adv_ids.append(adv_id)

                    dropped_reasons.append(
                        f"dropped_by_category_guard:category_not_in_allowlist:{adv_category}"
                    )

                    continue

                filtered_aggregator[adv_id] = data

            aggregator = filtered_aggregator

            log.info(
                "category_guard_applied",
                query=search_query,
                query_categories=query_categories,
                primary_category=primary_query_category,
                allowlist=list(allowlist),
                dropped_count=len(dropped_adv_ids),
                remaining_count=len(aggregator),
            )

    else:

        # query_categories가 비어있는 경우: "안전 모드" 발동

        # SEMANTIC-only로 들어온 후보는 전량 제거

        # 오직 키워드(KW_*)나 카테고리(CAT:*) 매칭이 있는 후보만 허용

        filtered_aggregator = {}

        for adv_id, data in aggregator.items():

            reasons = data.get("reasons", [])

            has_keyword = any(r.startswith("KW_") for r in reasons)

            has_category = any(r.startswith("CAT:") for r in reasons)

            has_semantic_only = any(
                r.startswith("SEMANTIC:") for r in reasons
            ) and not (has_keyword or has_category)

            if has_semantic_only:

                dropped_adv_ids.append(adv_id)

                dropped_reasons.append("dropped_by_safety_mode:semantic_only")

                continue

            filtered_aggregator[adv_id] = data

        aggregator = filtered_aggregator

        log.info(
            "safety_mode_activated",
            query=search_query,
            dropped_count=len(dropped_adv_ids),
            remaining_count=len(aggregator),
        )

    # Drop된 광고주 로깅

    if dropped_adv_ids:

        log.info(
            "category_guard_dropped_advertisers",
            query=search_query,
            dropped_adv_ids=dropped_adv_ids,
            dropped_reasons=dropped_reasons,
        )

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

    # 4) 정책 필터링 및 정렬 (개선된 로직)

    final_advertisers = []

    for adv_id, data in aggregator.items():

        settings = abs_map.get(adv_id)

        if not settings:

            log.debug(
                "bid_filtering_result",
                advertiser_id=adv_id,
                keyword_matched=data["reasons"],
                match_score=round(data["score"], 3),
                result="FAIL",
                fail_reason="no_auto_bid_settings",
            )

            continue

        match_score = data["score"]

        min_quality_score = (
            settings["min_quality_score"] if settings["min_quality_score"] else 50
        )

        # 개선된 통과 로직 적용

        passes, fail_reason = check_advertiser_passes(
            match_score=match_score,
            quality_score=quality_score,
            min_quality_score=min_quality_score,
            reasons=data["reasons"],
        )

        # 상세 로깅

        log.debug(
            "bid_filtering_result",
            advertiser_id=adv_id,
            keyword_matched=data["reasons"],
            match_type=(
                data["reasons"][0].split(":")[0] if data["reasons"] else "unknown"
            ),
            match_score=round(match_score, 3),
            user_quality_score=quality_score,
            min_quality_score=min_quality_score,
            threshold_high=MATCH_THRESHOLD_HIGH,
            threshold_low=MATCH_THRESHOLD_LOW,
            result="PASS" if passes else "FAIL",
            fail_reason=fail_reason if not passes else None,
        )

        if passes:

            final_advertisers.append(
                {
                    "advertiser_id": adv_id,
                    "match_score": match_score,
                    "reasons": data["reasons"],
                }
            )

    # 시맨틱 매칭으로 추가된 광고주 수 계산

    semantic_matches = sum(
        1
        for adv_id, data in aggregator.items()
        if any(r.startswith("SEMANTIC:") for r in data["reasons"])
    )

    # === 5) 최종 필터링 단계 (Hard Negative + Semantic-only 추가 필터) ===

    filtered_advertisers: list[dict[str, Any]] = []

    for adv in final_advertisers:

        adv_id = adv["advertiser_id"]

        reasons: list[str] = adv.get("reasons", [])

        # 5-1. Hard Negative 재검증 (KW_*, SEMANTIC:* 이유 기반)

        blocked = False

        for reason in reasons:

            if reason.startswith("KW_") or reason.startswith("SEMANTIC:"):

                try:

                    # "KW_EXACT:아이폰16 사전예약" 또는 "SEMANTIC:아이폰 케이스(0.82)"

                    _, raw = reason.split(":", 1)

                    keyword_text = raw.split("(", 1)[0].strip()

                except ValueError:

                    continue

                if has_hard_negative(search_query, keyword_text):

                    log.info(
                        "hard_negative_filtered_after_scoring",
                        advertiser_id=adv_id,
                        keyword=keyword_text,
                        query=search_query,
                    )

                    blocked = True

                    break

        if blocked:

            continue

        # 5-2. Semantic-only에 대한 추가 유사도 필터

        has_keyword = any(r.startswith("KW_") or r.startswith("CAT:") for r in reasons)

        has_semantic = any(r.startswith("SEMANTIC:") for r in reasons)

        if (not has_keyword) and has_semantic:

            semantic_sims: list[float] = []

            for r in reasons:

                if r.startswith("SEMANTIC:") and "(" in r:

                    try:

                        sim_str = r.split("(", 1)[1].rstrip(")")

                        semantic_sims.append(float(sim_str))

                    except Exception:

                        continue

            if semantic_sims:

                max_sim = max(semantic_sims)

                if max_sim < SEMANTIC_ONLY_MIN_SIM:

                    log.debug(
                        "semantic_only_low_similarity_filtered",
                        advertiser_id=adv_id,
                        similarity=max_sim,
                        threshold=SEMANTIC_ONLY_MIN_SIM,
                    )

                    continue

        filtered_advertisers.append(adv)

    # === 6) 최종 로그 & 반환 ===

    log.info(
        "matching_complete",
        query=search_query,
        total_candidates=len(aggregator),
        passed_count=len(filtered_advertisers),
        failed_count=len(aggregator) - len(filtered_advertisers),
        semantic_enabled=SEMANTIC_ENABLED,
        semantic_matches=semantic_matches,
    )

    # --------------- [New] LLM 기반 최종 Intent 검증 단계 (1-D. Bounded Concurrency) ---------------

    # 1차 필터링까지 통과한 광고주 목록을 점수 순으로 정렬

    sorted_candidates = sorted(
        filtered_advertisers, key=lambda x: x["match_score"], reverse=True
    )

    # 후보가 너무 적으면 그대로 반환

    if not sorted_candidates:

        return []

    # 상위 N개(기본 3개)만 AI 정밀 검증 (속도/비용 고려)

    TOP_N_FOR_AI = 3

    top_candidates = sorted_candidates[:TOP_N_FOR_AI]

    remaining = sorted_candidates[TOP_N_FOR_AI:]

    # --- 1-D. Intent verification을 bounded concurrency로 병렬화 ---

    sem = asyncio.Semaphore(3)  # 최대 3개 동시 Gemini 호출

    async def verify_candidate(adv: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        """단일 후보를 검증하는 헬퍼 함수"""

        reasons = adv.get("reasons") or []

        keyword_text = _pick_representative_keyword(reasons)

        # 대표 키워드를 뽑지 못하면 AI 검증 없이 통과

        if not keyword_text:

            return adv, True

        # Semaphore로 동시 호출 수 제한

        async with sem:

            is_valid = await verify_intent_with_gemini(search_query, keyword_text)

        if not is_valid:

            log.info(
                "ai_blocked_mismatch",
                query=search_query,
                keyword=keyword_text,
                advertiser_id=adv.get("advertiser_id"),
                match_score=adv.get("match_score"),
            )

        return adv, is_valid

    # 모든 top candidates를 병렬로 검증

    verification_results = await asyncio.gather(
        *[verify_candidate(adv) for adv in top_candidates],
        return_exceptions=True,
    )

    # 결과 수집: 통과한 후보만 final_verified_top에 추가

    final_verified_top: list[dict] = []

    for result in verification_results:

        if isinstance(result, Exception):

            log.error(
                "intent_verification_error",
                error=str(result),
                exc_info=True,
            )

            continue

        # 타입 가드: Exception이 아니면 tuple[dict, bool]임

        if isinstance(result, tuple) and len(result) == 2:

            adv, is_valid = result

            if is_valid:

                final_verified_top.append(adv)

    # 만약 AI가 상위 후보들을 모두 잘라냈다면, 차단된 후보를 되살리지 않는다.

    # - final_verified_top 이 비어있고 remaining 도 없다면 → 광고 미노출 (빈 리스트 반환)

    # - remaining 이 있다면 → AI 검증을 거치지 않은 "하위 순위" 후보들만으로 경매 진행

    if not final_verified_top:

        log.warning(
            "ai_verification_removed_all_top_candidates",
            query=search_query,
            total_candidates=len(sorted_candidates),
        )

        # 상위 후보는 모두 차단되었으므로 resurrect 금지

        if not remaining:

            return []

        return sorted(remaining, key=lambda x: x["match_score"], reverse=True)

    # 최종 리스트 = AI 검증 통과한 상위권 + 나머지 후보들

    final_list = final_verified_top + remaining

    # 다시 match_score 순으로 정렬하여 반환

    return sorted(final_list, key=lambda x: x["match_score"], reverse=True)


# --- 2. 자동 입찰가 계산 알고리즘 ---


async def calculate_auto_bid_price(
    match_score: float,
    quality_score: int,  # 🔹 사용자 검색어 품질 점수
    settings: Dict[str, Any],
    review: Dict[str, Any] | None,
) -> int:
    """

    매칭 점수와 광고주 설정, 품질 점수를 기반으로 최적 입찰가 계산 (DB 조회 없음)



    변경점:

    - match_score를 1.5 기준으로 스케일링하여, 높은 점수일수록 입찰가를 100~200%까지 상승

    - 저품질 Exact 매칭에 대해 Risk Discount를 적용

    """

    if not settings:

        return 0

    max_bid = int(settings["max_bid_per_keyword"] or 0)

    # 1) 매칭 점수 스케일링

    #    - match_score 1.5 → 1.0배

    #    - match_score 3.0 → 2.0배 (상한)

    scaled_score = match_score / 1.5

    scaled_score = max(0.3, min(scaled_score, 2.0))  # 너무 낮거나 높은 값 클램프

    base_bid = int(max_bid * scaled_score)

    # 2) 리스크 조정 계수 (저품질 방어)

    risk_factor = 1.0

    # 기본: match_score가 높더라도 저품질이면 할인

    if match_score >= MATCH_THRESHOLD_HIGH:

        if quality_score < 30:

            # 매우 낮은 품질: 강한 할인

            risk_factor = min(RISK_DISCOUNT_FACTOR, 0.5)

        elif quality_score < 40:

            # 낮은 품질: 중간 수준 할인

            risk_factor = min(RISK_DISCOUNT_FACTOR, 0.6)

        elif quality_score < LOW_QUALITY_RISK_THRESHOLD:

            # 경계 구간: 환경변수에 정의된 기본 할인 사용

            risk_factor = RISK_DISCOUNT_FACTOR

        else:

            risk_factor = 1.0

    final_bid = int(base_bid * risk_factor)

    # 3) 리뷰 기반 권장 범위에 맞춰 보정

    if review:

        final_bid = max(
            review.get("recommended_bid_min", 0) or 0,
            min(final_bid, review.get("recommended_bid_max", final_bid) or final_bid),
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



    변경점:

    - 플랫폼 폴백을 절대 생성하지 않음

    - 매칭된 광고주가 없거나 valid bids가 없으면 빈 리스트 반환

    """

    log = logger.bind(service="auction-service")

    log.info(
        "auction_matching_start",
        query=search_query,
        quality_score=quality_score,
    )

    # 1) 키워드/카테고리 기반 매칭

    matching_advertisers = await find_matching_advertisers(search_query, quality_score)

    if not matching_advertisers:

        log.warning("no_matching_advertisers", query=search_query)

        return []

    advertiser_ids = [m["advertiser_id"] for m in matching_advertisers]

    # 2) 광고주 상세 정보 + 자동 입찰 설정 + 리뷰 정보 일괄 조회

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

        # 🔹 품질 점수까지 고려한 자동 입찰가 계산 (Risk Discount 포함)

        bid_price = await calculate_auto_bid_price(
            match_score, quality_score, settings, review
        )

        if bid_price <= 0:

            continue

        # 🔹 Exact + 저품질 구간에 대한 리스크 태그 추가 (리포팅/분석용)

        is_exact = any(r.startswith("KW_EXACT") for r in reasons)

        if (
            is_exact
            and match_score >= MATCH_THRESHOLD_HIGH
            and quality_score < LOW_QUALITY_RISK_THRESHOLD
        ):

            reasons = list(reasons) + [f"RISK:EXACT_LOW_QUALITY:{quality_score}"]

        # 예산 확인은 나중에 reserve_and_insert_bid에서 트랜잭션으로 처리

        import uuid

        bid_id = (
            f"bid_real_{adv_id}_{int(datetime.now(timezone.utc).timestamp())}_"
            f"{uuid.uuid4().hex[:8]}"
        )

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

        return []

    # 정확도(matchScore) 우선 정렬, 그 다음 가격(price)

    return sorted(real_bids, key=lambda x: ((x.matchScore or 0), x.price), reverse=True)


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
    search_query: str, quality_score: int, current_highest_bid: int = 0
) -> List[BidResponse]:
    """

    광고주 매칭이 실패했을 때 또는 보완이 필요할 때 플랫폼 사업자들이 제공하는

    적립 입찰을 생성합니다.



    변경점:

    - 실제 광고주가 존재한다면, Fallback 입찰가는 무조건 그보다 낮게 설정됩니다.

    - current_highest_bid > 0: base_price = max(50, current_highest_bid - 10)

    - current_highest_bid == 0: base_price = 200 (기존 유지)

    """

    log = logger.bind(service="auction-service")

    log.info("platform_fallback_bids_creating", current_highest_bid=current_highest_bid)

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

    now = datetime.now(timezone.utc)

    # 동적 가격 결정: 실제 광고주 우대 정책

    if current_highest_bid > 0:

        # 실제 광고주가 존재: 최고 입찰가보다 10원 싸게, 최소 50원

        base_price = max(50, current_highest_bid - 10)

    else:

        # 실제 광고주 없음: 기존 200원 유지

        base_price = 200

    fallback_bids = []

    for i, buyer in enumerate(platform_buyers):

        import uuid

        bid_id = f"platform_bid_{buyer['name_en']}_{int(now.timestamp())}_{i}"

        # 안전장치: current_highest_bid를 절대 넘지 않도록

        this_bid_price = (
            min(base_price, current_highest_bid)
            if current_highest_bid > 0
            else base_price
        )

        bid_type = "PLATFORM"

        sig = sign_click(bid_id, this_bid_price, bid_type)

        click_url = f"{REDIRECT_BASE_URL}/api/redirect/{bid_id}?sig={sig}"

        fallback_bids.append(
            BidResponse(
                id=bid_id,
                buyerName="Intendex",
                price=this_bid_price,
                bonus=buyer["bonus"],
                timestamp=now,
                landingUrl=buyer["url"],
                clickUrl=click_url,
                advertiserId=PLATFORM_ADVERTISER_ID,
                matchScore=1.0,
                reasons=[f"PLATFORM:{buyer['name_en']}"],
            )
        )

    log.info(
        "platform_fallback_bids_created",
        count=len(fallback_bids),
        base_price=base_price,
        current_highest_bid=current_highest_bid,
    )

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

    역경매를 시작합니다. (개선된 버전)



    변경점:

    - 실제 광고주 매칭 결과에서 highest_real_bid를 계산

    - 광고주 0명인 경우에만 플랫폼 폴백 생성

    - 입찰가가 너무 낮은 경우(예: 300원 미만)에만 플랫폼 폴백을 "추가로" 섞어서 경쟁 유도

    - 실제 광고주 우대 정책: Fallback 입찰가는 항상 실제 광고주보다 낮게 설정

    """

    log = logger.bind(service="auction-service")

    log.info("reverse_auction_start", query=query, quality_score=value_score)

    # 1) 실제 광고주 매칭 시도

    bids = await generate_real_advertiser_bids(query, value_score)

    # 2) 실제 광고주 최고 입찰가 계산 (bids가 비어있으면 0)

    highest_real_bid = max(
        (b.price for b in bids if b.price and b.price > 0), default=0
    )

    # 3) 광고주 0명인 경우 → 플랫폼 폴백으로 대체

    if not bids:

        log.warning("no_bids_generated_real_advertiser", query=query)

        bids = generate_platform_fallback_bids(
            query, value_score, current_highest_bid=0
        )

        await log_auto_bids(bids, query, value_score)

        log.info("reverse_auction_complete", bid_count=len(bids))

        for i, bid in enumerate(bids):

            log.debug("bid_detail", index=i + 1, buyer=bid.buyerName, price=bid.price)

        return bids

    # 4) 입찰가가 너무 낮은 경우(예: 300원 미만) → 플랫폼 폴백을 "추가로" 섞어서 경쟁 유도

    if highest_real_bid < 300:

        log.info(
            "real_bids_too_low_add_platform_fallback",
            highest_real_bid=highest_real_bid,
            query=query,
        )

        fallback_bids = generate_platform_fallback_bids(
            query, value_score, current_highest_bid=highest_real_bid
        )

        bids.extend(fallback_bids)

    # 5) 가격 내림차순으로 정렬 (실제 광고주가 항상 상위에 위치)

    bids = sorted(bids, key=lambda x: x.price, reverse=True)

    # 6) 자동 입찰 결과 DB에 기록

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

        # --- 2-A. 입찰 정보를 DB에 저장 (예산 예약과 함께 하나의 트랜잭션으로 처리) ---

        # 같은 advertiser의 bid는 순차 실행, 다른 advertiser 그룹은 병렬 실행

        # 1단계: bids를 advertiserId로 그룹화

        bid_groups: Dict[int | None, List[BidResponse]] = defaultdict(list)

        for bid in bids:

            # 광고주 ID가 BidResponse에 없으면 bid_id에서 추출 시도

            if not bid.advertiserId and bid.id.startswith("bid_real_"):

                try:

                    parts = bid.id.split("_")

                    if len(parts) >= 3:

                        bid.advertiserId = int(parts[2])

                except (ValueError, IndexError):

                    pass

            # PLATFORM bid는 None으로 그룹화 (플랫폼 bid는 예산 예약 없음)

            adv_id = (
                bid.advertiserId if not bid.id.startswith("platform_bid_") else None
            )

            bid_groups[adv_id].append(bid)

        # 2단계: 각 그룹 내부는 순차 실행, 그룹 간은 병렬 실행

        async def process_bid_group(group_bids: List[BidResponse]) -> List[BidResponse]:
            """같은 advertiser의 bid들을 순차적으로 처리"""

            successful: List[BidResponse] = []

            for bid in group_bids:

                try:

                    success = await reserve_and_insert_bid(
                        auction_id, user_id if user_id else 1, bid
                    )

                    if success:

                        successful.append(bid)

                    else:

                        logger.warning(
                            "bid_insert_failed",
                            bid_id=bid.id,
                            advertiser_id=bid.advertiserId,
                            reason="budget_insufficient_or_db_error",
                        )

                except Exception as e:

                    logger.error(
                        "bid_insert_exception",
                        bid_id=bid.id,
                        advertiser_id=bid.advertiserId,
                        error=str(e),
                        exc_info=True,
                    )

            return successful

        # 2-B. 모든 그룹을 병렬로 실행 (return_exceptions=True로 에러 처리)

        group_results = await asyncio.gather(
            *[process_bid_group(group_bids) for group_bids in bid_groups.values()],
            return_exceptions=True,
        )

        # 결과 수집: 성공한 bid만 모음

        successful_bids: List[BidResponse] = []

        for result in group_results:

            if isinstance(result, Exception):

                logger.error(
                    "bid_group_processing_error",
                    error=str(result),
                    exc_info=True,
                )

                continue

            # 타입 가드: Exception이 아니면 List[BidResponse]임

            if isinstance(result, list):

                successful_bids.extend(result)

        # 최소한 하나의 bid라도 저장되어야 함 (없으면 플랫폼 폴백 처리)

        if not successful_bids:

            logger.error("no_bids_stored", auction_id=auction_id)

            # 모든 입찰이 실패했을 경우 빈 리스트 반환 또는 플랫폼 폴백 재생성

            bids = generate_platform_fallback_bids(
                request.query, request.valueScore, current_highest_bid=0
            )

            # 플랫폼 폴백은 예산 예약이 없으므로 순차 실행해도 안전

            for bid in bids:

                try:

                    await reserve_and_insert_bid(
                        auction_id, user_id if user_id else 1, bid
                    )

                except Exception as e:

                    logger.error(
                        "platform_fallback_bid_insert_error",
                        bid_id=bid.id,
                        error=str(e),
                        exc_info=True,
                    )

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
