import pytest
from httpx import AsyncClient
from services.auction_service.main import app


@pytest.mark.asyncio
async def test_start_auction_basic_flow():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        payload = {"query": "제주도 항공권", "valueScore": 80}
        resp = await ac.post("/start", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True

        auction = data["data"]
        assert auction["query"] == "제주도 항공권"
        assert len(auction["bids"]) >= 1

        first_bid = auction["bids"][0]
        assert "reasons" in first_bid
        assert isinstance(first_bid["reasons"], list)
        assert "clickUrl" in first_bid
