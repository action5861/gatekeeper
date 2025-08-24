from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Dict, Any
from datetime import datetime, timedelta
import random
import asyncio
from decimal import Decimal

# Database import
try:
    from database import (
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


async def find_matching_advertisers(
    search_query: str, quality_score: int
) -> List[Dict[str, Any]]:
    """
    주어진 검색 쿼리 및 품질 점수와 일치하는 광고주를 찾고 매칭 점수를 계산합니다.

    Args:
        search_query (str): 사용자가 입력한 검색 쿼리.
        quality_score (int): 검색 쿼리의 품질 점수.

    Returns:
        List[Dict[str, Any]]: 매칭된 광고주 정보와 점수가 포함된 리스트.
                               (예: [{'advertiser_id': 1, 'match_score': 0.95}, ...])
    """
    # 한글 검색어 처리를 위한 토큰화 개선
    search_tokens = set()

    # 1. 전체 검색어를 하나의 토큰으로 추가
    search_tokens.add(search_query.lower())

    # 2. 공백으로 분리된 토큰들 추가 (영어, 숫자 등)
    search_tokens.update(search_query.lower().split())

    # 3. 한글 검색어의 경우 부분 문자열도 토큰으로 추가 (2글자 이상)
    if any(ord(char) > 127 for char in search_query):  # 한글이 포함된 경우
        for i in range(len(search_query) - 1):
            for j in range(i + 2, len(search_query) + 1):
                token = search_query[i:j].lower()
                if len(token) >= 2:
                    search_tokens.add(token)

    print(f"🔍 검색 토큰: {search_tokens}")
    matched_advertisers = {}

    # --- 매칭 전략 1: 직접 키워드 매칭 (가중치: 1.0) ---
    # 광고주가 등록한 키워드와 검색 쿼리를 비교합니다.
    keyword_match_query = """
        SELECT advertiser_id, keyword, priority, match_type
        FROM advertiser_keywords
        WHERE keyword = ANY(:keywords)
    """
    db_keywords = await database.fetch_all(
        keyword_match_query, values={"keywords": list(search_tokens)}
    )

    for row in db_keywords:
        advertiser_id = row["advertiser_id"]
        if advertiser_id not in matched_advertisers:
            matched_advertisers[advertiser_id] = {"score": 0, "reasons": []}

        # 매치 타입 및 우선순위에 따른 점수 차등 부여
        score_boost = 0
        if row["match_type"] == "exact":
            score_boost = 1.0
        elif row["match_type"] == "phrase":
            score_boost = 0.85
        elif row["match_type"] == "broad":
            score_boost = 0.7

        # 우선순위(1~5)를 가중치로 변환 (5가 가장 높음)
        priority_weight = 1 + (row["priority"] / 10.0)
        final_score = score_boost * priority_weight

        matched_advertisers[advertiser_id]["score"] += final_score
        matched_advertisers[advertiser_id]["reasons"].append(
            f"키워드 매칭: {row['keyword']} ({row['match_type']})"
        )

    # --- 매칭 전략 2: 카테고리 매칭 (가중치: 0.6) ---
    # 검색 쿼리에서 카테고리를 추론하고, 해당 카테고리를 등록한 광고주를 찾습니다.
    # (실제 구현에서는 NLP 모델을 사용하여 카테고리를 추론하는 것이 이상적입니다.)
    # 여기서는 예시로 검색어 토큰이 카테고리명에 포함되는 경우를 확인합니다.

    # 모든 비즈니스 카테고리 정보를 가져옵니다.
    all_categories_query = (
        "SELECT id, name, path, level FROM business_categories WHERE is_active = true"
    )
    all_categories = await database.fetch_all(all_categories_query)

    matched_category_paths = []
    for token in search_tokens:
        for category in all_categories:
            if token in category["name"].lower():
                # 하위 카테고리까지 모두 포함
                path_prefix = category["path"]
                for cat in all_categories:
                    if cat["path"].startswith(path_prefix):
                        matched_category_paths.append(cat["path"])

    if matched_category_paths:
        category_match_query = """
            SELECT advertiser_id, category_path, is_primary
            FROM advertiser_categories
            WHERE category_path = ANY(:paths)
        """
        db_categories = await database.fetch_all(
            category_match_query, values={"paths": list(set(matched_category_paths))}
        )

        for row in db_categories:
            advertiser_id = row["advertiser_id"]
            if advertiser_id not in matched_advertisers:
                matched_advertisers[advertiser_id] = {"score": 0, "reasons": []}

            # 기본 점수에 is_primary 여부로 가중치 추가
            category_score = 0.6 * (1.2 if row["is_primary"] else 1.0)
            matched_advertisers[advertiser_id]["score"] += category_score
            matched_advertisers[advertiser_id]["reasons"].append(
                f"카테고리 매칭: {row['category_path']}"
            )

    # --- 최종 필터링 및 정렬 ---
    # 자동 입찰이 활성화된 광고주만 대상으로 필터링합니다.
    final_advertisers = []
    if matched_advertisers:
        advertiser_ids = list(matched_advertisers.keys())
        auto_bid_settings_query = """
            SELECT advertiser_id, min_quality_score
            FROM auto_bid_settings
            WHERE advertiser_id = ANY(:advertiser_ids) AND is_enabled = true
        """
        enabled_advertisers = await database.fetch_all(
            auto_bid_settings_query, values={"advertiser_ids": advertiser_ids}
        )

        for row in enabled_advertisers:
            # 검색 쿼리의 품질 점수가 광고주 설정 기준 이상인 경우에만 최종 후보에 포함
            if quality_score >= row["min_quality_score"]:
                final_advertisers.append(
                    {
                        "advertiser_id": row["advertiser_id"],
                        "match_score": matched_advertisers[row["advertiser_id"]][
                            "score"
                        ],
                        "reasons": matched_advertisers[row["advertiser_id"]]["reasons"],
                    }
                )

    # 매칭 점수가 높은 순으로 정렬
    return sorted(final_advertisers, key=lambda x: x["match_score"], reverse=True)


# --- 2. 자동 입찰가 계산 알고리즘 ---


async def calculate_auto_bid_price(advertiser_id: int, match_score: float) -> int:
    """
    매칭 점수와 광고주 설정을 기반으로 최적의 입찰가를 동적으로 계산합니다.

    Args:
        advertiser_id (int): 광고주 ID.
        match_score (float): find_matching_advertisers에서 계산된 매칭 점수.

    Returns:
        int: 계산된 최종 입찰가.
    """
    settings_query = """
        SELECT daily_budget, max_bid_per_keyword
        FROM auto_bid_settings
        WHERE advertiser_id = :advertiser_id
    """
    settings = await database.fetch_one(
        settings_query, values={"advertiser_id": advertiser_id}
    )

    if not settings:
        return 0

    # 기본 입찰가 = 최대 입찰가의 (매칭 점수)%
    # 매칭 점수가 1.0이면 최대 입찰가의 100%를, 0.5이면 50%를 기본 입찰가로 설정
    base_bid = int(settings["max_bid_per_keyword"] * min(match_score, 1.0))

    # 광고주 심사 결과에 따른 입찰가 조정 (가산점/감점)
    review_query = """
        SELECT recommended_bid_min, recommended_bid_max
        FROM advertiser_reviews
        WHERE advertiser_id = :advertiser_id AND review_status = 'approved'
    """
    review = await database.fetch_one(
        review_query, values={"advertiser_id": advertiser_id}
    )

    final_bid = base_bid
    if review:
        # 추천 입찰가 범위 내에서 최종 입찰가 조정
        final_bid = max(
            review["recommended_bid_min"], min(final_bid, review["recommended_bid_max"])
        )

    return final_bid


# --- 3. 예산 확인 로직 ---


async def check_budget_availability(advertiser_id: int, bid_amount: int) -> bool:
    """
    광고주의 현재 예산으로 입찰이 가능한지 확인합니다.

    Args:
        advertiser_id (int): 광고주 ID.
        bid_amount (int): 입찰할 금액.

    Returns:
        bool: 입찰 가능 여부.
    """
    # 오늘 하루 동안 해당 광고주가 지출한 총액을 계산
    today_spend_query = """
        SELECT SUM(price) as total_spent
        FROM bids
        WHERE buyer_name = (SELECT company_name FROM advertisers WHERE id = :advertiser_id)
          AND created_at >= current_date
    """
    result = await database.fetch_one(
        today_spend_query, values={"advertiser_id": advertiser_id}
    )
    total_spent_today = result["total_spent"] if result and result["total_spent"] else 0

    # 광고주의 일일 예산 한도를 가져옴
    budget_query = "SELECT daily_budget FROM auto_bid_settings WHERE advertiser_id = :advertiser_id"
    budget_settings = await database.fetch_one(
        budget_query, values={"advertiser_id": advertiser_id}
    )

    if not budget_settings:
        return False

    # (총 지출액 + 이번 입찰금액)이 일일 예산을 초과하는지 확인
    if (total_spent_today + bid_amount) > budget_settings["daily_budget"]:
        print(f"광고주 {advertiser_id}: 일일 예산 초과로 입찰 불가")
        return False

    # TODO: 실제 예치금 잔액 확인 로직 추가
    # 예: payment_service 와의 연동을 통해 실제 출금 가능한 잔액 확인

    return True


# --- 4. 실제 광고주 자동 입찰 생성 ---


async def generate_real_advertiser_bids(
    search_query: str, quality_score: int
) -> List[BidResponse]:
    """
    실제 광고주들의 자동 입찰을 생성합니다.

    Args:
        search_query (str): 검색 쿼리
        quality_score (int): 품질 점수

    Returns:
        List[BidResponse]: 실제 광고주들의 입찰 목록
    """
    print(
        f"--- 검색어 '{search_query}' (품질 점수: {quality_score})에 대한 실제 광고주 매칭 시작 ---"
    )

    # 1. 매칭되는 광고주 찾기
    matching_advertisers = await find_matching_advertisers(search_query, quality_score)

    if not matching_advertisers:
        print(">> 매칭되는 광고주가 없습니다.")
        return []

    print(f">> 총 {len(matching_advertisers)}명의 잠재적 광고주를 찾았습니다.")

    real_bids = []

    # 2. 각 광고주별 입찰가 계산 및 예산 확인
    for advertiser in matching_advertisers:
        advertiser_id = advertiser["advertiser_id"]
        match_score = advertiser["match_score"]

        # 광고주 정보 조회
        advertiser_info_query = """
            SELECT company_name, website_url
            FROM advertisers
            WHERE id = :advertiser_id
        """
        advertiser_info = await database.fetch_one(
            advertiser_info_query, values={"advertiser_id": advertiser_id}
        )

        if not advertiser_info:
            continue

        # 입찰가 계산
        bid_price = await calculate_auto_bid_price(advertiser_id, match_score)

        if bid_price > 0:
            # 예산 확인
            is_available = await check_budget_availability(advertiser_id, bid_price)

            if is_available:
                # 보너스 조건 생성 (타입 변환)
                advertiser_info_dict = dict(advertiser_info)
                bonus_conditions = generate_bonus_conditions_for_advertiser(
                    advertiser_info_dict, match_score, quality_score
                )

                # BidResponse 생성
                import uuid

                bid_id = f"bid_real_{advertiser_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"

                real_bids.append(
                    BidResponse(
                        id=bid_id,
                        buyerName=advertiser_info["company_name"],
                        price=bid_price,
                        bonus=bonus_conditions,
                        timestamp=datetime.now(),
                        landingUrl=advertiser_info["website_url"]
                        or f"https://www.google.com/search?q={search_query}",
                    )
                )

                print(
                    f"  - 광고주 {advertiser_info['company_name']}: 입찰가 {bid_price}원, 매칭 점수 {match_score:.2f}"
                )
            else:
                print(
                    f"  - 광고주 {advertiser_info['company_name']}: 예산 부족으로 입찰 제외"
                )
        else:
            print(
                f"  - 광고주 {advertiser_info['company_name']}: 입찰가 0원으로 입찰 제외"
            )

    # 3. 최종 입찰 결과 정렬
    if real_bids:
        sorted_bids = sorted(real_bids, key=lambda x: x.price, reverse=True)
        print(f"\n--- 최종 입찰 결과: {len(sorted_bids)}개 ---")
        for rank, bid in enumerate(sorted_bids, 1):
            print(f"{rank}위: {bid.buyerName} (입찰가: {bid.price}원)")

        return sorted_bids
    else:
        print("\n>> 최종 입찰자가 없습니다.")
        return []


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
    """실제 광고주 매칭 시스템과 시뮬레이션을 혼합하여 입찰 목록을 생성"""

    # 1. 실제 광고주 매칭 시도
    real_bids = await generate_real_advertiser_bids(query, value_score)

    # 자동 입찰 로그 기록
    await log_auto_bids(real_bids, query, value_score)

    # 2. 실제 광고주가 충분하지 않은 경우 시뮬레이션 보완
    if len(real_bids) < 3:
        simulation_bids = await generate_simulation_bids(
            query, value_score, 3 - len(real_bids)
        )
        real_bids.extend(simulation_bids)

    # 3. 최소 1개는 보장
    if not real_bids:
        fallback_bids = await generate_fallback_bids(query, value_score)
        real_bids.extend(fallback_bids)

    # 가격순으로 정렬 (높은 가격이 먼저)
    return sorted(real_bids, key=lambda x: x.price, reverse=True)


async def generate_simulation_bids(
    query: str, value_score: int, count: int
) -> List[BidResponse]:
    """시뮬레이션 입찰 생성 (실제 광고주 부족 시 보완용)"""
    now = datetime.now()
    bids = []

    # 플랫폼별 검색 URL 생성
    search_urls = {
        "google": f"https://www.google.com/search?q={query}",
        "naver": f"https://search.naver.com/search.naver?query={query}",
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

        bids.append(
            BidResponse(
                id=bid_id,
                buyerName=platform_buyer["name"],
                price=price,
                bonus=platform_buyer["bonus"],
                timestamp=now,
                landingUrl=platform_buyer["url"],
            )
        )

    return bids


async def log_auto_bids(bids: List[BidResponse], query: str, value_score: int):
    """자동 입찰 결과를 로그 테이블에 기록"""
    try:
        for bid in bids:
            # bid.id에서 advertiser_id 추출 시도 (bid_real_123_... 형식)
            advertiser_id = 1  # 기본값
            if bid.id.startswith("bid_real_"):
                try:
                    # bid_real_123_timestamp_uuid 형식에서 123 추출
                    parts = bid.id.split("_")
                    if len(parts) >= 3:
                        advertiser_id = int(parts[2])
                except (ValueError, IndexError):
                    advertiser_id = 1  # 파싱 실패 시 기본값

            # auto_bid_logs 테이블에 기록
            await database.execute(
                """
                INSERT INTO auto_bid_logs (
                    advertiser_id, search_query, match_type, match_score, 
                    bid_amount, bid_result, quality_score, competitor_count, created_at
                ) VALUES (
                    :advertiser_id, :search_query, :match_type, :match_score,
                    :bid_amount, :bid_result, :quality_score, :competitor_count, :created_at
                )
                """,
                {
                    "advertiser_id": advertiser_id,
                    "search_query": query,
                    "match_type": "broad",  # 기본값
                    "match_score": 0.7,  # 기본값
                    "bid_amount": bid.price,
                    "bid_result": (
                        "won" if bid.price > 500 else "lost"
                    ),  # 시뮬레이션 결과
                    "quality_score": value_score,
                    "competitor_count": len(bids),
                    "created_at": bid.timestamp,
                },
            )

        print(f"✅ Auto bid logs recorded for {len(bids)} bids")

    except Exception as e:
        print(f"❌ Error logging auto bids: {e}")
        # 로깅 실패는 전체 시스템에 영향을 주지 않도록 함


async def generate_fallback_bids(query: str, value_score: int) -> List[BidResponse]:
    """최소 보장용 폴백 입찰 생성"""
    now = datetime.now()

    import uuid

    bid_id = f"bid_fallback_{int(now.timestamp())}_{uuid.uuid4().hex[:8]}"

    return [
        BidResponse(
            id=bid_id,
            buyerName="Google",
            price=random.randint(100, 500),
            bonus="기본 검색 결과",
            timestamp=now,
            landingUrl=f"https://www.google.com/search?q={query}",
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
            bid_query = """
                INSERT INTO bids (id, auction_id, buyer_name, price, bonus_description, landing_url)
                VALUES (:id, :auction_id, :buyer_name, :price, :bonus_description, :landing_url)
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
