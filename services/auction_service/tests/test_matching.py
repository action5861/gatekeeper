import os
import pytest
from datetime import datetime

# 테스트 대상 모듈/함수
import services.auction_service.main as m
from services.auction_service.main import BidResponse


@pytest.mark.asyncio
async def test_generate_real_advertiser_bids_no_db(monkeypatch):
    """
    DB 없이 generate_real_advertiser_bids가 정상적으로 BidResponse를 생성하는지 검증.
    - find_matching_advertisers: 매칭 결과 더미 주입
    - database.fetch_all: 광고주 상세정보 더미 주입
    - check_budget_availability: 항상 True
    - sign_click: 고정 서명값
    - 환경변수 REDIRECT_BASE_URL 확인
    """
    # 1) 매칭 결과 더미
    fake_matches = [
        {
            "advertiser_id": 101,
            "match_score": 0.92,
            "reasons": ["KW_EXACT:테스트키워드"],
        },
        {"advertiser_id": 202, "match_score": 0.81, "reasons": ["CAT:/쇼핑/항공권"]},
    ]

    async def fake_find_matching_advertisers(q, qs):
        return fake_matches

    monkeypatch.setattr(m, "find_matching_advertisers", fake_find_matching_advertisers)

    # 2) 광고주 상세정보 더미 (details_query 결과)
    class Row(dict):
        # dict로 충분하지만, m.database.fetch_all이 dict-like만 기대하므로 간단 구현
        pass

    async def fake_fetch_all(query, values=None):
        ids = values.get("ids", []) if values else []
        rows = []
        for adv_id in ids:
            rows.append(
                Row(
                    {
                        "advertiser_id": adv_id,
                        "company_name": f"Advertiser-{adv_id}",
                        "website_url": f"https://adv{adv_id}.example.com",
                        "daily_budget": 100000,
                        "max_bid_per_keyword": 3000,
                        "recommended_bid_min": 500,
                        "recommended_bid_max": 2500,
                    }
                )
            )
        return rows

    monkeypatch.setattr(m.database, "fetch_all", fake_fetch_all)

    # 3) 예산 확인 통과
    async def fake_check_budget(advertiser_id: int, bid_amount: int) -> bool:
        return True

    monkeypatch.setattr(m, "check_budget_availability", fake_check_budget)

    # 4) 서명 고정
    def fake_sign_click(bid_id, price, bid_type):
        return "TESTSIG"

    monkeypatch.setattr(m, "sign_click", fake_sign_click)

    # 5) 리다이렉트 베이스 URL 주입
    os.environ["REDIRECT_BASE_URL"] = "http://api-gateway:8000"
    # main 모듈 내 상수 갱신
    m.REDIRECT_BASE_URL = os.getenv("REDIRECT_BASE_URL", "http://api-gateway:8000")

    # 실행
    bids = await m.generate_real_advertiser_bids("제주도 항공권", 80)

    # 검증
    assert isinstance(bids, list) and len(bids) == 2
    for b in bids:
        assert isinstance(b, BidResponse)
        assert b.buyerName.startswith("Advertiser-")
        assert b.price >= 500 and b.price <= 2500  # 추천 범위 내에서 클램핑
        assert isinstance(b.timestamp, datetime)
        assert b.landingUrl.startswith("https://adv")
        assert b.clickUrl.startswith(os.environ["REDIRECT_BASE_URL"])
        assert hasattr(b, "reasons")
        assert isinstance(b.reasons, list) and len(b.reasons) >= 1
        # 선택 필드가 있다면 타입 체크
        if hasattr(b, "matchScore") and b.matchScore is not None:
            assert isinstance(b.matchScore, float)
        if hasattr(b, "advertiserId") and b.advertiserId is not None:
            assert isinstance(b.advertiserId, int)

    # 가격 내림차순 정렬 여부(기본 로직) 간단 확인
    prices = [b.price for b in bids]
    assert prices == sorted(prices, reverse=True)
