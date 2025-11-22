import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock
import sys
from pathlib import Path

# 프로젝트 루트가 sys.path 에 추가되어 있어야 합니다
ROOT = Path(__file__).resolve().parent.parent.parent  # gatekeeper_copy
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# auction_service 디렉터리를 sys.path에 추가하여 utils 모듈 import 가능하도록
AUCTION_SERVICE_DIR = Path(__file__).resolve().parent
if str(AUCTION_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(AUCTION_SERVICE_DIR))

# OptimizedAdvertiserMatcher, OptimizedBidGenerator는 main.py에 통합되어 직접 사용하지 않음


@pytest.fixture(scope="session")
def anyio_backend():
    """pytest-asyncio가 httpx와 호환되도록 설정"""
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def client(mocker):
    """
    모든 테스트에서 사용할 비동기 HTTP 테스트 클라이언트 (CORS 헤더 포함)
    """
    from services.auction_service.main import app, database

    # DB 연결 함수를 모킹하여 실제 연결을 시도하지 않도록 함
    mocker.patch("services.auction_service.main.connect_to_database", return_value=None)
    mocker.patch(
        "services.auction_service.main.disconnect_from_database", return_value=None
    )

    # database 객체의 모든 메서드를 AsyncMock으로 대체
    mocker.patch.object(database, "connect", AsyncMock())
    mocker.patch.object(database, "disconnect", AsyncMock())
    mocker.patch.object(database, "fetch_one", AsyncMock(return_value=None))
    mocker.patch.object(database, "fetch_all", AsyncMock(return_value=[]))
    mocker.patch.object(database, "execute", AsyncMock())

    # transaction을 AsyncContextManager로 모킹
    mock_transaction = AsyncMock()
    mock_transaction.__aenter__ = AsyncMock(return_value=None)
    mock_transaction.__aexit__ = AsyncMock(return_value=False)
    mocker.patch.object(database, "transaction", return_value=mock_transaction)

    # 모든 요청에 'Origin' 헤더를 추가하여 CORS 문제를 해결합니다.
    headers = {"Origin": "http://localhost:3000"}

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test", headers=headers
    ) as ac:
        yield ac


class FakeDB:
    """테스트 전용 가짜 DB. main.py 내부의 배치 쿼리 패턴을 키워드로 분기해 응답을 생성합니다."""

    async def fetch_all(self, query: str, values=None):
        values = values or {}
        q = (query or "").lower()

        # 1) advertisers + settings + reviews (enabled만 반환)
        if "from advertisers" in q and "auto_bid_settings" in q:
            # ids 필터링
            ids = values.get("ids")

            def mkrow(advid):
                return {
                    "advertiser_id": advid,
                    "company_name": f"Advertiser-{advid}",
                    "website_url": f"https://adv{advid}.example.com",
                    "daily_budget": 100000,
                    "max_bid_per_keyword": 3000,
                    "min_quality_score": 50,
                    "review_status": "approved",
                    "recommended_bid_min": 500,
                    "recommended_bid_max": 2500,
                    "is_enabled": True,
                }

            base = [mkrow(101), mkrow(202), mkrow(303)]
            if ids:
                return [r for r in base if r["advertiser_id"] in ids]
            return base

        # 2) auto_bid_settings enabled map
        if (
            "from auto_bid_settings" in q
            and "is_enabled = true" in q
            and "where advertiser_id = any" in q
        ):
            ids = values.get("ids", [])
            return [{"advertiser_id": i, "min_quality_score": 50} for i in ids]

        # 3) advertiser_keywords (EXACT/PHRASE/BROAD)
        if "from advertiser_keywords" in q:
            tokens_norm = set(values.get("tokens_norm", []))
            tokens_like = set(values.get("tokens_like", []))
            rows = []

            # 간단한 키워드 샘플
            sample_kw = [
                {
                    "advertiser_id": 101,
                    "keyword": "테스트키워드",
                    "priority": 5,
                    "match_type": "exact",
                },
                {
                    "advertiser_id": 202,
                    "keyword": "제주도 항공권",
                    "priority": 4,
                    "match_type": "phrase",
                },
                {
                    "advertiser_id": 303,
                    "keyword": "키워드",
                    "priority": 3,
                    "match_type": "broad",
                },
            ]

            def norm(s):
                return "".join(s.lower().split())

            if "match_type = 'exact'" in q or "match_type = 'phrase'" in q:
                for kw in sample_kw:
                    if (
                        kw["match_type"] in ("exact", "phrase")
                        and norm(kw["keyword"]) in tokens_norm
                    ):
                        rows.append(kw)

            if "match_type = 'broad'" in q:
                for kw in sample_kw:
                    if kw["match_type"] == "broad":
                        # LIKE 매칭 간소화 (tokens_like: '%토큰%')
                        for tl in tokens_like:
                            t = tl.strip("%").lower()
                            if t and t in kw["keyword"].lower():
                                rows.append(kw)
                                break
            return rows

        # 4) advertiser_categories + business_categories 조인
        if "from advertiser_categories" in q and "business_categories" in q:
            # 모든 광고주에 동일한 카테고리 하나씩 있다고 가정
            return [
                {
                    "advertiser_id": 101,
                    "category_path": "/쇼핑/항공권",
                    "is_primary": True,
                    "category_name": "항공권",
                },
                {
                    "advertiser_id": 202,
                    "category_path": "/여행/제주",
                    "is_primary": False,
                    "category_name": "제주",
                },
                {
                    "advertiser_id": 303,
                    "category_path": "/쇼핑/티켓",
                    "is_primary": False,
                    "category_name": "티켓",
                },
            ]

        # 5) business_categories 단독 조회
        if "from business_categories" in q:
            return [
                {
                    "id": 1,
                    "name": "항공권",
                    "path": "/쇼핑/항공권",
                    "level": 2,
                    "is_active": True,
                },
                {
                    "id": 2,
                    "name": "제주",
                    "path": "/여행/제주",
                    "level": 2,
                    "is_active": True,
                },
                {
                    "id": 3,
                    "name": "티켓",
                    "path": "/쇼핑/티켓",
                    "level": 2,
                    "is_active": True,
                },
            ]

        # 기타: 빈 리스트
        return []

    async def fetch_one(self, query: str, values=None):
        # budget query 등에서 사용
        q = (query or "").lower()
        if "from auto_bid_settings" in q and "daily_budget" in q:
            return {"daily_budget": 100000}
        if "sum(price)" in q:
            return {"total_spent": 1000}
        return None

    async def execute(self, query: str, values=None):
        return None


@pytest.fixture
def fake_db():
    return FakeDB()


@pytest.fixture(scope="function")
def db_mock(mocker):
    """
    database 객체를 직접 모킹하여 반환값을 제어할 수 있는 픽스처
    """
    mock = MagicMock()
    mock.fetch_one = AsyncMock()
    mock.fetch_all = AsyncMock()
    mock.execute = AsyncMock()

    # 트랜잭션 컨텍스트 매니저 모킹
    mock_transaction = AsyncMock()
    mock_transaction.__aenter__ = AsyncMock(return_value=None)
    mock_transaction.__aexit__ = AsyncMock(return_value=False)
    mock.transaction = AsyncMock(return_value=mock_transaction)

    # main 모듈의 'database' 객체를 이 mock으로 교체
    mocker.patch("services.auction_service.main.database", new=mock)
    return mock


# OptimizedAdvertiserMatcher, OptimizedBidGenerator는 main.py에 통합되어
# 별도의 fixture가 필요하지 않음
