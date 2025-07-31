from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal
from datetime import datetime, timedelta
import random
import asyncio
from database import (
    database,
    SearchQuery,
    Auction,
    Bid,
    connect_to_database,
    disconnect_from_database,
)

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


# Pydantic 모델
class Bid(BaseModel):
    id: str
    buyerName: str
    price: int
    bonus: str
    timestamp: datetime
    landingUrl: str


class Auction(BaseModel):
    searchId: str
    query: str
    bids: List[Bid]
    status: Literal["active", "completed", "cancelled"]
    createdAt: datetime
    expiresAt: datetime


class StartAuctionRequest(BaseModel):
    query: str
    valueScore: int


class StartAuctionResponse(BaseModel):
    success: bool
    data: Auction
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


# 가상 데이터 수요자 목록
DATA_BUYERS = [
    {
        "id": "buyer_a",
        "name": "A 광고회사",
        "industry": "광고/마케팅",
        "budget": 50000,
        "preferences": ["구매", "가격", "리뷰", "브랜드"],
    },
    {
        "id": "buyer_b",
        "name": "B 마케팅",
        "industry": "디지털마케팅",
        "budget": 30000,
        "preferences": ["트렌드", "소셜", "인플루언서", "콘텐츠"],
    },
    {
        "id": "buyer_c",
        "name": "C 데이터랩",
        "industry": "데이터분석",
        "budget": 40000,
        "preferences": ["통계", "분석", "리서치", "시장조사"],
    },
]

# 메모리 내 경매 저장소 (실제로는 데이터베이스 사용)
# 이제 PostgreSQL에서 데이터를 가져옵니다


def generate_bonus_conditions(buyer: dict, value_score: int) -> str:
    """보너스 조건 생성"""
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


def start_reverse_auction(query: str, value_score: int) -> List[Bid]:
    """가치 점수에 비례하여 가상 입찰 목록을 생성"""
    now = datetime.now()

    # '아이폰16' 특별 케이스 처리
    if "아이폰16" in query.lower() or "iphone16" in query.lower():
        return [
            Bid(
                id="bid-google",
                buyerName="Google",
                price=random.randint(100, 1000),
                bonus="가장 빠른 최신 정보",
                timestamp=now,
                landingUrl=f"https://www.google.com/search?q={query}",
            ),
            Bid(
                id="bid-naver",
                buyerName="네이버",
                price=random.randint(100, 1000),
                bonus="네이버쇼핑 최저가 비교",
                timestamp=now,
                landingUrl=f"https://search.naver.com/search.naver?query={query}",
            ),
            Bid(
                id="bid-coupang",
                buyerName="쿠팡",
                price=random.randint(100, 1000),
                bonus="로켓배송으로 바로 받기",
                timestamp=now,
                landingUrl=f"https://www.coupang.com/np/search?q={query}",
            ),
            Bid(
                id="bid-amazon",
                buyerName="Amazon",
                price=random.randint(100, 1000),
                bonus="해외 직구 & 빠른 배송",
                timestamp=now,
                landingUrl=f"https://www.amazon.com/s?k={query}",
            ),
        ]

    # 기존의 일반 검색어 처리 로직
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
        {"name": query, "url": search_urls["google"], "bonus": "직접 검색 결과"},
    ]

    for i, buyer in enumerate(DATA_BUYERS):
        price = random.randint(100, 1000)
        platform_buyer = platform_buyers[i % len(platform_buyers)]

        bid_id = f"bid_{buyer['id']}_{int(now.timestamp())}_{i}"

        bids.append(
            Bid(
                id=bid_id,
                buyerName=platform_buyer["name"],
                price=price,
                bonus=platform_buyer["bonus"],
                timestamp=now,
                landingUrl=platform_buyer["url"],
            )
        )

    # 가격순으로 정렬 (높은 가격이 먼저)
    return sorted(bids, key=lambda x: x.price, reverse=True)


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
        # 역경매 시작
        bids = start_reverse_auction(request.query, request.valueScore)

        # 경매 정보 생성
        search_id = (
            f"search_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
        )
        now = datetime.now()
        expires_at = now + timedelta(minutes=30)  # 30분 후 만료

        auction = Auction(
            searchId=search_id,
            query=request.query.strip(),
            bids=bids,
            status="active",
            createdAt=now,
            expiresAt=expires_at,
        )

        # 경매 저장
        auctions[search_id] = auction

        return StartAuctionResponse(
            success=True, data=auction, message="역경매가 성공적으로 시작되었습니다."
        )

    except Exception as e:
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

        # 경매 존재 확인
        if request.searchId not in auctions:
            raise HTTPException(status_code=404, detail="경매를 찾을 수 없습니다.")

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
        if search_id not in auctions:
            raise HTTPException(status_code=404, detail="경매를 찾을 수 없습니다.")

        auction = auctions[search_id]
        status_update = await simulate_auction_update(search_id)

        return AuctionStatusResponse(
            success=True,
            data={"auction": auction, "status": status_update},
            message="경매 상태 조회가 완료되었습니다.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "auction-service", "database": "connected"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
