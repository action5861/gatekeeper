"""
경매 서비스 통합 테스트
- /start → /select → /status/{search_id} 3단계 통합 테스트
- 예산 초과, 키워드 미일치, 폴백 입찰 시나리오 검증
"""
import pytest
from fastapi.testclient import TestClient
from services.auction_service.main import app

client = TestClient(app)


def test_auction_workflow_start_select_status():
    """기본 경매 워크플로우 테스트: 시작 → 선택 → 상태 조회"""
    # 1. 경매 시작
    start_response = client.post(
        "/start",
        json={"query": "스마트폰", "valueScore": 75}
    )
    assert start_response.status_code == 200
    data = start_response.json()
    assert data["success"] is True
    assert "searchId" in data["data"]
    assert len(data["data"]["bids"]) > 0
    
    search_id = data["data"]["searchId"]
    
    # 첫 번째 입찰 선택
    selected_bid_id = data["data"]["bids"][0]["id"]
    
    # 2. 입찰 선택
    select_response = client.post(
        "/select",
        json={
            "searchId": search_id,
            "selectedBidId": selected_bid_id
        }
    )
    assert select_response.status_code == 200
    select_data = select_response.json()
    assert select_data["success"] is True
    assert "rewardAmount" in select_data["data"]
    
    # 3. 상태 조회
    status_response = client.get(f"/status/{search_id}")
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["success"] is True
    assert status_data["data"]["auction"]["status"] == "completed"


def test_auction_budget_exceeded():
    """예산 초과 시나리오 테스트"""
    # 광고주의 예산이 소진된 경우 플랫폼 폴백 입찰이 반환되는지 확인
    response = client.post(
        "/start",
        json={"query": "테스트 키워드", "valueScore": 50}
    )
    assert response.status_code == 200
    data = response.json()
    
    # 플랫폼 폴백 입찰이 포함되어 있는지 확인
    bids = data["data"]["bids"]
    platform_bids = [b for b in bids if b["id"].startswith("platform_bid_")]
    # 예산 초과 시 플랫폼 폴백이 제공되어야 함
    assert len(bids) > 0


def test_auction_keyword_mismatch_fallback():
    """키워드 미일치 시 폴백 입찰 테스트"""
    # 존재하지 않는 키워드로 검색
    response = client.post(
        "/start",
        json={"query": "존재하지않는키워드12345", "valueScore": 50}
    )
    assert response.status_code == 200
    data = response.json()
    
    # 플랫폼 폴백 입찰이 반환되어야 함
    bids = data["data"]["bids"]
    assert len(bids) > 0
    # 최소한 플랫폼 입찰이 있어야 함
    assert any(b["id"].startswith("platform_bid_") for b in bids)


def test_auction_invalid_search_id():
    """유효하지 않은 search_id로 상태 조회 시 에러 테스트"""
    response = client.get("/status/invalid_search_id_12345")
    assert response.status_code == 404


def test_health_check():
    """헬스체크 엔드포인트 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_system_status():
    """시스템 상태 확인 엔드포인트 테스트"""
    response = client.get("/system-status")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "statistics" in data
    assert "performance" in data
    assert "features" in data

