from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Dict, Any
from datetime import datetime, timedelta
import random
import asyncio
from decimal import Decimal
import os
import json

# HMAC 서명 import
from .utils.sign import sign_click

REDIRECT_BASE_URL = os.getenv("REDIRECT_BASE_URL", "http://api-gateway:8000")

# 최적화된 매칭 로직 import
from .optimized_matching import OptimizedAdvertiserMatcher, OptimizedBidGenerator

# Database import
try:
    from .database import (
        database,
        SearchQuery,
        connect_to_database,
        disconnect_from_database,
    )

    print("✅ Database models imported successfully")
except ImportError as e:
    print(f"❌ Database import failed: {e}")
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
        print("✅ Auction Service database connected successfully!")

    async def disconnect_from_database():
        await database.disconnect()
        print("Auction Service database disconnected")


# === Tokenization & normalization utilities ===
def _normalize(s: str) -> str:
    """문자열을 소문자로 변환하고 모든 공백을 제거합니다."""
    return "".join(s.lower().split())


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


app = FastAPI(title="Auction Service", version="1.0.0")


# 🚀 시작 이벤트
@app.on_event("startup")
async def startup():
    await connect_to_database()


# 🛑 종료 이벤트
@app.on_event("shutdown")
async def shutdown():
    await disconnect_from_database()


# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
          SELECT 1 FROM unnest(:tokens_norm) t(tok)
          WHERE lower(replace(keyword, ' ', '')) LIKE '%' || tok || '%'
             OR tok LIKE '%' || lower(replace(keyword, ' ', '')) || '%'
     )
  )
"""

BROAD_SQL = """
SELECT advertiser_id, keyword, priority, match_type
FROM advertiser_keywords
WHERE match_type = 'broad'
  AND EXISTS (
      SELECT 1 FROM unnest(:tokens_like) t(tok)
      WHERE lower(keyword) LIKE t.tok
  )
"""

CATEGORY_SQL = """
WITH matched_categories AS (
    SELECT DISTINCT path
    FROM business_categories
    WHERE is_active = true
      AND EXISTS (
          SELECT 1 FROM unnest(:tokens_like) t(tok)
          WHERE lower(name) LIKE t.tok
      )
)
SELECT ac.advertiser_id, ac.category_path, ac.is_primary
FROM advertiser_categories ac
JOIN matched_categories mc ON ac.category_path LIKE mc.path || '%'
"""

SCORES = {"exact": 1.0, "phrase": 0.85, "broad": 0.7}
SCORE_CAP = 3.0  # 최대 점수 상한


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

    aggregator: Dict[int, Dict[str, Any]] = {}

    # 1) 키워드 매칭 3종 병렬 실행
    exact_rows, phrase_rows, broad_rows = await asyncio.gather(
        database.fetch_all(EXACT_SQL, {"tokens_norm": tokens_norm}),
        database.fetch_all(PHRASE_SQL, {"tokens_norm": tokens_norm}),
        database.fetch_all(BROAD_SQL, {"tokens_like": tokens_like}),
    )
    for rows in (exact_rows, phrase_rows, broad_rows):
        for r in rows:
            _add_keyword_score(
                aggregator,
                r["advertiser_id"],
                r["match_type"],
                r["priority"],
                r["keyword"],
            )

    # 2) 카테고리 매칭
    if tokens_like:
        rows_cat = await database.fetch_all(CATEGORY_SQL, {"tokens_like": tokens_like})
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
    abs_query = """
        SELECT advertiser_id, min_quality_score
        FROM auto_bid_settings
        WHERE advertiser_id = ANY(:ids) AND is_enabled = true
    """
    abs_rows = await database.fetch_all(abs_query, {"ids": advertiser_ids})
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


async def check_budget_availability(advertiser_id: int, bid_amount: int) -> bool:
    """
    광고주의 현재 예산으로 입찰 가능 여부 확인 (KST 자정 기준)
    """
    spend_query = """
        SELECT COALESCE(SUM(price), 0) AS total_spent
        FROM bids
        WHERE advertiser_id = :advertiser_id
          AND created_at >= (date_trunc('day', timezone('Asia/Seoul', now())) AT TIME ZONE 'Asia/Seoul')
    """
    result = await database.fetch_one(spend_query, {"advertiser_id": advertiser_id})
    total_spent_today = result["total_spent"] if result else 0

    budget_query = "SELECT daily_budget FROM auto_bid_settings WHERE advertiser_id = :advertiser_id"
    budget_settings = await database.fetch_one(
        budget_query, {"advertiser_id": advertiser_id}
    )
    if not budget_settings:
        return False

    return (total_spent_today + bid_amount) <= budget_settings["daily_budget"]


# --- 4. 실제 광고주 자동 입찰 생성 ---


async def generate_real_advertiser_bids(
    search_query: str, quality_score: int
) -> List[BidResponse]:
    """
    실제 광고주 자동 입찰 생성 (N+1 제거, 점수/사유 전달)
    """
    print(f"--- 검색어 '{search_query}' (품질 점수: {quality_score}) 매칭 시작 ---")

    matching_advertisers = await find_matching_advertisers(search_query, quality_score)
    if not matching_advertisers:
        print(">> 매칭 광고주 없음 → 플랫폼 폴백 반환")
        return generate_platform_fallback_bids(search_query, quality_score)

    advertiser_ids = [m["advertiser_id"] for m in matching_advertisers]
    details_query = """
        SELECT 
            a.id as advertiser_id, a.company_name, a.website_url,
            abs.daily_budget, abs.max_bid_per_keyword,
            ar.recommended_bid_min, ar.recommended_bid_max
        FROM advertisers a
        LEFT JOIN auto_bid_settings abs ON a.id = abs.advertiser_id
        LEFT JOIN advertiser_reviews ar ON a.id = ar.advertiser_id AND ar.review_status = 'approved'
        WHERE a.id = ANY(:ids) AND abs.is_enabled = true
    """
    rows = await database.fetch_all(details_query, {"ids": advertiser_ids})
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

        if not await check_budget_availability(adv_id, bid_price):
            print(f"   - 광고주 {adv_id}: 예산 부족")
            continue

        import uuid

        bid_id = f"bid_real_{adv_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
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
                timestamp=datetime.now(),
                landingUrl=info["website_url"]
                or f"https://www.google.com/search?q={search_query}",
                clickUrl=click_url,
                reasons=reasons,
                matchScore=match_score,
                advertiserId=adv_id,
            )
        )
        print(
            f"   - 광고주 {info['company_name']}: {bid_price}원 (점수 {match_score:.2f})"
        )

    if not real_bids:
        print(">> 유효 입찰자 없음 → 플랫폼 폴백")
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
    print(">> 플랫폼 사업자 고정 적립 입찰 생성 중...")

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
    now = datetime.now()

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
                buyerName=buyer["name"],
                price=200,  # 고정 200원 적립
                bonus=buyer["bonus"],
                timestamp=now,
                landingUrl=buyer["url"],
                clickUrl=click_url,
            )
        )

    print(f">> {len(fallback_bids)}개의 플랫폼 사업자 고정 적립 입찰 생성 완료")
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
    print(f">> 역경매 시작 - 검색어: {query}, 품질점수: {value_score}")

    # 실제 광고주 매칭 시도
    bids = await generate_real_advertiser_bids(query, value_score)

    # 혹시 모를 상황에 대비한 안전장치
    if not bids:
        print(">> 오류: 입찰 결과가 없습니다. 강제로 플랫폼 폴백 생성")
        bids = generate_platform_fallback_bids(query, value_score)

    # 자동 입찰 결과 DB에 기록
    await log_auto_bids(bids, query, value_score)

    print(f">> 최종 반환: {len(bids)}개 입찰")
    for i, bid in enumerate(bids):
        print(f"   {i+1}. {bid.buyerName}: {bid.price}원")

    return bids


async def generate_simulation_bids(
    query: str, value_score: int, count: int
) -> List[BidResponse]:
    """시뮬레이션 입찰 생성 (실제 광고주 부족 시 보완용)"""
    now = datetime.now()
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


async def log_auto_bids(bids: List[BidResponse], query: str, value_score: int):
    """자동 입찰 결과를 로그 테이블에 기록 (reasons JSONB / matchScore 반영)"""
    try:
        for bid in bids:
            advertiser_id = bid.advertiserId or (
                0 if bid.id.startswith("platform_bid_") else None
            )
            match_score = bid.matchScore or 0.0
            reasons_json = json.dumps(bid.reasons or [])

            await database.execute(
                """
                INSERT INTO auto_bid_logs (
                    advertiser_id, search_query, match_type, match_score, 
                    bid_amount, bid_result, quality_score, competitor_count, created_at, reasons
                ) VALUES (
                    :advertiser_id, :search_query, :match_type, :match_score,
                    :bid_amount, :bid_result, :quality_score, :competitor_count, :created_at, :reasons::jsonb
                )
                """,
                {
                    "advertiser_id": advertiser_id,
                    "search_query": query,
                    "match_type": "complex",
                    "match_score": match_score,
                    "bid_amount": bid.price,
                    "bid_result": ("won" if bid.price > 500 else "lost"),
                    "quality_score": value_score,
                    "competitor_count": len(bids),
                    "created_at": bid.timestamp,
                    "reasons": reasons_json,
                },
            )
        print(f"✅ Auto bid logs recorded for {len(bids)} bids")
    except Exception as e:
        print(f"❌ Error logging auto bids: {e}")


async def generate_fallback_bids(query: str, value_score: int) -> List[BidResponse]:
    """최소 보장용 폴백 입찰 생성"""
    now = datetime.now()

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
async def start_auction(request: StartAuctionRequest):
    """역경매를 시작합니다."""
    try:
        # 한글 검색어 디버깅
        print(f"🔍 받은 검색어: '{request.query}' (길이: {len(request.query)})")
        print(f"🔍 검색어 바이트: {request.query.encode('utf-8')}")
        print(f"🔍 검색어 유니코드: {[ord(c) for c in request.query]}")

        # 역경매 시작 (실제 광고주 매칭 시스템 사용)
        bids = await start_reverse_auction(request.query, request.valueScore)

        # 경매 정보 생성
        search_id = (
            f"search_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
        )
        now = datetime.now()
        expires_at = now + timedelta(minutes=30)  # 30분 후 만료

        # 경매 정보를 DB에 저장
        auction_query = """
            INSERT INTO auctions (search_id, query_text, user_id, status, expires_at)
            VALUES (:search_id, :query_text, :user_id, :status, :expires_at)
            RETURNING id
        """

        try:
            auction_result = await database.fetch_one(
                auction_query,
                {
                    "search_id": search_id,
                    "query_text": request.query.strip(),
                    "user_id": 1,  # 하드코딩된 user_id
                    "status": "active",
                    "expires_at": expires_at,
                },
            )
        except Exception as db_error:
            print(f"❌ Database error in auction creation: {str(db_error)}")
            raise HTTPException(
                status_code=500, detail=f"데이터베이스 오류: {str(db_error)}"
            )

        if not auction_result:
            raise HTTPException(status_code=500, detail="경매 생성에 실패했습니다.")

        auction_id = auction_result["id"]

        # 입찰 정보를 DB에 저장
        for bid in bids:
            # bid_id에서 타입 추출
            bid_type = (
                "PLATFORM" if bid.id.startswith("platform_bid_") else "ADVERTISER"
            )

            # 광고주 ID 조회 (ADVERTISER 타입인 경우)
            advertiser_id = None
            if bid_type == "ADVERTISER":
                try:
                    # bid_id에서 광고주 ID 추출 시도
                    if bid.id.startswith("bid_real_"):
                        parts = bid.id.split("_")
                        if len(parts) >= 3:
                            advertiser_id = int(parts[2])
                except (ValueError, IndexError):
                    # buyer_name으로 광고주 ID 조회
                    try:
                        advertiser_result = await database.fetch_one(
                            "SELECT id FROM advertisers WHERE company_name = :company_name",
                            {"company_name": bid.buyerName},
                        )
                        if advertiser_result:
                            advertiser_id = advertiser_result["id"]
                    except Exception:
                        advertiser_id = None

            bid_query = """
                INSERT INTO bids (id, auction_id, buyer_name, price, bonus_description, landing_url, type, user_id, dest_url, advertiser_id)
                VALUES (:id, :auction_id, :buyer_name, :price, :bonus_description, :landing_url, :type, :user_id, :dest_url, :advertiser_id)
            """

            await database.execute(
                bid_query,
                {
                    "id": bid.id,
                    "auction_id": auction_id,
                    "buyer_name": bid.buyerName,
                    "price": bid.price,
                    "bonus_description": bid.bonus,
                    "landing_url": bid.landingUrl,
                    "type": bid_type,
                    "user_id": 1,  # 하드코딩된 user_id (실제로는 JWT에서 추출)
                    "dest_url": bid.landingUrl,
                    "advertiser_id": advertiser_id,
                },
            )

        auction = AuctionResponse(
            searchId=search_id,
            query=request.query.strip(),
            bids=bids,
            status="active",
            createdAt=now,
            expiresAt=expires_at,
        )

        return StartAuctionResponse(
            success=True, data=auction, message="역경매가 성공적으로 시작되었습니다."
        )

    except Exception as e:
        print(f"❌ Auction service error: {str(e)}")
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

        return {
            "id": bid["id"],
            "auction_id": bid["auction_id"],
            "buyer_name": bid["buyer_name"],
            "price": bid["price"],
            "bonus_description": bid["bonus_description"],
            "landing_url": bid["landing_url"],
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
                    "timestamp": datetime.now().isoformat(),
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
    """실제 광고주 매칭 시스템 상태 확인"""
    try:
        # 실제 광고주 수 확인
        advertiser_count_query = """
            SELECT COUNT(*) as count
            FROM advertisers a
            JOIN auto_bid_settings abs ON a.id = abs.advertiser_id
            WHERE abs.is_enabled = true
        """
        advertiser_count = await database.fetch_one(advertiser_count_query)

        # 승인된 광고주 수 확인
        approved_count_query = """
            SELECT COUNT(*) as count
            FROM advertisers a
            JOIN advertiser_reviews ar ON a.id = ar.advertiser_id
            JOIN auto_bid_settings abs ON a.id = abs.advertiser_id
            WHERE ar.review_status = 'approved' AND abs.is_enabled = true
        """
        approved_count = await database.fetch_one(approved_count_query)

        # 등록된 키워드 수 확인
        keyword_count_query = "SELECT COUNT(*) as count FROM advertiser_keywords"
        keyword_count = await database.fetch_one(keyword_count_query)

        # 등록된 카테고리 수 확인
        category_count_query = "SELECT COUNT(*) as count FROM advertiser_categories"
        category_count = await database.fetch_one(category_count_query)

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
            "features": {
                "real_advertiser_matching": True,
                "auto_bid_calculation": True,
                "budget_management": True,
                "category_matching": True,
                "simulation_fallback": True,
            },
        }
    except Exception as e:
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
