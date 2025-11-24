"""
auction_service의 핵심 기능에 대한 포괄적인 pytest 테스트 스위트
- 유틸리티 함수 단위 테스트
- 트랜잭션 로직 단위 테스트
- API 엔드포인트 통합 테스트
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, ANY
from datetime import datetime, timezone

# main.py에서 필요한 함수들 임포트
from services.auction_service.main import (
    _validate_url,
    get_user_id_from_token,
    _reserve_budget_tx,
    reserve_and_insert_bid,
    BidResponse,
    StartAuctionRequest,
    security,
)


# ========================================
# 1단계: 핵심 유틸리티 함수 단위 테스트
# ========================================

@pytest.mark.parametrize("url, expected", [
    ("https://good.com", "https://good.com"),
    ("http://bad.com", None),  # HTTP는 거부
    ("javascript:alert(1)", None),  # XSS 방지
    ("ftp://files.com", None),
    ("not-a-url", None),
    (None, None),
    ("https://example.com/path?query=test", "https://example.com/path?query=test"),
])
def test_validate_url(url, expected):
    """URL 유효성 검사 테스트"""
    assert _validate_url(url) == expected


@pytest.mark.asyncio
async def test_get_user_id_from_token_success(mocker):
    """JWT 인증 함수 테스트 (성공 케이스)"""
    # Mock credentials
    mock_credentials = MagicMock()
    mock_credentials.credentials = "valid.token.here"
    
    # Mock JWT decode payload
    mock_payload = {"sub": "test@example.com"}
    mocker.patch("services.auction_service.main.jwt.decode", return_value=mock_payload)
    
    # Mock database fetch_one
    mock_user = {"id": 123}
    mocker.patch("services.auction_service.main.database.fetch_one", new_callable=AsyncMock, return_value=mock_user)
    
    user_id = await get_user_id_from_token(credentials=mock_credentials)
    
    assert user_id == 123
    # mocker가 patch한 것을 다시 import해서 사용하므로 직접 assert는 건너뜀


@pytest.mark.asyncio
async def test_get_user_id_from_token_invalid_jwt(mocker):
    """JWT 인증 함수 테스트 (유효하지 않은 토큰)"""
    from jwt import PyJWTError
    
    mock_credentials = MagicMock()
    mock_credentials.credentials = "invalid.token"
    
    mocker.patch(
        "services.auction_service.main.jwt.decode",
        side_effect=PyJWTError("Invalid token")
    )
    
    user_id = await get_user_id_from_token(credentials=mock_credentials)
    assert user_id is None


@pytest.mark.asyncio
async def test_get_user_id_from_token_user_not_found(mocker):
    """JWT 인증 함수 테스트 (존재하지 않는 유저)"""
    mock_credentials = MagicMock()
    mock_credentials.credentials = "valid.token"
    
    mock_payload = {"sub": "ghost@example.com"}
    mocker.patch("services.auction_service.main.jwt.decode", return_value=mock_payload)
    mocker.patch("services.auction_service.main.database.fetch_one", new_callable=AsyncMock, return_value=None)
    
    user_id = await get_user_id_from_token(credentials=mock_credentials)
    assert user_id is None


@pytest.mark.asyncio
async def test_get_user_id_from_token_no_credentials():
    """JWT 인증 함수 테스트 (자격증명 없음)"""
    user_id = await get_user_id_from_token(credentials=None)
    assert user_id is None


# ========================================
# 2단계: 트랜잭션 로직 단위 테스트 (중요)
# ========================================

@pytest.mark.asyncio
async def test_reserve_budget_tx_success(mocker):
    """예산이 충분할 때 성공"""
    # Mock DB calls
    mock_execute = AsyncMock()
    mocker.patch("services.auction_service.main.database.fetch_one", new_callable=AsyncMock, side_effect=[
        {"amount": 10000},  # 현재 지출액
        {"daily_budget": 50000}  # 일일 예산
    ])
    mocker.patch("services.auction_service.main.database.execute", new=mock_execute)
    
    bid_amount = 5000
    result = await _reserve_budget_tx(advertiser_id=1, bid_amount=bid_amount)
    
    assert result is True
    # UPDATE 쿼리가 호출되었는지 확인
    assert mock_execute.called


@pytest.mark.asyncio
async def test_reserve_budget_tx_fail_insufficient(mocker):
    """예산이 부족할 때 실패"""
    mock_execute = AsyncMock()
    mocker.patch("services.auction_service.main.database.fetch_one", new_callable=AsyncMock, side_effect=[
        {"amount": 48000},  # 현재 지출액
        {"daily_budget": 50000}  # 일일 예산
    ])
    mocker.patch("services.auction_service.main.database.execute", new=mock_execute)
    
    bid_amount = 3000  # 48000 + 3000 > 50000
    result = await _reserve_budget_tx(advertiser_id=1, bid_amount=bid_amount)
    
    assert result is False
    # UPDATE 쿼리가 호출되지 않았는지 확인
    assert not mock_execute.called


@pytest.mark.asyncio
async def test_reserve_budget_tx_new_advertiser(mocker):
    """당일 첫 지출이라 레코드가 없을 때 (INSERT + UPDATE)"""
    mock_execute = AsyncMock()
    mocker.patch("services.auction_service.main.database.fetch_one", new_callable=AsyncMock, side_effect=[
        None,  # 1. 첫 SELECT (FOR UPDATE) -> 없음
        {"amount": 0},  # 2. 두 번째 SELECT (FOR UPDATE) -> 0
        {"daily_budget": 50000}  # 3. 예산 조회
    ])
    mocker.patch("services.auction_service.main.database.execute", new=mock_execute)
    
    bid_amount = 5000
    result = await _reserve_budget_tx(advertiser_id=2, bid_amount=bid_amount)
    
    assert result is True
    # 1. INSERT, 2. UPDATE 총 2번 호출
    assert mock_execute.call_count == 2


@pytest.mark.asyncio
async def test_reserve_budget_tx_no_budget_setting(mocker):
    """예산 설정이 없을 때 실패"""
    mocker.patch("services.auction_service.main.database.fetch_one", new_callable=AsyncMock, side_effect=[
        {"amount": 10000},
        None  # 예산 설정 없음
    ])
    
    bid_amount = 5000
    result = await _reserve_budget_tx(advertiser_id=1, bid_amount=bid_amount)
    
    assert result is False


@pytest.mark.asyncio
async def test_reserve_and_insert_bid_success(mocker):
    """예산 예약과 bid 저장 성공"""
    # database.transaction을 AsyncContextManager로 모킹
    mock_transaction = AsyncMock()
    mock_transaction.__aenter__ = AsyncMock()
    mock_transaction.__aexit__ = AsyncMock(return_value=False)
    
    mocker.patch("services.auction_service.main.database.transaction", return_value=mock_transaction)
    mocker.patch("services.auction_service.main._reserve_budget_tx", return_value=True)
    mocker.patch("services.auction_service.main.database.execute", new_callable=AsyncMock)
    
    bid = BidResponse(
        id="bid_real_1_123456",
        buyerName="Test Ad",
        price=1000,
        bonus="Test Bonus",
        timestamp=datetime.now(timezone.utc),
        landingUrl="https://good.com",
        clickUrl="http://signed.url",
        advertiserId=1
    )
    
    result = await reserve_and_insert_bid(auction_id=100, user_id=123, bid=bid)
    
    assert result is True


@pytest.mark.asyncio
async def test_reserve_and_insert_bid_budget_fail(mocker):
    """예산 부족으로 실패"""
    mock_transaction = AsyncMock()
    mock_transaction.__aenter__ = AsyncMock()
    mock_transaction.__aexit__ = AsyncMock(return_value=False)
    
    mocker.patch("services.auction_service.main.database.transaction", return_value=mock_transaction)
    mocker.patch("services.auction_service.main._reserve_budget_tx", return_value=False)
    mocker.patch("services.auction_service.main.database.execute", new_callable=AsyncMock)
    
    bid = BidResponse(
        id="bid_real_1_123456",
        buyerName="Test Ad",
        price=1000,
        bonus="Test Bonus",
        timestamp=datetime.now(timezone.utc),
        landingUrl="https://good.com",
        clickUrl="http://signed.url",
        advertiserId=1
    )
    
    result = await reserve_and_insert_bid(auction_id=100, user_id=123, bid=bid)
    
    assert result is False


@pytest.mark.asyncio
async def test_reserve_and_insert_bid_platform_bid(mocker):
    """플랫폼 입찰은 예산 검사 스킵"""
    mock_transaction = AsyncMock()
    mock_transaction.__aenter__ = AsyncMock()
    mock_transaction.__aexit__ = AsyncMock(return_value=False)
    
    mock_reserve_budget = AsyncMock()
    mocker.patch("services.auction_service.main.database.transaction", return_value=mock_transaction)
    mocker.patch("services.auction_service.main._reserve_budget_tx", new=mock_reserve_budget)
    mocker.patch("services.auction_service.main.database.execute", new_callable=AsyncMock)
    
    bid = BidResponse(
        id="platform_bid_coupang_123",
        buyerName="Coupang",
        price=200,
        bonus="로켓배송",
        timestamp=datetime.now(timezone.utc),
        landingUrl="https://coupang.com",
        clickUrl="http://signed.url",
        advertiserId=None
    )
    
    result = await reserve_and_insert_bid(auction_id=100, user_id=123, bid=bid)
    
    assert result is True
    # _reserve_budget_tx가 호출되지 않았는지 확인
    assert not mock_reserve_budget.called


# ========================================
# 3단계: API 엔드포인트 통합 테스트
# ========================================

@pytest.mark.asyncio
async def test_start_auction_happy_path(client, mocker):
    """/start API 테스트 (Happy Path)"""
    # Mock dependencies
    mocker.patch("services.auction_service.main.get_user_id_from_token", return_value=123)
    mocker.patch("services.auction_service.main.check_rate_limit", return_value=True)
    
    # Mock start_reverse_auction
    mock_bid = BidResponse(
        id="bid_real_1_123456",
        buyerName="Test Ad",
        price=1000,
        bonus="Test Bonus",
        timestamp=datetime.now(timezone.utc),
        landingUrl="https://good.com",
        clickUrl="http://signed.url",
        advertiserId=1
    )
    mocker.patch("services.auction_service.main.start_reverse_auction", return_value=[mock_bid])
    
    # Mock auctions INSERT
    mocker.patch("services.auction_service.main.database.fetch_one", new_callable=AsyncMock, side_effect=[
        {"id": 99}  # 새 auction ID
    ])
    
    # Mock reserve_and_insert_bid
    mocker.patch("services.auction_service.main.reserve_and_insert_bid", return_value=True)
    mocker.patch("services.auction_service.main.log_auto_bids", new_callable=AsyncMock)
    
    # API Call
    response = await client.post(
        "/start",
        json={"query": "test query", "valueScore": 80}
    )
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["query"] == "test query"
    assert len(data["data"]["bids"]) == 1
    assert data["data"]["bids"][0]["id"] == "bid_real_1_123456"


@pytest.mark.asyncio
async def test_start_auction_rate_limit(client, mocker):
    """/start API 테스트 (Rate Limit)"""
    mocker.patch("services.auction_service.main.check_rate_limit", return_value=False)
    
    response = await client.post(
        "/start",
        json={"query": "test query", "valueScore": 80}
    )
    
    assert response.status_code == 429


@pytest.mark.asyncio
async def test_start_auction_all_bids_fail_fallback(client, mocker):
    """예산 부족으로 모든 입찰 실패 시 폴백"""
    mocker.patch("services.auction_service.main.get_user_id_from_token", return_value=123)
    mocker.patch("services.auction_service.main.check_rate_limit", return_value=True)
    
    # Mock start_reverse_auction - real bid
    mock_real_bid = BidResponse(
        id="bid_real_1_123456",
        buyerName="Test Ad",
        price=1000,
        bonus="Test Bonus",
        timestamp=datetime.now(timezone.utc),
        landingUrl="https://good.com",
        clickUrl="http://signed.url",
        advertiserId=1
    )
    mocker.patch("services.auction_service.main.start_reverse_auction", return_value=[mock_real_bid])
    
    # Mock auctions INSERT
    mocker.patch("services.auction_service.main.database.fetch_one", new_callable=AsyncMock, side_effect=[
        {"id": 100}
    ])
    
    # Mock reserve_and_insert_bid - 첫 번째는 실패, generate_platform_fallback_bids가 호출되면 성공
    reserve_mock = mocker.patch("services.auction_service.main.reserve_and_insert_bid")
    reserve_mock.side_effect = [False, True]  # real bid 실패, platform bid 성공
    
    # Mock generate_platform_fallback_bids
    mock_platform_bid = BidResponse(
        id="platform_bid_coupang_123",
        buyerName="쿠팡",
        price=200,
        bonus="로켓배송",
        timestamp=datetime.now(timezone.utc),
        landingUrl="https://coupang.com",
        clickUrl="http://signed.url",
        advertiserId=None
    )
    mock_fallback_gen = mocker.patch(
        "services.auction_service.main.generate_platform_fallback_bids",
        return_value=[mock_platform_bid]
    )
    mocker.patch("services.auction_service.main.log_auto_bids", new_callable=AsyncMock)
    
    # API Call
    response = await client.post(
        "/start",
        json={"query": "all fail", "valueScore": 80}
    )
    
    assert response.status_code == 200
    # generate_platform_fallback_bids가 호출되었는지 확인
    mock_fallback_gen.assert_called_once()


@pytest.mark.asyncio
async def test_select_bid_success(client, mocker):
    """/select API 테스트 (성공)"""
    # Mock auction 조회
    mocker.patch("services.auction_service.main.database.fetch_one", new_callable=AsyncMock, side_effect=[
        {"id": 1, "search_id": "search_123", "status": "active"}
    ])
    mocker.patch("services.auction_service.main.database.execute", new_callable=AsyncMock)
    mocker.patch("services.auction_service.main.simulate_real_time_delay", new_callable=AsyncMock)
    
    response = await client.post(
        "/select",
        json={
            "searchId": "search_123",
            "selectedBidId": "bid_456"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "rewardAmount" in data["data"]


@pytest.mark.asyncio
async def test_select_bid_not_found(client, mocker):
    """/select API 테스트 (경매 없음)"""
    mocker.patch("services.auction_service.main.database.fetch_one", new_callable=AsyncMock, return_value=None)
    
    response = await client.post(
        "/select",
        json={
            "searchId": "invalid_search_id",
            "selectedBidId": "bid_456"
        }
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_select_bid_invalid_request(client):
    """/select API 테스트 (잘못된 요청)"""
    response = await client.post(
        "/select",
        json={
            "searchId": "",
            "selectedBidId": ""
        }
    )
    
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_auction_status_success(client, mocker):
    """/status/{search_id} API 테스트 (성공)"""
    # Mock auction과 bids 조회
    mocker.patch("services.auction_service.main.database.fetch_one", new_callable=AsyncMock, side_effect=[
        {"id": 1, "search_id": "search_123", "status": "active"}
    ])
    mocker.patch("services.auction_service.main.database.fetch_all", new_callable=AsyncMock, return_value=[
        {"id": "bid_1", "auction_id": 1, "price": 1000},
        {"id": "bid_2", "auction_id": 1, "price": 2000}
    ])
    mocker.patch("services.auction_service.main.simulate_auction_update", new_callable=AsyncMock, return_value={"status": "active", "participants": 2})
    
    response = await client.get("/status/search_123")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["bids"]) == 2


@pytest.mark.asyncio
async def test_get_auction_status_not_found(client, mocker):
    """/status/{search_id} API 테스트 (경매 없음)"""
    mocker.patch("services.auction_service.main.database.fetch_one", new_callable=AsyncMock, return_value=None)
    
    response = await client.get("/status/invalid_search_id")
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_health_check(client):
    """/health API 테스트"""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "auction-service"


@pytest.mark.asyncio
async def test_get_bid_info_success(client, mocker):
    """/bid/{bid_id} API 테스트 (성공)"""
    mock_bid = {
        "id": "bid_123",
        "auction_id": 1,
        "buyer_name": "Test Buyer",
        "price": 1000,
        "bonus_description": "Test Bonus",
        "landing_url": "https://example.com"
    }
    mocker.patch("services.auction_service.main.database.fetch_one", new_callable=AsyncMock, return_value=mock_bid)
    
    response = await client.get("/bid/bid_123")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "bid_123"
    assert data["buyer_name"] == "Test Buyer"


@pytest.mark.asyncio
async def test_get_bid_info_not_found(client, mocker):
    """/bid/{bid_id} API 테스트 (입찰 없음)"""
    mocker.patch("services.auction_service.main.database.fetch_one", new_callable=AsyncMock, return_value=None)
    
    response = await client.get("/bid/invalid_bid_id")
    
    assert response.status_code == 404

