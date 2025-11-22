# app.py
import os
import re
import random
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Optional, Literal, Annotated
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator, Field, ConfigDict
import httpx
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# 데이터베이스
from database import (
    database,
    connect_to_database,
    disconnect_from_database,
)

# AutoBidOptimizer
from auto_bid_optimizer import (
    AutoBidOptimizer,
    BidContext,
    MatchType,
    BidResult,
    OptimizationResult,
)

# ------------------------------------------------------------------------------
# 환경/로깅
# ------------------------------------------------------------------------------
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("advertiser-service")

DATABASE_URL = os.getenv("DATABASE_URL", "")
SAFE_DB_REFERENCE = None
if DATABASE_URL:
    parsed_db = urlparse(DATABASE_URL)
    host = parsed_db.hostname or "unknown-host"
    port = f":{parsed_db.port}" if parsed_db.port else ""
    db_name = parsed_db.path.lstrip("/") or "unknown-db"
    SAFE_DB_REFERENCE = f"{parsed_db.scheme}://{host}{port}/{db_name}"
    logger.info("Advertiser service database target: %s", SAFE_DB_REFERENCE)

app = FastAPI(title="Advertiser Service", version="1.1.0")


# ------------------------------------------------------------------------------
# 시작/종료 이벤트
# ------------------------------------------------------------------------------
@app.on_event("startup")
async def startup():
    await connect_to_database()
    # 카테고리 초기 데이터 (idempotent)
    try:
        # name 컬럼에 UNIQUE 제약이 있다고 가정. 없다면 추가 권장.
        # 카테고리 데이터를 개별적으로 삽입 (ON CONFLICT 지원)
        categories = [
            {"name": "전자제품", "path": "전자제품", "level": 1, "sort_order": 1},
            {"name": "패션/뷰티", "path": "패션/뷰티", "level": 1, "sort_order": 2},
            {"name": "생활/건강", "path": "생활/건강", "level": 1, "sort_order": 3},
            {"name": "식품/음료", "path": "식품/음료", "level": 1, "sort_order": 4},
            {
                "name": "스포츠/레저/자동차",
                "path": "스포츠/레저/자동차",
                "level": 1,
                "sort_order": 5,
            },
            {"name": "유아/아동", "path": "유아/아동", "level": 1, "sort_order": 6},
            {"name": "여행/문화", "path": "여행/문화", "level": 1, "sort_order": 7},
            {"name": "반려동물", "path": "반려동물", "level": 1, "sort_order": 8},
            {
                "name": "디지털 콘텐츠",
                "path": "디지털 콘텐츠",
                "level": 1,
                "sort_order": 9,
            },
            {
                "name": "부동산/인테리어",
                "path": "부동산/인테리어",
                "level": 1,
                "sort_order": 10,
            },
            {
                "name": "의료/건강",
                "path": "의료/건강",
                "level": 1,
                "sort_order": 11,
            },
            {"name": "서비스", "path": "서비스", "level": 1, "sort_order": 12},
            {
                "name": "교육/도서",
                "path": "교육/도서",
                "level": 1,
                "sort_order": 13,
            },
        ]

        for category in categories:
            await database.execute(
                """
                INSERT INTO business_categories (name, path, level, sort_order)
                VALUES (:name, :path, :level, :sort_order)
                ON CONFLICT DO NOTHING
                """,
                category,
            )
    except Exception as e:
        logger.exception("카테고리 초기화 중 오류: %r", e)
        # 계속 실행


@app.on_event("shutdown")
async def shutdown():
    await disconnect_from_database()


# ------------------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------------------
origins_env = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000")
allow_origins = [o.strip() for o in origins_env.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,  # "*" + credentials 조합 금지
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# 보안/JWT/패스워드
# ------------------------------------------------------------------------------
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("환경변수 JWT_SECRET_KEY가 설정되어야 합니다.")
# 타입 힌트를 명확히 하기 위해 assert 사용
assert SECRET_KEY is not None
ALGORITHM = os.getenv("JWT_ALG", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
JWT_ISSUER = os.getenv("JWT_ISSUER")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE")

# Website Analysis Service URL
WEBSITE_ANALYSIS_SERVICE_URL = os.getenv(
    "WEBSITE_ANALYSIS_SERVICE_URL", "http://website-analysis-service:8009"
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=True)


def verify_password(plain_password, hashed_password) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    if JWT_ISSUER:
        to_encode["iss"] = JWT_ISSUER
    if JWT_AUDIENCE:
        to_encode["aud"] = JWT_AUDIENCE
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # type: ignore


async def get_current_advertiser(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    logger.info(f"Validating JWT token: {token[:50]}...")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,  # type: ignore
            algorithms=[ALGORITHM],
            issuer=JWT_ISSUER if JWT_ISSUER else None,
            audience=JWT_AUDIENCE if JWT_AUDIENCE else None,
            options={
                "require_exp": True,
                "verify_iss": bool(JWT_ISSUER),
                "verify_aud": bool(JWT_AUDIENCE),
            },
        )
        username = payload.get("sub")
        logger.info(f"JWT payload extracted: username={username}")

        if not username:
            logger.warning("No username found in JWT payload")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"JWT validation failed: {e}")
        raise credentials_exception

    logger.info(f"Looking up advertiser with username: {username}")
    adv = await database.fetch_one(
        "SELECT * FROM advertisers WHERE username = :u OR email = :u",
        {"u": username},
    )
    if not adv:
        logger.warning(f"Advertiser not found for username: {username}")
        raise credentials_exception

    logger.info(f"Advertiser found: ID={adv['id']}, username={adv['username']}")
    return dict(adv)


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """관리자 JWT 토큰 검증"""
    print("=== requireAdminAuth called ===")
    print("=== Admin Auth Debug ===")
    print(
        f"Authorization header: {credentials.scheme} {credentials.credentials[:50]}..."
    )

    token = credentials.credentials
    print(f"Extracted token: {token[:50]}...")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,  # type: ignore
            algorithms=[ALGORITHM],
            issuer=JWT_ISSUER if JWT_ISSUER else None,
            audience=JWT_AUDIENCE if JWT_AUDIENCE else None,
        )
        print(f"JWT payload: {payload}")

        username = payload.get("username")
        role = payload.get("role")
        if username is None or role != "admin":
            print(f"Invalid credentials: username={username}, role={role}")
            raise credentials_exception

        print("Admin auth successful")
        admin_data = {
            "username": str(username),
            "role": str(role),
            "id": payload.get("sub"),
        }
        print(f"Admin auth successful, returning admin: {admin_data.get('username')}")
        return admin_data
    except JWTError as e:
        print(f"JWT decode error: {e}")
        raise credentials_exception


# require_admin 함수 제거 - get_current_admin에서 이미 role 검증을 수행함


# ------------------------------------------------------------------------------
# 유틸/검증
# ------------------------------------------------------------------------------
def sanitize_input(value: str) -> str:
    return value.strip() if isinstance(value, str) else str(value)


def validate_password_strength(password: str) -> bool:
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False
    return True


def validate_url(u: str) -> bool:
    try:
        p = urlparse(u)
        return p.scheme in {"http", "https"} and bool(p.netloc)
    except Exception:
        return False


def parse_match_type(s: str) -> "MatchType":
    try:
        return MatchType(s)
    except Exception:
        return MatchType("broad")


# ------------------------------------------------------------------------------
# Pydantic 모델
# ------------------------------------------------------------------------------
class PerformanceHistory(BaseModel):
    name: str = Field(..., max_length=100)
    score: int = Field(..., ge=0, le=100)

    @validator("name")
    def validate_name(cls, v):
        return sanitize_input(v)


class BiddingSummary(BaseModel):
    totalBids: int = Field(..., ge=0)
    successfulBids: int = Field(..., ge=0)
    totalSpent: int = Field(..., ge=0)
    averageBidAmount: float = Field(..., ge=0)


class DashboardResponse(BaseModel):
    biddingSummary: Optional[BiddingSummary] = None
    performanceHistory: Optional[List[PerformanceHistory]] = None
    recentBids: Optional[List[dict]] = None
    additionalStats: Optional[dict] = None
    advertiserInfo: Optional[dict] = None


class BidRange(BaseModel):
    min: int = Field(..., ge=50, le=10000, description="최소 입찰가")
    max: int = Field(..., ge=50, le=10000, description="최대 입찰가")

    @validator("max")
    def validate_max_greater_than_min(cls, v, values):
        if "min" in values and v <= values["min"]:
            raise ValueError("최대 입찰가는 최소 입찰가보다 커야 합니다")
        return v


class BusinessSetupData(BaseModel):
    # AI 온보딩: websiteUrl만 필수, 나머지는 선택적 (AI가 자동 생성하거나 기본값 사용)
    websiteUrl: str = Field(..., max_length=500)
    keywords: Optional[List[str]] = Field(None, description="키워드 목록")
    categories: Optional[List[int]] = Field(None, description="카테고리 ID 목록")
    dailyBudget: Optional[int] = Field(None, ge=1000, le=10000000)
    bidRange: Optional[BidRange] = None

    @validator("websiteUrl")
    def validate_website_url(cls, v):
        v = sanitize_input(v)
        if not validate_url(v):
            raise ValueError("올바른 URL 형식이 아닙니다")
        return v

    @validator("keywords")
    def validate_keywords(cls, v):
        if v is None:
            return v
        if len(v) > 100:
            raise ValueError("키워드는 최대 100개까지 입력 가능합니다")
        for k in v:
            k = sanitize_input(k)
            if len(k) > 50:
                raise ValueError("키워드는 최대 50자까지 입력 가능합니다")
        return v

    @validator("categories")
    def validate_categories(cls, v):
        if v is None:
            return v
        if len(v) > 50:
            raise ValueError("카테고리는 최대 50개까지 선택 가능합니다")
        for cid in v:
            if not isinstance(cid, int) or cid < 1:
                raise ValueError("올바른 카테고리 ID가 아닙니다")
        return v


class AutoBidSettingsUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    daily_budget: Annotated[
        float,
        Field(gt=0, alias="dailyBudget", description="일일 예산(양수)"),
    ]
    max_bid_per_keyword: Annotated[
        int,
        Field(
            ge=0, alias="maxBidPerKeyword", description="키워드당 최대 입찰가(0 이상)"
        ),
    ]
    min_quality_score: Annotated[
        int,
        Field(
            ge=0,
            le=100,
            alias="minQualityScore",
            description="최소 품질 점수(0~100)",
        ),
    ]
    is_enabled: bool = Field(
        True, alias="isEnabled", description="자동 입찰 활성화 여부"
    )
    excluded_keywords: Optional[List[str]] = Field(
        default=None,
        alias="excludedKeywords",
        description="제외 키워드 목록",
    )

    @validator("excluded_keywords", pre=True, always=True)
    def ensure_list(cls, value: Optional[Any]) -> List[str]:
        if value in (None, "", []):
            return []
        if isinstance(value, str):
            cleaned = value.strip()
            return [cleaned] if cleaned else []
        if isinstance(value, list):
            cleaned_list: List[str] = []
            for item in value:
                if item is None:
                    continue
                cleaned = str(item).strip()
                if cleaned:
                    cleaned_list.append(cleaned)
            return cleaned_list
        raise ValueError("excluded_keywords must be a list of strings")


class AdvertiserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    company_name: str = Field(..., min_length=2, max_length=100)
    business_setup: Optional[BusinessSetupData] = None

    @validator("username")
    def validate_username(cls, v):
        v = sanitize_input(v)
        if not re.match(r"^[a-zA-Z0-9_가-힣]+$", v):
            raise ValueError("사용자명은 영문, 숫자, 언더스코어, 한글만 가능")
        return v

    @validator("email")
    def validate_email(cls, v):
        return sanitize_input(v.lower())

    @validator("password")
    def validate_password(cls, v):
        if not validate_password_strength(v):
            raise ValueError("비밀번호는 8자 이상, 대/소문자, 숫자, 특수문자 포함")
        return v

    @validator("company_name")
    def validate_company_name(cls, v):
        return sanitize_input(v)


class AdvertiserLogin(BaseModel):
    username: str
    password: str

    @validator("username")
    def v_user(cls, v):
        return sanitize_input(v)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# ------------------------------------------------------------------------------
# 헬퍼
# ------------------------------------------------------------------------------
async def get_recent_bids() -> List[dict]:
    """최근 입찰 내역 (외부 경매 서비스 연동 예시)"""
    try:
        auction_service_url = os.getenv("AUCTION_SERVICE_URL", "http://localhost:8002")
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{auction_service_url}/bids")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("bids", [])
    except Exception as error:
        logger.warning("Failed to fetch bids: %r", error)
    return []


# ------------------------------------------------------------------------------
# 엔드포인트: 인증/등록
# ------------------------------------------------------------------------------
@app.post("/register", response_model=dict)
async def register_advertiser(advertiser: AdvertiserRegister):
    """광고주 회원가입"""
    try:
        logger.info(f"Registration attempt for: {advertiser.username}")
        logger.info(f"Business setup data: {advertiser.business_setup}")
        # 이메일 중복
        existing_email = await database.fetch_one(
            "SELECT id FROM advertisers WHERE email = :email",
            {"email": advertiser.email},
        )
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already registered")

        # 사용자명 중복
        existing_username = await database.fetch_one(
            "SELECT id FROM advertisers WHERE username = :username",
            {"username": advertiser.username},
        )
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already registered")

        hashed_password = get_password_hash(advertiser.password)

        website_url = (
            advertiser.business_setup.websiteUrl if advertiser.business_setup else None
        )
        daily_budget = (
            advertiser.business_setup.dailyBudget
            if advertiser.business_setup and advertiser.business_setup.dailyBudget
            else 10000.0
        )

        new_id_row = await database.fetch_one(
            """
            INSERT INTO advertisers (username, email, hashed_password, company_name, website_url, daily_budget, approval_status)
            VALUES (:username, :email, :hashed_password, :company_name, :website_url, :daily_budget, :approval_status)
            RETURNING id
            """,
            {
                "username": advertiser.username,
                "email": advertiser.email,
                "hashed_password": hashed_password,
                "company_name": advertiser.company_name,
                "website_url": website_url,
                "daily_budget": daily_budget,
                "approval_status": "pending_analysis" if website_url else "pending",
            },
        )
        if not new_id_row:
            raise HTTPException(status_code=500, detail="Failed to create advertiser")
        advertiser_id = new_id_row["id"]

        if advertiser.business_setup:
            await save_business_setup_data(advertiser_id, advertiser.business_setup)

        # 심사 상태 생성 (website_url 전달)
        await create_review_status(advertiser_id, website_url)

        # 웹사이트 URL이 있으면 AI 분석 서비스 호출
        if website_url:
            await trigger_website_analysis(advertiser_id, website_url)
            message = "광고주 등록이 완료되었습니다. AI가 웹사이트를 분석 중이며, 완료 후 알림을 드립니다."
            review_status = "pending_analysis"
        else:
            message = "광고주 등록이 완료되었습니다. 24시간 내에 심사가 완료됩니다."
            review_status = "pending"

        return {
            "success": True,
            "message": message,
            "username": advertiser.username,
            "review_status": review_status,
            "review_message": (
                "AI 분석 진행 중" if website_url else "24시간 내 심사 완료"
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Registration error: %r", e)
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


async def save_business_setup_data(
    advertiser_id: int, business_setup: BusinessSetupData
):
    """비즈니스 설정 저장"""
    try:
        # 키워드 (사용자가 직접 입력한 키워드) - AI 온보딩 시에는 None일 수 있음
        if business_setup.keywords:
            for keyword in business_setup.keywords:
                await database.execute(
                    """
                    INSERT INTO advertiser_keywords (advertiser_id, keyword, priority, match_type, source)
                    VALUES (:advertiser_id, :keyword, :priority, :match_type, :source)
                    """,
                    {
                        "advertiser_id": advertiser_id,
                        "keyword": keyword,
                        "priority": 1,
                        "match_type": "broad",
                        "source": "user_added",
                    },
                )

        # 카테고리 (사용자가 직접 선택한 카테고리) - AI 온보딩 시에는 None일 수 있음
        if business_setup.categories:
            for category_id in business_setup.categories:
                try:
                    info = await database.fetch_one(
                        "SELECT name, path, level FROM business_categories WHERE id = :id",
                        {"id": category_id},
                    )
                    if info:
                        await database.execute(
                            """
                            INSERT INTO advertiser_categories (advertiser_id, category_path, category_level, is_primary, source)
                            VALUES (:advertiser_id, :path, :level, :is_primary, :source)
                            """,
                            {
                                "advertiser_id": advertiser_id,
                                "path": info["path"],
                                "level": info["level"],
                                "is_primary": False,
                                "source": "user_added",
                            },
                        )
                    else:
                        await database.execute(
                            """
                            INSERT INTO advertiser_categories (advertiser_id, category_path, category_level, is_primary, source)
                            VALUES (:advertiser_id, :path, :level, :is_primary, :source)
                            """,
                            {
                                "advertiser_id": advertiser_id,
                                "path": f"Unknown Category {category_id}",
                                "level": 1,
                                "is_primary": False,
                                "source": "user_added",
                            },
                        )
                except Exception:
                    await database.execute(
                        """
                        INSERT INTO advertiser_categories (advertiser_id, category_path, category_level, is_primary, source)
                        VALUES (:advertiser_id, :path, :level, :is_primary, :source)
                        """,
                        {
                            "advertiser_id": advertiser_id,
                            "path": f"Category {category_id}",
                            "level": 1,
                            "is_primary": False,
                            "source": "user_added",
                        },
                    )

        # 자동 입찰 초기 설정 - AI 온보딩 시 기본값 사용
        import json

        # 기본값 설정
        daily_budget = (
            business_setup.dailyBudget if business_setup.dailyBudget else 10000
        )
        min_bid = business_setup.bidRange.min if business_setup.bidRange else 100
        max_bid = business_setup.bidRange.max if business_setup.bidRange else 3000
        # JSONB 타입에는 Python dict/list를 직접 전달
        preferred_cats = business_setup.categories if business_setup.categories else []

        await database.execute(
            """
            INSERT INTO auto_bid_settings (
                advertiser_id, is_enabled, daily_budget, min_bid_per_keyword, max_bid_per_keyword, 
                min_quality_score, preferred_categories, excluded_keywords
            )
            VALUES (:advertiser_id, :is_enabled, :daily_budget, :min_bid_per_keyword, :max_bid_per_keyword, 
                    :min_quality_score, :preferred_categories, :excluded_keywords)
            """,
            {
                "advertiser_id": advertiser_id,
                "is_enabled": False,
                "daily_budget": daily_budget,
                "min_bid_per_keyword": min_bid,
                "max_bid_per_keyword": max_bid,
                "min_quality_score": 50,
                "preferred_categories": json.dumps(
                    preferred_cats
                ),  # JSONB는 JSON 문자열
                "excluded_keywords": [],  # TEXT[] 배열은 Python 리스트
            },
        )
    except Exception as e:
        logger.exception("save_business_setup_data error: %r", e)
        raise


async def create_review_status(advertiser_id: int, website_url: Optional[str] = None):
    """심사 상태 생성"""
    try:
        # 웹사이트 URL이 있으면 AI 분석 대기, 없으면 일반 심사 대기
        review_status = "pending_analysis" if website_url else "pending"
        await database.execute(
            """
            INSERT INTO advertiser_reviews (advertiser_id, review_status, recommended_bid_min, recommended_bid_max)
            VALUES (:advertiser_id, :review_status, :min_bid, :max_bid)
            """,
            {
                "advertiser_id": advertiser_id,
                "review_status": review_status,
                "min_bid": 100,
                "max_bid": 5000,
            },
        )
    except Exception as e:
        logger.exception("create_review_status error: %r", e)
        raise


async def trigger_website_analysis(advertiser_id: int, website_url: str):
    """
    WebsiteAnalysisService에 분석 요청을 비동기로 전송합니다.
    실패해도 회원가입은 완료되어야 하므로 에러를 로깅만 합니다.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{WEBSITE_ANALYSIS_SERVICE_URL}/analyze",
                json={"advertiser_id": advertiser_id, "url": website_url},
            )
            if response.status_code == 200:
                logger.info(
                    f"✅ Website analysis triggered for advertiser_id={advertiser_id}"
                )
            else:
                logger.warning(
                    f"⚠️ Website analysis request failed with status {response.status_code} for advertiser_id={advertiser_id}"
                )
    except Exception as e:
        logger.error(
            f"❌ Failed to trigger website analysis for advertiser_id={advertiser_id}: {e}"
        )


@app.post("/login", response_model=Token)
async def login_advertiser(advertiser: AdvertiserLogin):
    try:
        logger.info(f"Login attempt for username: {advertiser.username}")
        logger.info(f"Password provided: {bool(advertiser.password)}")

        user = await database.fetch_one(
            "SELECT * FROM advertisers WHERE username = :u OR email = :u",
            {"u": advertiser.username},
        )
        if not user:
            logger.warning(f"User not found: {advertiser.username}")
            raise HTTPException(
                status_code=401, detail="Incorrect username or password"
            )

        logger.info(f"User found: {user['username']}, verifying password...")
        password_valid = verify_password(advertiser.password, user["hashed_password"])
        logger.info(f"Password verification result: {password_valid}")

        if not password_valid:
            logger.warning(f"Invalid password for user: {advertiser.username}")
            raise HTTPException(
                status_code=401, detail="Incorrect username or password"
            )

        token_data = {"sub": user["username"]}
        logger.info(f"Creating JWT token with data: {token_data}")

        token = create_access_token(
            data=token_data,
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        logger.info(f"JWT token created successfully for user: {user['username']}")

        return {"access_token": token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Login error: %r", e)
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


# ------------------------------------------------------------------------------
# AI 온보딩 관련 API
# ------------------------------------------------------------------------------
@app.get("/status")
async def get_advertiser_status(
    current_advertiser: dict = Depends(get_current_advertiser),
):
    """현재 광고주의 승인 상태 및 심사 상태 조회"""
    try:
        advertiser_id = current_advertiser["id"]

        # 광고주 기본 정보 조회
        advertiser_info = await database.fetch_one(
            """
            SELECT approval_status, website_url, created_at
            FROM advertisers 
            WHERE id = :id
            """,
            {"id": advertiser_id},
        )

        if not advertiser_info:
            raise HTTPException(status_code=404, detail="Advertiser not found")

        # 심사 정보 조회
        review_info = await database.fetch_one(
            """
            SELECT review_status, website_analysis, updated_at
            FROM advertiser_reviews 
            WHERE advertiser_id = :id
            ORDER BY created_at DESC LIMIT 1
            """,
            {"id": advertiser_id},
        )

        return {
            "approval_status": advertiser_info["approval_status"],
            "review_status": review_info["review_status"] if review_info else None,
            "website_analysis": (
                review_info["website_analysis"] if review_info else None
            ),
            "website_url": advertiser_info["website_url"],
            "created_at": (
                advertiser_info["created_at"].isoformat()
                if advertiser_info["created_at"]
                else None
            ),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Get status error: %r", e)
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@app.get("/ai-suggestions")
async def get_ai_suggestions(
    current_advertiser: dict = Depends(get_current_advertiser),
):
    """AI가 제안한 키워드와 카테고리 조회"""
    try:
        advertiser_id = current_advertiser["id"]

        # AI가 제안한 키워드 조회
        keywords = await database.fetch_all(
            """
            SELECT id, keyword, priority, match_type
            FROM advertiser_keywords 
            WHERE advertiser_id = :id AND source = 'ai_suggested'
            ORDER BY id
            """,
            {"id": advertiser_id},
        )

        # AI가 제안한 카테고리 조회
        categories = await database.fetch_all(
            """
            SELECT id, category_path, category_level, is_primary
            FROM advertiser_categories 
            WHERE advertiser_id = :id AND source = 'ai_suggested'
            ORDER BY id
            """,
            {"id": advertiser_id},
        )

        return {
            "keywords": [
                {
                    "id": row["id"],
                    "keyword": row["keyword"],
                    "priority": row["priority"],
                    "match_type": row["match_type"],
                }
                for row in keywords
            ],
            "categories": [
                {
                    "id": row["id"],
                    "category_path": row["category_path"],
                    "category_level": row["category_level"],
                    "is_primary": row["is_primary"],
                }
                for row in categories
            ],
        }
    except Exception as e:
        logger.exception("Get AI suggestions error: %r", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to get AI suggestions: {str(e)}"
        )


@app.post("/confirm-suggestions")
async def confirm_suggestions(
    payload: dict, current_advertiser: dict = Depends(get_current_advertiser)
):
    """사용자가 수정한 AI 제안을 확정"""
    try:
        advertiser_id = current_advertiser["id"]
        keywords = payload.get("keywords", [])
        categories = payload.get("categories", [])

        # 기존 AI 제안 삭제
        await database.execute(
            "DELETE FROM advertiser_keywords WHERE advertiser_id = :id AND source = 'ai_suggested'",
            {"id": advertiser_id},
        )
        await database.execute(
            "DELETE FROM advertiser_categories WHERE advertiser_id = :id AND source = 'ai_suggested'",
            {"id": advertiser_id},
        )

        # 수정된 키워드 저장 (source를 'user_confirmed'로 변경)
        for kw in keywords:
            await database.execute(
                """
                INSERT INTO advertiser_keywords (advertiser_id, keyword, source, match_type, priority)
                VALUES (:advertiser_id, :keyword, 'user_confirmed', :match_type, :priority)
                """,
                {
                    "advertiser_id": advertiser_id,
                    "keyword": kw.get("keyword"),
                    "match_type": kw.get("match_type", "broad"),
                    "priority": kw.get("priority", 1),
                },
            )

        # 수정된 카테고리 저장 (source를 'user_confirmed'로 변경)
        for cat in categories:
            await database.execute(
                """
                INSERT INTO advertiser_categories (advertiser_id, category_path, source, category_level, is_primary)
                VALUES (:advertiser_id, :category_path, 'user_confirmed', :category_level, :is_primary)
                """,
                {
                    "advertiser_id": advertiser_id,
                    "category_path": cat.get("category_path"),
                    "category_level": cat.get("category_level", 1),
                    "is_primary": cat.get("is_primary", False),
                },
            )

        return {
            "success": True,
            "message": "설정이 확정되었습니다.",
            "keywords_count": len(keywords),
            "categories_count": len(categories),
        }
    except Exception as e:
        logger.exception("Confirm suggestions error: %r", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to confirm suggestions: {str(e)}"
        )


# ------------------------------------------------------------------------------
# 심사/관리자 API (관리자 보호)
# ------------------------------------------------------------------------------
@app.get("/review-status")
async def get_review_status(current_advertiser: dict = Depends(get_current_advertiser)):
    try:
        advertiser_id = current_advertiser["id"]
        review_info = await database.fetch_one(
            """
            SELECT review_status, review_notes, created_at, updated_at
            FROM advertiser_reviews 
            WHERE advertiser_id = :id
            ORDER BY created_at DESC LIMIT 1
            """,
            {"id": advertiser_id},
        )
        if not review_info:
            return {
                "review_status": "not_found",
                "message": "심사 정보를 찾을 수 없습니다.",
            }

        status_messages = {
            "pending": "심사 대기 중입니다. 24시간 내에 심사가 완료됩니다.",
            "in_progress": "심사가 진행 중입니다.",
            "approved": "심사가 승인되었습니다. 광고 등록이 가능합니다.",
            "rejected": "심사가 거부되었습니다. 자세한 내용은 관리자에게 문의하세요.",
        }
        return {
            "review_status": review_info["review_status"],
            "message": status_messages.get(
                review_info["review_status"], "알 수 없는 상태입니다."
            ),
            "created_at": review_info["created_at"],
            "updated_at": review_info["updated_at"],
            "notes": review_info["review_notes"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_review_status error: %r", e)
        raise HTTPException(status_code=500, detail=f"심사 상태 조회 실패: {str(e)}")


@app.get("/admin/pending-reviews")
async def get_pending_reviews(admin_user: dict = Depends(get_current_admin)):
    try:
        advertisers = await database.fetch_all(
            """
            SELECT 
                ar.id, ar.advertiser_id, adv.company_name, adv.email, adv.website_url, 
                adv.daily_budget, ar.created_at, ar.review_status, ar.review_notes,
                ar.recommended_bid_min, ar.recommended_bid_max
            FROM advertiser_reviews ar
            JOIN advertisers adv ON ar.advertiser_id = adv.id
            WHERE ar.review_status = 'pending'
            ORDER BY ar.created_at ASC
            """
        )
        result = []
        for adv in advertisers:
            keywords = await database.fetch_all(
                "SELECT keyword FROM advertiser_keywords WHERE advertiser_id = :id",
                {"id": adv["advertiser_id"]},
            )
            categories = await database.fetch_all(
                "SELECT category_path FROM advertiser_categories WHERE advertiser_id = :id",
                {"id": adv["advertiser_id"]},
            )
            result.append(
                {
                    "id": adv["id"],
                    "advertiser_id": adv["advertiser_id"],
                    "company_name": adv["company_name"],
                    "email": adv["email"],
                    "website_url": adv["website_url"],
                    "daily_budget": float(adv["daily_budget"]),
                    "created_at": adv["created_at"].isoformat(),
                    "review_status": adv["review_status"],
                    "review_notes": adv["review_notes"],
                    "recommended_bid_min": adv["recommended_bid_min"],
                    "recommended_bid_max": adv["recommended_bid_max"],
                    "keywords": [k["keyword"] for k in keywords],
                    "categories": [c["category_path"] for c in categories],
                }
            )
        return {"advertisers": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_pending_reviews error: %r", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch pending reviews: {str(e)}"
        )


@app.get("/admin/rejected-advertisers")
async def get_rejected_advertisers(admin_user: dict = Depends(get_current_admin)):
    try:
        advertisers = await database.fetch_all(
            """
            SELECT 
                ar.id, ar.advertiser_id, adv.company_name, adv.email, adv.website_url, 
                adv.daily_budget, ar.created_at, ar.review_status, ar.review_notes,
                ar.recommended_bid_min, ar.recommended_bid_max
            FROM advertiser_reviews ar
            JOIN advertisers adv ON ar.advertiser_id = adv.id
            WHERE ar.review_status = 'rejected'
            ORDER BY ar.created_at DESC
            """
        )
        result = []
        for adv in advertisers:
            keywords = await database.fetch_all(
                "SELECT keyword FROM advertiser_keywords WHERE advertiser_id = :id",
                {"id": adv["advertiser_id"]},
            )
            categories = await database.fetch_all(
                "SELECT category_path FROM advertiser_categories WHERE advertiser_id = :id",
                {"id": adv["advertiser_id"]},
            )
            result.append(
                {
                    "id": adv["id"],
                    "advertiser_id": adv["advertiser_id"],
                    "company_name": adv["company_name"],
                    "email": adv["email"],
                    "website_url": adv["website_url"],
                    "daily_budget": float(adv["daily_budget"]),
                    "created_at": adv["created_at"].isoformat(),
                    "review_status": adv["review_status"],
                    "review_notes": adv["review_notes"],
                    "recommended_bid_min": adv["recommended_bid_min"],
                    "recommended_bid_max": adv["recommended_bid_max"],
                    "keywords": [k["keyword"] for k in keywords],
                    "categories": [c["category_path"] for c in categories],
                }
            )
        return {"advertisers": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_rejected_advertisers error: %r", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch rejected advertisers: {str(e)}"
        )


@app.get("/admin/approved-advertisers")
async def get_approved_advertisers(admin_user: dict = Depends(get_current_admin)):
    try:
        advertisers = await database.fetch_all(
            """
            SELECT 
                ar.id, ar.advertiser_id, adv.company_name, adv.email, adv.website_url, 
                adv.daily_budget, ar.created_at, ar.review_status, ar.review_notes,
                ar.recommended_bid_min, ar.recommended_bid_max
            FROM advertiser_reviews ar
            JOIN advertisers adv ON ar.advertiser_id = adv.id
            WHERE ar.review_status = 'approved'
            ORDER BY ar.created_at DESC
            """
        )
        result = []
        for adv in advertisers:
            keywords = await database.fetch_all(
                "SELECT keyword FROM advertiser_keywords WHERE advertiser_id = :id",
                {"id": adv["advertiser_id"]},
            )
            categories = await database.fetch_all(
                "SELECT category_path FROM advertiser_categories WHERE advertiser_id = :id",
                {"id": adv["advertiser_id"]},
            )
            result.append(
                {
                    "id": adv["id"],
                    "advertiser_id": adv["advertiser_id"],
                    "company_name": adv["company_name"],
                    "email": adv["email"],
                    "website_url": adv["website_url"],
                    "daily_budget": float(adv["daily_budget"]),
                    "created_at": adv["created_at"].isoformat(),
                    "review_status": adv["review_status"],
                    "review_notes": adv["review_notes"],
                    "recommended_bid_min": adv["recommended_bid_min"],
                    "recommended_bid_max": adv["recommended_bid_max"],
                    "keywords": [k["keyword"] for k in keywords],
                    "categories": [c["category_path"] for c in categories],
                }
            )
        return {"advertisers": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_approved_advertisers error: %r", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch approved advertisers: {str(e)}"
        )


@app.put("/admin/update-review")
async def update_review_status(
    advertiser_id: int,
    review_status: str,
    review_notes: str,
    recommended_bid_min: int,
    recommended_bid_max: int,
    admin_user: dict = Depends(get_current_admin),
):
    try:
        # 1. 심사 상태 업데이트
        await database.execute(
            """
            UPDATE advertiser_reviews 
            SET review_status = :st,
                review_notes = :notes,
                recommended_bid_min = :minb,
                recommended_bid_max = :maxb,
                updated_at = CURRENT_TIMESTAMP
            WHERE advertiser_id = :id
            """,
            {
                "st": review_status,
                "notes": review_notes,
                "minb": recommended_bid_min,
                "maxb": recommended_bid_max,
                "id": advertiser_id,
            },
        )

        # 2. 승인 시 자동 입찰 활성화
        if review_status == "approved":
            await database.execute(
                """
                UPDATE auto_bid_settings 
                SET is_enabled = true,
                    updated_at = CURRENT_TIMESTAMP
                WHERE advertiser_id = :id
                """,
                {"id": advertiser_id},
            )
            logger.info(f"광고주 {advertiser_id} 심사 승인으로 자동 입찰 활성화")

        return {"success": True, "message": "심사 상태가 업데이트되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("update_review_status error: %r", e)
        raise HTTPException(
            status_code=500, detail=f"심사 상태 업데이트 실패: {str(e)}"
        )


@app.patch("/admin/update-advertiser-data")
async def update_advertiser_data(
    advertiser_id: int,
    keywords: List[str],
    categories: List[str],
    admin_user: dict = Depends(get_current_admin),
):
    try:
        await database.execute(
            "DELETE FROM advertiser_keywords WHERE advertiser_id = :id",
            {"id": advertiser_id},
        )
        for kw in keywords:
            await database.execute(
                """
                INSERT INTO advertiser_keywords (advertiser_id, keyword, priority, match_type)
                VALUES (:id, :kw, :priority, :mt)
                """,
                {"id": advertiser_id, "kw": kw, "priority": 1, "mt": "broad"},
            )

        await database.execute(
            "DELETE FROM advertiser_categories WHERE advertiser_id = :id",
            {"id": advertiser_id},
        )
        for path in categories:
            level = len(path.split(" > "))
            await database.execute(
                """
                INSERT INTO advertiser_categories (advertiser_id, category_path, category_level, is_primary)
                VALUES (:id, :path, :level, :is_primary)
                """,
                {
                    "id": advertiser_id,
                    "path": path,
                    "level": level,
                    "is_primary": False,
                },
            )
        return {"success": True, "message": "광고주 데이터가 업데이트되었습니다."}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("update_advertiser_data error: %r", e)
        raise HTTPException(
            status_code=500, detail=f"광고주 데이터 업데이트 실패: {str(e)}"
        )


# ------------------------------------------------------------------------------
# 일반 엔드포인트
# ------------------------------------------------------------------------------
@app.post("/additional-info")
async def submit_additional_info(additional_info: dict):
    try:
        # 필요 시 저장
        return {
            "success": True,
            "message": "추가 정보가 제출되었습니다. 검토 후 연락드리겠습니다.",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("submit_additional_info error: %r", e)
        raise HTTPException(status_code=500, detail=f"추가 정보 제출 실패: {str(e)}")


@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(current_advertiser: dict = Depends(get_current_advertiser)):
    try:
        advertiser_id = current_advertiser["id"]
        logger.info(f"Dashboard request for advertiser_id: {advertiser_id}")

        review_info = await database.fetch_one(
            """
            SELECT review_status FROM advertiser_reviews 
            WHERE advertiser_id = :id
            ORDER BY created_at DESC LIMIT 1
            """,
            {"id": advertiser_id},
        )
        review_status = review_info["review_status"] if review_info else "pending"
        logger.info(f"Review status: {review_status}")

        # 광고주 기본 정보 가져오기 (심사 상태와 관계없이)
        advertiser_info = await database.fetch_one(
            """
            SELECT company_name, website_url, daily_budget
            FROM advertisers WHERE id = :id
            """,
            {"id": advertiser_id},
        )
        logger.info(f"Advertiser info from DB: {advertiser_info}")

        advertiser_info_dict = dict(advertiser_info) if advertiser_info else {}
        advertiser_data = {
            "company_name": advertiser_info_dict.get("company_name", ""),
            "website_url": advertiser_info_dict.get("website_url", ""),
            "daily_budget": float(advertiser_info_dict.get("daily_budget", 10000)),
        }
        logger.info(f"Processed advertiser_data: {advertiser_data}")

        if review_status == "approved":
            # 1) 입찰 요약 (정산 금액 기준)
            bid_summary = await database.fetch_one(
                """
                SELECT 
                    COUNT(DISTINCT abl.id) as total_bids,
                    COUNT(DISTINCT CASE WHEN abl.bid_result = 'won' OR s.verification_decision IS NOT NULL THEN abl.id END) as successful_bids,
                    COALESCE(SUM(COALESCE(s.payable_amount, 0)), 0) as total_spent,
                    COALESCE(AVG(abl.bid_amount), 0) as avg_bid_amount
                FROM auto_bid_logs abl
                LEFT JOIN bids b ON b.advertiser_id = abl.advertiser_id 
                    AND ABS(EXTRACT(EPOCH FROM (b.created_at - abl.created_at))) < 300
                    AND ABS(b.price - abl.bid_amount) < 10
                LEFT JOIN LATERAL (
                    SELECT t.id, t.bid_id
                    FROM transactions t
                    WHERE (t.bid_id = b.id OR (t.advertiser_id = abl.advertiser_id AND t.query_text = abl.search_query))
                    ORDER BY t.created_at DESC
                    LIMIT 1
                ) t ON TRUE
                LEFT JOIN settlements s ON s.trade_id = COALESCE(t.bid_id, t.id)
                WHERE abl.advertiser_id = :id
                  AND abl.created_at >= CURRENT_DATE - INTERVAL '30 days'
                """,
                {"id": advertiser_id},
            )
            # Record 타입을 dict로 변환하여 .get() 메서드 사용
            bid_summary_dict = dict(bid_summary) if bid_summary else {}
            total_bids = int(bid_summary_dict.get("total_bids") or 0)
            successful_bids = int(bid_summary_dict.get("successful_bids") or 0)
            total_spent = int(bid_summary_dict.get("total_spent") or 0)
            average_bid_amount = float(bid_summary_dict.get("avg_bid_amount") or 0)

            # 2) 자동입찰 설정/예산
            auto_bid_settings = await database.fetch_one(
                """
                SELECT is_enabled, daily_budget, max_bid_per_keyword, min_quality_score
                FROM auto_bid_settings WHERE advertiser_id = :id
                """,
                {"id": advertiser_id},
            )
            today_spent_row = await database.fetch_one(
                """
                SELECT COALESCE(SUM(COALESCE(s.payable_amount, 0)), 0) as today_spent
                FROM auto_bid_logs abl
                LEFT JOIN bids b ON b.advertiser_id = abl.advertiser_id 
                    AND ABS(EXTRACT(EPOCH FROM (b.created_at - abl.created_at))) < 300
                    AND ABS(b.price - abl.bid_amount) < 10
                LEFT JOIN LATERAL (
                    SELECT t.id, t.bid_id
                    FROM transactions t
                    WHERE (t.bid_id = b.id OR (t.advertiser_id = abl.advertiser_id AND t.query_text = abl.search_query))
                    ORDER BY t.created_at DESC
                    LIMIT 1
                ) t ON TRUE
                LEFT JOIN settlements s ON s.trade_id = COALESCE(t.bid_id, t.id)
                WHERE abl.advertiser_id = :id
                  AND DATE(abl.created_at) = CURRENT_DATE
                """,
                {"id": advertiser_id},
            )
            daily_budget = float(
                auto_bid_settings["daily_budget"] if auto_bid_settings else 10000
            )
            if auto_bid_settings:
                advertiser_data["daily_budget"] = daily_budget
            # Record 타입을 dict로 변환하여 .get() 메서드 사용
            today_spent_dict = dict(today_spent_row) if today_spent_row else {}
            today_spent = int(today_spent_dict.get("today_spent") or 0)
            budget_usage_percent = (
                (today_spent / daily_budget * 100) if daily_budget > 0 else 0
            )

            # 3) 최근 입찰 (정산 정보 포함)
            # auto_bid_logs를 기준으로 하되, transactions를 통해 정산 정보 연결
            # 최신순으로 정렬하고 중복 제거
            recent_bids_rows = await database.fetch_all(
                """
                WITH ranked_bids AS (
                    SELECT 
                        abl.id,
                        abl.search_query,
                        abl.bid_amount as amount,
                        abl.created_at as timestamp,
                        abl.bid_result as status,
                        b.id as bid_id,
                        COALESCE(s.verification_decision, NULL) as settlement_decision,
                        COALESCE(s.payable_amount, NULL) as settled_amount,
                        COALESCE(dm.v_atf, NULL) as v_atf,
                        COALESCE(dm.clicked, FALSE) as clicked,
                        COALESCE(dm.t_dwell_on_ad_site, 0.0) as t_dwell_on_ad_site,
                        t.id as transaction_id,
                        t.user_id,
                        t.primary_reward,
                        ROW_NUMBER() OVER (PARTITION BY abl.id ORDER BY abl.created_at DESC) as rn
                    FROM auto_bid_logs abl
                    LEFT JOIN bids b ON b.advertiser_id = abl.advertiser_id 
                        AND ABS(EXTRACT(EPOCH FROM (b.created_at - abl.created_at))) < 300
                        AND ABS(b.price - abl.bid_amount) < 10
                    LEFT JOIN LATERAL (
                        SELECT t.id, t.user_id, t.bid_id, t.primary_reward
                        FROM transactions t
                        WHERE (t.bid_id = b.id OR (t.advertiser_id = abl.advertiser_id AND t.query_text = abl.search_query))
                        ORDER BY t.created_at DESC
                        LIMIT 1
                    ) t ON TRUE
                    LEFT JOIN delivery_metrics dm ON dm.trade_id = COALESCE(t.bid_id, t.id)
                    LEFT JOIN settlements s ON s.trade_id = COALESCE(t.bid_id, t.id)
                    WHERE abl.advertiser_id = :id
                )
                SELECT 
                    id, search_query, amount, timestamp, status, bid_id,
                    settlement_decision, settled_amount, v_atf, clicked,
                    t_dwell_on_ad_site, transaction_id, user_id, primary_reward
                FROM ranked_bids
                WHERE rn = 1
                ORDER BY timestamp DESC
                LIMIT 10
                """,
                {"id": advertiser_id},
            )
            recent_bids = []
            for bid in recent_bids_rows:
                settlement_info = None
                # 정산 정보 기본값 설정
                v_atf = float(bid["v_atf"]) if bid["v_atf"] else 0.0
                clicked = bool(bid["clicked"])
                t_dwell_on_ad_site = (
                    float(bid["t_dwell_on_ad_site"])
                    if bid["t_dwell_on_ad_site"]
                    else 0.0
                )
                primary_reward = (
                    float(bid["primary_reward"])
                    if bid["primary_reward"]
                    else float(bid["amount"])  # primary_reward가 없으면 입찰 금액 사용
                )
                
                # 정산 영수증 API와 동일한 재계산 로직 적용
                # delivery_metrics의 실제 데이터를 기반으로 판정을 재계산
                recalculated_decision = None
                if clicked and v_atf >= 0.3:
                    if t_dwell_on_ad_site >= 20.0:
                        recalculated_decision = "PASSED"
                    elif t_dwell_on_ad_site > 3.0:
                        recalculated_decision = "PARTIAL"
                    else:
                        recalculated_decision = "FAILED"
                else:
                    recalculated_decision = "FAILED"
                
                # settlements 테이블의 decision이 있으면 우선 사용, 없으면 재계산된 값 사용
                final_decision = (
                    bid["settlement_decision"]
                    if bid["settlement_decision"]
                    else recalculated_decision
                )
                
                # 재계산된 판정이 더 정확하면 그것을 사용 (settlements의 decision이 없거나, 재계산 결과가 다르면)
                if not bid["settlement_decision"] or (
                    recalculated_decision
                    and recalculated_decision != bid["settlement_decision"]
                ):
                    final_decision = recalculated_decision
                
                # 정산 정보가 있는 경우 (decision이 있거나 delivery_metrics가 있는 경우)
                if final_decision or (v_atf > 0 or clicked or t_dwell_on_ad_site > 0):
                    # 정산 금액 재계산
                    recalculated_amount = 0.0
                    if final_decision == "PASSED":
                        # 전액 지급
                        recalculated_amount = primary_reward
                    elif final_decision == "PARTIAL":
                        # 선형 보상 계산: 3초 = 25%, 20초 = 100%로 선형 보간
                        if t_dwell_on_ad_site <= 3.0:
                            ratio = 0.0
                        elif t_dwell_on_ad_site >= 20.0:
                            ratio = 1.0
                        else:
                            # 공식: 0.25 + 0.75 * (dwell - 3) / (20 - 3)
                            ratio = 0.25 + 0.75 * (t_dwell_on_ad_site - 3.0) / (20.0 - 3.0)
                            ratio = max(0.0, min(1.0, ratio))  # 0~1로 클램프
                        recalculated_amount = primary_reward * ratio
                    else:  # FAILED
                        recalculated_amount = 0.0
                    
                    # settlements 테이블의 금액이 있고 판정이 같으면 그것을 사용, 아니면 재계산된 금액 사용
                    final_amount = (
                        float(bid["settled_amount"])
                        if bid["settled_amount"]
                        and bid["settlement_decision"] == final_decision
                        else recalculated_amount
                    )
                    
                    settlement_info = {
                        "decision": final_decision or "FAILED",
                        "settled_amount": final_amount,
                        "v_atf": v_atf,
                        "clicked": clicked,
                        "t_dwell_on_ad_site": t_dwell_on_ad_site,
                        "trade_id": bid["bid_id"] or str(bid["id"]),
                        "transaction_id": bid["transaction_id"],
                    }

                # 정산 정보가 있으면 상태를 "won"으로 설정
                bid_status = bid["status"].lower() if bid["status"] else "lost"
                if settlement_info and bid_status != "won":
                    bid_status = "won"

                # 정산 금액이 있으면 정산 금액을 사용, 없으면 입찰 금액 사용
                display_amount = (
                    settlement_info["settled_amount"]
                    if settlement_info and settlement_info.get("settled_amount", 0) > 0
                    else bid["amount"]
                )

                recent_bids.append(
                    {
                        "id": str(bid["id"]),
                        "bidId": bid["bid_id"],
                        "auctionId": bid["search_query"] or "N/A",
                        "amount": display_amount,  # 정산 금액 또는 입찰 금액
                        "timestamp": (
                            bid["timestamp"].isoformat() if bid["timestamp"] else ""
                        ),
                        "status": bid_status,
                        "highestBid": bid["amount"],  # 입찰 금액 유지
                        "myBid": bid["amount"],  # 입찰 금액 유지
                        "settlement": settlement_info,
                    }
                )

            # 4) 성과 이력
            perf_rows = await database.fetch_all(
                """
                SELECT DATE_TRUNC('week', created_at) as week_start,
                       COUNT(*) as total_bids,
                       COUNT(CASE WHEN bid_result='won' THEN 1 END) as won_bids
                FROM auto_bid_logs
                WHERE advertiser_id = :id
                  AND created_at >= CURRENT_DATE - INTERVAL '4 weeks'
                GROUP BY DATE_TRUNC('week', created_at)
                ORDER BY week_start DESC
                """,
                {"id": advertiser_id},
            )
            performance_history: List[PerformanceHistory] = []
            for idx, row in enumerate(perf_rows):
                total = int(row["total_bids"] or 0)
                won = int(row["won_bids"] or 0)
                rate = (won / total * 100) if total > 0 else 0
                performance_history.append(
                    PerformanceHistory(name=f"Week {idx+1}", score=int(round(rate, 0)))
                )
            if not performance_history:
                performance_history = [
                    PerformanceHistory(name="Week 1", score=65),
                    PerformanceHistory(name="Week 2", score=70),
                    PerformanceHistory(name="Week 3", score=72),
                    PerformanceHistory(name="Week 4", score=75),
                ]

            additional_stats = {
                "autoBidEnabled": (
                    bool(auto_bid_settings["is_enabled"])
                    if auto_bid_settings
                    else False
                ),
                "dailyBudget": daily_budget,
                "todaySpent": today_spent,
                "budgetUsagePercent": round(budget_usage_percent, 1),
                "maxBidPerKeyword": (
                    int(auto_bid_settings["max_bid_per_keyword"])
                    if auto_bid_settings
                    else 3000
                ),
                "minQualityScore": (
                    int(auto_bid_settings["min_quality_score"])
                    if auto_bid_settings
                    else 50
                ),
                "remainingBudget": daily_budget - today_spent,
            }
        else:
            total_bids = successful_bids = total_spent = 0
            average_bid_amount = 0.0
            recent_bids = []
            performance_history = [
                PerformanceHistory(name="Week 1", score=0),
                PerformanceHistory(name="Week 2", score=0),
                PerformanceHistory(name="Week 3", score=0),
                PerformanceHistory(name="Week 4", score=0),
            ]
            additional_stats = {
                "autoBidEnabled": False,
                "dailyBudget": 0,
                "todaySpent": 0,
                "budgetUsagePercent": 0,
                "maxBidPerKeyword": 0,
                "minQualityScore": 0,
                "remainingBudget": 0,
            }

        bidding_summary = BiddingSummary(
            totalBids=total_bids,
            successfulBids=successful_bids,
            totalSpent=total_spent,
            averageBidAmount=round(average_bid_amount, 2),
        )

        response_data = DashboardResponse(
            biddingSummary=bidding_summary,
            performanceHistory=performance_history,
            recentBids=recent_bids,
            additionalStats=additional_stats,
            advertiserInfo=advertiser_data,
        )
        logger.info(f"Dashboard response data: {response_data}")
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Dashboard error: %r", e)
        raise HTTPException(
            status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@app.get("/health")
async def health_check():
    db_ok = bool(getattr(database, "is_connected", False))
    return {
        "status": "healthy" if db_ok else "degraded",
        "service": "advertiser-service",
        "database": "connected" if db_ok else "disconnected",
        "database_url": SAFE_DB_REFERENCE,
    }


# ------------------------------------------------------------------------------
# 프로필/설정/키워드
# ------------------------------------------------------------------------------
@app.get("/me")
async def get_current_advertiser_info(
    current_advertiser: dict = Depends(get_current_advertiser),
):
    try:
        adv = await database.fetch_one(
            "SELECT id, username, email, company_name, website_url FROM advertisers WHERE id = :id",
            {"id": current_advertiser["id"]},
        )
        if not adv:
            raise HTTPException(status_code=404, detail="광고주를 찾을 수 없습니다")
        return adv
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_current_advertiser_info error: %r", e)
        raise HTTPException(status_code=500, detail=f"광고주 정보 조회 실패: {str(e)}")


@app.put("/update-account-info")
async def update_account_info(
    account_info: dict,
    current_advertiser: dict = Depends(get_current_advertiser),
):
    """광고주 계정 정보 업데이트"""
    try:
        advertiser_id = current_advertiser["id"]

        # 입력 데이터 검증
        company_name = account_info.get("companyName", "").strip()
        website_url = account_info.get("websiteUrl", "").strip()
        daily_budget = account_info.get("dailyBudget", 10000)

        if not company_name:
            raise HTTPException(status_code=400, detail="회사명은 필수입니다")

        if website_url and not validate_url(website_url):
            raise HTTPException(status_code=400, detail="올바른 URL 형식이 아닙니다")

        if not isinstance(daily_budget, (int, float)) or daily_budget < 1000:
            raise HTTPException(
                status_code=400, detail="일일 예산은 1,000원 이상이어야 합니다"
            )

        # 데이터베이스 업데이트
        await database.execute(
            """
            UPDATE advertisers 
            SET company_name = :company_name, 
                website_url = :website_url, 
                daily_budget = :daily_budget,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :id
            """,
            {
                "id": advertiser_id,
                "company_name": company_name,
                "website_url": website_url,
                "daily_budget": float(daily_budget),
            },
        )

        # 자동입찰 설정도 업데이트
        await database.execute(
            """
            UPDATE auto_bid_settings 
            SET daily_budget = :daily_budget,
                updated_at = CURRENT_TIMESTAMP
            WHERE advertiser_id = :id
            """,
            {
                "id": advertiser_id,
                "daily_budget": float(daily_budget),
            },
        )

        return {
            "success": True,
            "message": "계정 정보가 성공적으로 업데이트되었습니다",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Update account info error: %r", e)
        raise HTTPException(
            status_code=500, detail=f"계정 정보 업데이트 실패: {str(e)}"
        )


@app.get("/auto-bid-settings/{advertiser_id}")
async def get_auto_bid_settings(advertiser_id: int):
    try:
        settings = await database.fetch_one(
            """
            SELECT is_enabled, daily_budget, max_bid_per_keyword, 
                   min_quality_score, preferred_categories, excluded_keywords
            FROM auto_bid_settings WHERE advertiser_id = :id
            """,
            {"id": advertiser_id},
        )
        if not settings:
            default_settings = {
                "is_enabled": False,
                "daily_budget": 10000.0,
                "max_bid_per_keyword": 3000,
                "min_quality_score": 50,
                "preferred_categories": [],
                "excluded_keywords": [],
            }
            await database.execute(
                """
                INSERT INTO auto_bid_settings (advertiser_id, is_enabled, daily_budget, max_bid_per_keyword, min_quality_score)
                VALUES (:id, :en, :db, :maxb, :minq)
                """,
                {
                    "id": advertiser_id,
                    "en": False,
                    "db": 10000.0,
                    "maxb": 3000,
                    "minq": 50,
                },
            )
            return default_settings
        return dict(settings)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_auto_bid_settings error: %r", e)
        raise HTTPException(
            status_code=500, detail=f"자동 입찰 설정 조회 실패: {str(e)}"
        )


@app.put("/auto-bid-settings/{advertiser_id}")
async def update_auto_bid_settings(
    advertiser_id: int,
    payload: AutoBidSettingsUpdate,
):
    try:
        excluded_keywords = payload.excluded_keywords or []
        daily_budget = float(payload.daily_budget)
        max_bid_per_keyword = int(payload.max_bid_per_keyword)
        min_quality_score = int(payload.min_quality_score)
        is_enabled = bool(payload.is_enabled)

        await database.execute(
            """
            INSERT INTO auto_bid_settings (
                advertiser_id,
                daily_budget,
                max_bid_per_keyword,
                min_quality_score,
                is_enabled,
                excluded_keywords,
                created_at,
                updated_at
            )
            VALUES (:id, :db, :maxb, :minq, :en, :exk, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (advertiser_id) DO UPDATE
            SET daily_budget = EXCLUDED.daily_budget,
                max_bid_per_keyword = EXCLUDED.max_bid_per_keyword,
                min_quality_score = EXCLUDED.min_quality_score,
                is_enabled = EXCLUDED.is_enabled,
                excluded_keywords = EXCLUDED.excluded_keywords,
                updated_at = CURRENT_TIMESTAMP
            """,
            {
                "id": advertiser_id,
                "db": daily_budget,
                "maxb": max_bid_per_keyword,
                "minq": min_quality_score,
                "en": is_enabled,
                "exk": excluded_keywords,
            },
        )

        updated = await database.fetch_one(
            """
            SELECT advertiser_id, is_enabled, daily_budget, max_bid_per_keyword,
                   min_quality_score, excluded_keywords, updated_at
            FROM auto_bid_settings
            WHERE advertiser_id = :id
            """,
            {"id": advertiser_id},
        )
        if not updated:
            raise HTTPException(
                status_code=500, detail="업데이트 후 설정을 조회하지 못했습니다"
            )

        logger.info(
            "Auto bid settings updated for advertiser_id=%s: budget=%s, max_bid=%s, min_quality=%s, enabled=%s",
            advertiser_id,
            daily_budget,
            max_bid_per_keyword,
            min_quality_score,
            is_enabled,
        )

        return {"success": True, "data": dict(updated)}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("update_auto_bid_settings error: %r", e)
        raise HTTPException(
            status_code=500, detail=f"자동 입찰 설정 업데이트 실패: {str(e)}"
        )


@app.get("/keywords/{advertiser_id}")
async def get_advertiser_keywords(advertiser_id: int):
    try:
        rows = await database.fetch_all(
            """
            SELECT id, keyword, priority, match_type, created_at
            FROM advertiser_keywords WHERE advertiser_id = :id
            ORDER BY priority DESC, created_at ASC
            """,
            {"id": advertiser_id},
        )
        return rows
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_advertiser_keywords error: %r", e)
        raise HTTPException(status_code=500, detail=f"키워드 조회 실패: {str(e)}")


@app.put("/keywords/{advertiser_id}")
async def update_advertiser_keywords(advertiser_id: int, request: Request):
    try:
        try:
            raw_payload = await request.json()
        except Exception as parse_error:
            logger.exception("Failed to parse keywords payload: %r", parse_error)
            raise HTTPException(
                status_code=400, detail="유효한 JSON 형식이 아닙니다."
            ) from parse_error

        if isinstance(raw_payload, dict):
            keywords = raw_payload.get("keywords", [])
        elif isinstance(raw_payload, list):
            keywords = raw_payload
        elif raw_payload is None:
            keywords = []
        else:
            raise HTTPException(
                status_code=400, detail="키워드 데이터 형식이 올바르지 않습니다."
            )

        normalized_keywords: List[Dict[str, Any]] = []
        for item in keywords:
            if not isinstance(item, dict):
                raise HTTPException(
                    status_code=400, detail="각 키워드는 객체 형식이어야 합니다."
                )

            keyword_text = str(item.get("keyword", "")).strip()
            if not keyword_text:
                raise HTTPException(
                    status_code=400, detail="키워드 텍스트는 필수입니다."
                )

            try:
                priority_value = int(item.get("priority", 1))
            except (TypeError, ValueError) as priority_error:
                raise HTTPException(
                    status_code=400, detail="우선순위는 숫자여야 합니다."
                ) from priority_error

            match_type_value = str(item.get("match_type", "broad")).strip().lower()
            if match_type_value not in {"broad", "phrase", "exact"}:
                raise HTTPException(
                    status_code=400,
                    detail="match_type은 broad, phrase, exact 중 하나여야 합니다.",
                )

            normalized_keywords.append(
                {
                    "keyword": keyword_text,
                    "priority": max(1, min(priority_value, 5)),
                    "match_type": match_type_value,
                }
            )

        await database.execute(
            "DELETE FROM advertiser_keywords WHERE advertiser_id = :id",
            {"id": advertiser_id},
        )
        for item in normalized_keywords:
            await database.execute(
                """
                INSERT INTO advertiser_keywords (advertiser_id, keyword, priority, match_type)
                VALUES (:id, :kw, :priority, :mt)
                """,
                {
                    "id": advertiser_id,
                    "kw": item["keyword"],
                    "priority": item["priority"],
                    "mt": item["match_type"],
                },
            )
        return {"success": True, "message": "키워드가 업데이트되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("update_advertiser_keywords error: %r", e)
        raise HTTPException(status_code=500, detail=f"키워드 업데이트 실패: {str(e)}")


@app.get("/categories/{advertiser_id}")
async def get_advertiser_categories(advertiser_id: int):
    """광고주의 카테고리 조회"""
    try:
        rows = await database.fetch_all(
            """
            SELECT id, category_path, category_level, is_primary, created_at
            FROM advertiser_categories WHERE advertiser_id = :id
            ORDER BY is_primary DESC, category_level ASC, category_path ASC
            """,
            {"id": advertiser_id},
        )
        return rows
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_advertiser_categories error: %r", e)
        raise HTTPException(status_code=500, detail=f"카테고리 조회 실패: {str(e)}")


@app.post("/excluded-keywords/{advertiser_id}")
async def update_excluded_keywords(advertiser_id: int, action: str, keyword: str):
    try:
        if action == "add":
            query = """
                UPDATE auto_bid_settings
                SET excluded_keywords = array_append(excluded_keywords, :kw)
                WHERE advertiser_id = :id
            """
        elif action == "remove":
            query = """
                UPDATE auto_bid_settings
                SET excluded_keywords = array_remove(excluded_keywords, :kw)
                WHERE advertiser_id = :id
            """
        else:
            raise HTTPException(status_code=400, detail="잘못된 액션입니다")
        await database.execute(query, {"id": advertiser_id, "kw": keyword})
        return {"success": True, "message": f"제외 키워드가 {action}되었습니다"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("update_excluded_keywords error: %r", e)
        raise HTTPException(
            status_code=500, detail=f"제외 키워드 업데이트 실패: {str(e)}"
        )


# ------------------------------------------------------------------------------
# 입찰 히스토리/분석
# ------------------------------------------------------------------------------
@app.get("/bid-history/{advertiser_id}")
async def get_bid_history(
    advertiser_id: int,
    timeRange: str = "week",
    filter: str = "all",
    resultFilter: str = "all",
):
    try:
        time_conditions = {
            "today": "AND abl.created_at >= CURRENT_DATE",
            "week": "AND abl.created_at >= CURRENT_DATE - INTERVAL '7 days'",
            "month": "AND abl.created_at >= CURRENT_DATE - INTERVAL '30 days'",
        }
        time_condition = time_conditions.get(timeRange, time_conditions["week"])

        if filter not in {"all", "auto", "manual"}:
            logger.warning("Unknown filter '%s' received; defaulting to 'all'", filter)
            filter = "all"
        if filter == "manual":
            logger.info(
                "Bid history requested with filter=manual but manual bids are not logged; returning empty set"
            )
            return []

        result_condition = ""
        if resultFilter in {"won", "lost"}:
            result_condition = f"AND abl.bid_result = '{resultFilter}'"
        elif resultFilter != "all":
            logger.warning(
                "Unknown resultFilter '%s' received; defaulting to 'all'", resultFilter
            )

        rows = await database.fetch_all(
            f"""
            SELECT abl.id,
                   abl.search_query,
                   abl.bid_amount,
                   abl.bid_result,
                   abl.match_score,
                   COALESCE(abl.quality_score, 50) AS quality_score,
                   abl.created_at AS timestamp,
                   TRUE AS is_auto_bid
            FROM auto_bid_logs abl
            WHERE abl.advertiser_id = :id
              {time_condition} {result_condition}
            ORDER BY abl.created_at DESC
            LIMIT 100
            """,
            {"id": advertiser_id},
        )
        history = []
        for row in rows:
            timestamp = row["timestamp"]
            ts_value = (
                timestamp.isoformat()
                if hasattr(timestamp, "isoformat")
                else str(timestamp)
            )
            history.append(
                {
                    "id": str(row["id"]),
                    "searchQuery": row["search_query"],
                    "bidAmount": int(row["bid_amount"]),
                    "result": row["bid_result"],
                    "matchScore": float(row["match_score"]),
                    "qualityScore": (
                        int(row["quality_score"])
                        if row["quality_score"] is not None
                        else 50
                    ),
                    "timestamp": ts_value,
                    "isAutoBid": bool(row["is_auto_bid"]),
                }
            )
        return history
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_bid_history error: %r", e)
        raise HTTPException(status_code=500, detail=f"입찰 내역 조회 실패: {str(e)}")


@app.get("/settlement-receipt/{bid_id}")
async def get_settlement_receipt(
    bid_id: str, current_advertiser: dict = Depends(get_current_advertiser)
):
    """
    개별 입찰에 대한 정산 영수증 조회
    """
    try:
        advertiser_id = current_advertiser["id"]

        # 입찰 정보와 정산 정보 조회
        # 먼저 bids 테이블에서 조회 시도
        settlement_data = await database.fetch_one(
            """
            SELECT 
                b.id as bid_id,
                b.price as bid_amount,
                b.created_at as bid_timestamp,
                a.query_text as search_query,
                t.id as transaction_id,
                t.user_id,
                t.primary_reward,
                COALESCE(s.verification_decision, NULL) as decision,
                COALESCE(s.payable_amount, NULL) as settled_amount,
                COALESCE(s.settled_at, NULL) as settled_at,
                COALESCE(dm.v_atf, NULL) as v_atf,
                COALESCE(dm.clicked, FALSE) as clicked,
                COALESCE(dm.t_dwell_on_ad_site, 0.0) as t_dwell_on_ad_site,
                COALESCE(dm.created_at, NULL) as metrics_created_at
            FROM bids b
            LEFT JOIN auctions a ON a.id = b.auction_id
            LEFT JOIN transactions t ON t.bid_id = b.id
            LEFT JOIN delivery_metrics dm ON dm.trade_id = COALESCE(t.bid_id, t.id)
            LEFT JOIN settlements s ON s.trade_id = COALESCE(t.bid_id, t.id)
            WHERE b.id = :bid_id AND b.advertiser_id = :advertiser_id
            """,
            {"bid_id": bid_id, "advertiser_id": advertiser_id},
        )

        # bids에서 찾지 못한 경우 auto_bid_logs에서 조회
        if not settlement_data:
            try:
                auto_bid_log_id = int(bid_id)
                auto_bid_data = await database.fetch_one(
                    """
                    SELECT 
                        abl.id,
                        abl.bid_amount,
                        abl.created_at as bid_timestamp,
                        abl.search_query,
                        b.id as actual_bid_id,
                        t.id as transaction_id,
                        t.user_id,
                        t.primary_reward,
                        COALESCE(s.verification_decision, NULL) as decision,
                        COALESCE(s.payable_amount, NULL) as settled_amount,
                        COALESCE(s.settled_at, NULL) as settled_at,
                        COALESCE(dm.v_atf, NULL) as v_atf,
                        COALESCE(dm.clicked, FALSE) as clicked,
                        COALESCE(dm.t_dwell_on_ad_site, 0.0) as t_dwell_on_ad_site,
                        COALESCE(dm.created_at, NULL) as metrics_created_at
                    FROM auto_bid_logs abl
                    LEFT JOIN bids b ON b.advertiser_id = abl.advertiser_id 
                        AND ABS(EXTRACT(EPOCH FROM (b.created_at - abl.created_at))) < 300
                        AND ABS(b.price - abl.bid_amount) < 10
                    LEFT JOIN transactions t ON t.bid_id = b.id OR (t.advertiser_id = abl.advertiser_id AND t.query_text = abl.search_query)
                    LEFT JOIN delivery_metrics dm ON dm.trade_id = COALESCE(t.bid_id, t.id)
                    LEFT JOIN settlements s ON s.trade_id = COALESCE(t.bid_id, t.id)
                    WHERE abl.id = :auto_bid_log_id AND abl.advertiser_id = :advertiser_id
                    """,
                    {
                        "auto_bid_log_id": auto_bid_log_id,
                        "advertiser_id": advertiser_id,
                    },
                )
                if auto_bid_data:
                    # Record 타입을 dict로 변환하여 .get() 메서드 사용
                    auto_bid_dict = dict(auto_bid_data) if auto_bid_data else {}
                    # auto_bid_logs 결과를 bids 형식으로 변환
                    settlement_data = {
                        "bid_id": auto_bid_dict.get("actual_bid_id")
                        or str(auto_bid_dict.get("id", "")),
                        "bid_amount": auto_bid_dict.get("bid_amount"),
                        "bid_timestamp": auto_bid_dict.get("bid_timestamp"),
                        "search_query": auto_bid_dict.get("search_query"),
                        "transaction_id": auto_bid_dict.get("transaction_id"),
                        "user_id": auto_bid_dict.get("user_id"),
                        "primary_reward": auto_bid_dict.get("primary_reward"),
                        "decision": auto_bid_dict.get("decision"),
                        "settled_amount": auto_bid_dict.get("settled_amount"),
                        "settled_at": auto_bid_dict.get("settled_at"),
                        "v_atf": auto_bid_dict.get("v_atf"),
                        "clicked": auto_bid_dict.get("clicked"),
                        "t_dwell_on_ad_site": auto_bid_dict.get("t_dwell_on_ad_site"),
                        "metrics_created_at": auto_bid_dict.get("metrics_created_at"),
                    }
            except (ValueError, TypeError):
                pass

        if not settlement_data:
            raise HTTPException(status_code=404, detail="입찰 정보를 찾을 수 없습니다.")

        # 사용자 정보 익명화
        user_id = settlement_data["user_id"]
        anonymized_user_id = f"User_#{hash(str(user_id)) % 10000}" if user_id else None

        result = {
            "bid_id": settlement_data["bid_id"],
            "search_query": settlement_data["search_query"] or "N/A",
            "bid_amount": int(settlement_data["bid_amount"]),
            "bid_timestamp": (
                settlement_data["bid_timestamp"].isoformat()
                if settlement_data["bid_timestamp"]
                else None
            ),
            "transaction_id": settlement_data["transaction_id"],
            "user_id": anonymized_user_id,
            "primary_reward": (
                float(settlement_data["primary_reward"])
                if settlement_data["primary_reward"]
                else 0.0
            ),
            "settlement": None,
        }

        # 정산 정보가 있는 경우
        # delivery_metrics의 실제 데이터를 기반으로 판정을 재계산
        v_atf = float(settlement_data["v_atf"]) if settlement_data["v_atf"] else 0.0
        clicked = bool(settlement_data["clicked"])
        t_dwell_on_ad_site = (
            float(settlement_data["t_dwell_on_ad_site"])
            if settlement_data["t_dwell_on_ad_site"]
            else 0.0
        )
        primary_reward = (
            float(settlement_data["primary_reward"])
            if settlement_data["primary_reward"]
            else 0.0
        )

        # 실제 SLA 지표를 기반으로 판정 재계산
        recalculated_decision = None
        if clicked and v_atf >= 0.3:
            if t_dwell_on_ad_site >= 20.0:
                recalculated_decision = "PASSED"
            elif t_dwell_on_ad_site > 3.0:
                recalculated_decision = "PARTIAL"
            else:
                recalculated_decision = "FAILED"
        else:
            recalculated_decision = "FAILED"

        # settlements 테이블의 decision이 있으면 우선 사용, 없으면 재계산된 값 사용
        final_decision = (
            settlement_data["decision"]
            if settlement_data["decision"]
            else recalculated_decision
        )

        # 재계산된 판정이 더 정확하면 그것을 사용 (settlements의 decision이 없거나, 재계산 결과가 다르면)
        if not settlement_data["decision"] or (
            recalculated_decision
            and recalculated_decision != settlement_data["decision"]
        ):
            final_decision = recalculated_decision

        # 정산 금액 재계산
        recalculated_amount = 0.0
        if final_decision == "PASSED":
            # 전액 지급
            recalculated_amount = primary_reward
        elif final_decision == "PARTIAL":
            # 선형 보상 계산: 3초 = 25%, 20초 = 100%로 선형 보간
            if t_dwell_on_ad_site <= 3.0:
                ratio = 0.0
            elif t_dwell_on_ad_site >= 20.0:
                ratio = 1.0
            else:
                # 공식: 0.25 + 0.75 * (dwell - 3) / (20 - 3)
                ratio = 0.25 + 0.75 * (t_dwell_on_ad_site - 3.0) / (20.0 - 3.0)
                ratio = max(0.0, min(1.0, ratio))  # 0~1로 클램프
            recalculated_amount = primary_reward * ratio
        else:  # FAILED
            recalculated_amount = 0.0

        # settlements 테이블의 금액이 있고 판정이 같으면 그것을 사용, 아니면 재계산된 금액 사용
        final_amount = (
            float(settlement_data["settled_amount"])
            if settlement_data["settled_amount"]
            and settlement_data["decision"] == final_decision
            else recalculated_amount
        )

        if final_decision:
            result["settlement"] = {
                "decision": final_decision,
                "settled_amount": final_amount,
                "settled_at": (
                    settlement_data["settled_at"].isoformat()
                    if settlement_data["settled_at"]
                    else None
                ),
                "metrics": {
                    "v_atf": v_atf,
                    "clicked": clicked,
                    "t_dwell_on_ad_site": t_dwell_on_ad_site,
                    "created_at": (
                        settlement_data["metrics_created_at"].isoformat()
                        if settlement_data["metrics_created_at"]
                        else None
                    ),
                },
            }

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_settlement_receipt error: %r", e)
        raise HTTPException(status_code=500, detail=f"정산 영수증 조회 실패: {str(e)}")


@app.get("/analytics/auto-bidding/{advertiser_id}")
async def get_auto_bidding_analytics(advertiser_id: int, timeRange: str = "week"):
    try:
        tc_map = {
            "day": "AND created_at >= CURRENT_DATE",
            "week": "AND created_at >= CURRENT_DATE - INTERVAL '7 days'",
            "month": "AND created_at >= CURRENT_DATE - INTERVAL '30 days'",
        }
        time_condition = tc_map.get(timeRange, tc_map["week"])

        time_series = await database.fetch_all(
            f"""
            SELECT DATE(created_at) as date,
                   COUNT(*) as total_bids,
                   AVG(CASE WHEN bid_result='won' THEN 1.0 ELSE 0.0 END)*100 as success_rate,
                   AVG(bid_amount) as avg_bid_amount,
                   SUM(CASE WHEN bid_result='won' THEN bid_amount ELSE 0 END) as total_spent
            FROM auto_bid_logs
            WHERE advertiser_id = :id {time_condition}
            GROUP BY DATE(created_at)
            ORDER BY date DESC
            """,
            {"id": advertiser_id},
        )

        keyword_performance = await database.fetch_all(
            f"""
            SELECT search_query as keyword,
                   COUNT(*) as total_bids,
                   AVG(CASE WHEN bid_result='won' THEN 1.0 ELSE 0.0 END)*100 as success_rate,
                   AVG(bid_amount) as avg_bid_amount,
                   (AVG(CASE WHEN bid_result='won' THEN 1.0 ELSE 0.0 END)*100)*2 as roi
            FROM auto_bid_logs
            WHERE advertiser_id = :id {time_condition}
            GROUP BY search_query
            HAVING COUNT(*) >= 3
            ORDER BY success_rate DESC
            LIMIT 10
            """,
            {"id": advertiser_id},
        )

        match_type_analysis = await database.fetch_all(
            f"""
            SELECT match_type,
                   COUNT(*) as total_bids,
                   AVG(CASE WHEN bid_result='won' THEN 1.0 ELSE 0.0 END)*100 as success_rate,
                   AVG(bid_amount) as avg_bid_amount
            FROM auto_bid_logs
            WHERE advertiser_id = :id {time_condition}
            GROUP BY match_type
            ORDER BY success_rate DESC
            """,
            {"id": advertiser_id},
        )

        optimization_suggestions = await generate_optimization_suggestions(
            advertiser_id, time_condition
        )
        performance_comparison = await get_performance_comparison(
            advertiser_id, time_condition
        )

        return {
            "timeSeries": time_series,
            "keywordPerformance": keyword_performance,
            "matchTypeAnalysis": match_type_analysis,
            "optimizationSuggestions": optimization_suggestions,
            "performanceComparison": performance_comparison,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_auto_bidding_analytics error: %r", e)
        raise HTTPException(status_code=500, detail=f"자동 입찰 분석 실패: {str(e)}")


@app.get("/optimization/suggestions/{advertiser_id}")
async def get_optimization_suggestions_endpoint(advertiser_id: int):
    try:
        time_condition = "AND created_at >= CURRENT_DATE - INTERVAL '7 days'"
        suggestions = await generate_optimization_suggestions(
            advertiser_id, time_condition
        )
        return {
            "suggestions": suggestions,
            "generated_at": datetime.utcnow().isoformat(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_optimization_suggestions_endpoint error: %r", e)
        raise HTTPException(status_code=500, detail=f"최적화 제안 조회 실패: {str(e)}")


@app.get("/performance/comparison/{advertiser_id}")
async def get_performance_comparison_endpoint(
    advertiser_id: int, timeRange: str = "week"
):
    try:
        tc_map = {
            "day": "AND created_at >= CURRENT_DATE",
            "week": "AND created_at >= CURRENT_DATE - INTERVAL '7 days'",
            "month": "AND created_at >= CURRENT_DATE - INTERVAL '30 days'",
        }
        time_condition = tc_map.get(timeRange, tc_map["week"])
        comparison = await get_performance_comparison(advertiser_id, time_condition)
        return {"comparison": comparison, "timeRange": timeRange}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("get_performance_comparison_endpoint error: %r", e)
        raise HTTPException(status_code=500, detail=f"성과 비교 조회 실패: {str(e)}")


async def generate_optimization_suggestions(advertiser_id: int, time_condition: str):
    suggestions = []
    try:
        keyword_data = await database.fetch_all(
            f"""
            SELECT search_query,
                   COUNT(*) as bid_count,
                   AVG(CASE WHEN bid_result='won' THEN 1.0 ELSE 0.0 END)*100 as success_rate,
                   AVG(bid_amount) as avg_bid,
                   AVG(match_score) as avg_match_score
            FROM auto_bid_logs
            WHERE advertiser_id = :id {time_condition}
            GROUP BY search_query
            HAVING COUNT(*) >= 2
            """,
            {"id": advertiser_id},
        )
        for row in keyword_data:
            if row["success_rate"] < 30:
                suggestions.append(
                    {
                        "type": "keyword",
                        "priority": "high",
                        "title": f"키워드 '{row['search_query']}' 성과 개선 필요",
                        "description": f"성공률 {row['success_rate']:.1f}%로 낮습니다. 매칭 타입 조정/입찰가 하향을 검토하세요.",
                        "expectedImpact": "성공률 20% 향상",
                        "action": "키워드 설정 조정",
                    }
                )
            elif row["success_rate"] < 50:
                suggestions.append(
                    {
                        "type": "keyword",
                        "priority": "medium",
                        "title": f"키워드 '{row['search_query']}' 최적화 기회",
                        "description": f"성공률 {row['success_rate']:.1f}%. 입찰가 미세 조정 권장.",
                        "expectedImpact": "성공률 10% 향상",
                        "action": "입찰가 조정",
                    }
                )

        bid_data = await database.fetch_one(
            f"""
            SELECT 
                AVG(bid_amount) as avg_bid,
                AVG(CASE WHEN bid_result='won' THEN bid_amount ELSE NULL END) as avg_winning_bid,
                AVG(CASE WHEN bid_result='lost' THEN bid_amount ELSE NULL END) as avg_losing_bid
            FROM auto_bid_logs
            WHERE advertiser_id = :id {time_condition}
            """,
            {"id": advertiser_id},
        )
        if bid_data and bid_data["avg_winning_bid"] and bid_data["avg_losing_bid"]:
            if bid_data["avg_winning_bid"] > bid_data["avg_losing_bid"] * 1.5:
                suggestions.append(
                    {
                        "type": "bid",
                        "priority": "high",
                        "title": "입찰가 최적화 필요",
                        "description": "성공 입찰가가 실패 입찰가보다 50% 이상 높음. 낮춰 효율 개선을 검토하세요.",
                        "expectedImpact": "비용 30% 절감",
                        "action": "입찰가 하향",
                    }
                )

        time_data = await database.fetch_all(
            f"""
            SELECT EXTRACT(HOUR FROM created_at) as hour,
                   COUNT(*) as bid_count,
                   AVG(CASE WHEN bid_result='won' THEN 1.0 ELSE 0.0 END)*100 as success_rate
            FROM auto_bid_logs
            WHERE advertiser_id = :id {time_condition}
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY success_rate DESC
            """,
            {"id": advertiser_id},
        )
        if time_data:
            best = time_data[0]
            worst = time_data[-1]
            diff = best["success_rate"] - worst["success_rate"]
            if diff > 30:
                suggestions.append(
                    {
                        "type": "timing",
                        "priority": "medium",
                        "title": "시간대별 입찰 최적화",
                        "description": f"{int(best['hour'])}시대가 {int(worst['hour'])}시대보다 {diff:.1f}% 높습니다.",
                        "expectedImpact": "성공률 15% 향상",
                        "action": "시간대 설정 조정",
                    }
                )

        budget_data = await database.fetch_one(
            f"""
            SELECT SUM(CASE WHEN bid_result='won' THEN bid_amount ELSE 0 END) as total_spent,
                   COUNT(CASE WHEN bid_result='won' THEN 1 END) as won_bids,
                   COUNT(*) as total_bids
            FROM auto_bid_logs
            WHERE advertiser_id = :id {time_condition}
            """,
            {"id": advertiser_id},
        )
        if budget_data and budget_data["total_bids"] > 0:
            success_rate = (budget_data["won_bids"] / budget_data["total_bids"]) * 100
            if success_rate < 40:
                suggestions.append(
                    {
                        "type": "budget",
                        "priority": "high",
                        "title": "예산 효율성 개선 필요",
                        "description": f"전체 성공률 {success_rate:.1f}%. 키워드별 예산 재분배를 검토하세요.",
                        "expectedImpact": "ROI 25% 향상",
                        "action": "예산 재분배",
                    }
                )
        return suggestions[:5]
    except Exception as e:
        logger.exception("generate_optimization_suggestions error: %r", e)
        return []


async def get_performance_comparison(advertiser_id: int, time_condition: str):
    try:
        auto_perf = await database.fetch_one(
            f"""
            SELECT COUNT(*) as total_bids,
                   AVG(CASE WHEN bid_result='won' THEN 1.0 ELSE 0.0 END)*100 as success_rate,
                   AVG(bid_amount) as avg_bid_amount,
                   SUM(CASE WHEN bid_result='won' THEN bid_amount ELSE 0 END) as total_spent
            FROM auto_bid_logs
            WHERE advertiser_id = :id {time_condition}
            """,
            {"id": advertiser_id},
        )
        manual_perf = await database.fetch_one(
            f"""
            SELECT COUNT(*) as total_bids,
                   AVG(CASE WHEN result='won' THEN 1.0 ELSE 0.0 END)*100 as success_rate,
                   AVG(price) as avg_bid_amount,
                   SUM(CASE WHEN result='won' THEN price ELSE 0 END) as total_spent
            FROM bids b
            JOIN auctions a ON b.auction_id = a.id
            WHERE b.buyer_name = (SELECT company_name FROM advertisers WHERE id = :id)
              AND COALESCE(b.is_auto_bid,false) = false {time_condition.replace('created_at','b.created_at')}
            """,
            {"id": advertiser_id},
        )
        comparison = []
        if auto_perf and manual_perf:
            a_s, m_s = auto_perf["success_rate"] or 0, manual_perf["success_rate"] or 0
            comparison.append(
                {
                    "metric": "성공률",
                    "autoBid": round(a_s, 1),
                    "manualBid": round(m_s, 1),
                    "improvement": round((a_s - m_s) if m_s > 0 else 0, 1),
                }
            )
            a_avg, m_avg = (
                auto_perf["avg_bid_amount"] or 0,
                manual_perf["avg_bid_amount"] or 0,
            )
            comparison.append(
                {
                    "metric": "평균 입찰가",
                    "autoBid": round(a_avg),
                    "manualBid": round(m_avg),
                    "improvement": round(
                        ((m_avg - a_avg) / m_avg * 100) if m_avg > 0 else 0, 1
                    ),
                }
            )
            a_sp, m_sp = auto_perf["total_spent"] or 0, manual_perf["total_spent"] or 0
            comparison.append(
                {
                    "metric": "총 지출",
                    "autoBid": round(a_sp),
                    "manualBid": round(m_sp),
                    "improvement": round(
                        ((m_sp - a_sp) / m_sp * 100) if m_sp > 0 else 0, 1
                    ),
                }
            )
            a_tb, m_tb = auto_perf["total_bids"] or 0, manual_perf["total_bids"] or 0
            comparison.append(
                {
                    "metric": "입찰 횟수",
                    "autoBid": a_tb,
                    "manualBid": m_tb,
                    "improvement": round(
                        ((a_tb - m_tb) / m_tb * 100) if m_tb > 0 else 0, 1
                    ),
                }
            )
        return comparison
    except Exception as e:
        logger.exception("get_performance_comparison error: %r", e)
        return []


# ------------------------------------------------------------------------------
# 자동 입찰 (최적화/실행)
# ------------------------------------------------------------------------------
@app.post("/auto-bid/optimize")
async def optimize_bid(
    current_advertiser: dict = Depends(get_current_advertiser),
    search_query: Optional[str] = None,
    quality_score: Optional[int] = None,
    match_type: str = "broad",
    match_score: float = 0.5,
    competitor_count: int = 0,
    budget_remaining: float = 10000.0,
):
    try:
        advertiser_id = current_advertiser["id"]
        now = datetime.utcnow()
        time_of_day = now.hour
        day_of_week = now.weekday()

        historical = await database.fetch_one(
            """
            SELECT AVG(CASE WHEN bid_result='won' THEN 1.0 ELSE 0.0 END)*100 as historical_success_rate,
                   AVG(CASE WHEN bid_result='won' THEN bid_amount ELSE NULL END) as avg_winning_bid
            FROM auto_bid_logs
            WHERE advertiser_id = :id
              AND created_at >= CURRENT_DATE - INTERVAL '30 days'
            """,
            {"id": advertiser_id},
        )
        # Record 타입을 dict로 변환하여 .get() 메서드 사용
        historical_dict = dict(historical) if historical else {}
        historical_success_rate = float(
            historical_dict.get("historical_success_rate") or 50.0
        )
        avg_winning_bid = float(historical_dict.get("avg_winning_bid") or 1000.0)

        context = BidContext(
            search_query=search_query or "기본 검색",
            quality_score=quality_score or 50,
            match_type=parse_match_type(match_type),
            match_score=match_score,
            competitor_count=competitor_count,
            time_of_day=time_of_day,
            day_of_week=day_of_week,
            historical_success_rate=historical_success_rate,
            avg_winning_bid=avg_winning_bid,
            budget_remaining=budget_remaining,
        )
        optimizer = AutoBidOptimizer(database)
        res: OptimizationResult = await optimizer.get_optimal_bid(
            advertiser_id, context
        )
        return {
            "recommended_bid": res.recommended_bid,
            "confidence_score": res.confidence_score,
            "reasoning": res.reasoning,
            "expected_success_rate": res.expected_success_rate,
            "cost_efficiency": res.cost_efficiency,
            "context": {
                "search_query": context.search_query,
                "quality_score": context.quality_score,
                "match_type": context.match_type.value,
                "match_score": context.match_score,
                "competitor_count": context.competitor_count,
                "time_of_day": context.time_of_day,
                "budget_remaining": context.budget_remaining,
                # ✅ 누락분 포함 (실행 단계에서 사용)
                "historical_success_rate": historical_success_rate,
                "avg_winning_bid": avg_winning_bid,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("optimize_bid error: %r", e)
        raise HTTPException(status_code=500, detail=f"입찰 최적화 실패: {str(e)}")


@app.post("/auto-bid/execute")
async def execute_auto_bid(
    current_advertiser: dict = Depends(get_current_advertiser),
    search_query: Optional[str] = None,
    quality_score: Optional[int] = None,
    match_type: str = "broad",
    match_score: float = 0.5,
    competitor_count: int = 0,
):
    try:
        advertiser_id = current_advertiser["id"]
        settings = await database.fetch_one(
            """
            SELECT is_enabled, daily_budget, max_bid_per_keyword, min_quality_score
            FROM auto_bid_settings WHERE advertiser_id = :id
            """,
            {"id": advertiser_id},
        )
        if not settings or not settings["is_enabled"]:
            raise HTTPException(
                status_code=400, detail="자동 입찰이 비활성화되어 있습니다."
            )
        if quality_score is None or quality_score < settings["min_quality_score"]:
            raise HTTPException(
                status_code=400, detail="품질 점수가 최소 기준을 만족하지 않습니다."
            )

        budget_row = await database.fetch_one(
            """
            SELECT abs.daily_budget,
                   COALESCE(SUM(CASE WHEN abl.bid_result='won' THEN abl.bid_amount ELSE 0 END),0) as spent_today
            FROM auto_bid_settings abs
            LEFT JOIN auto_bid_logs abl ON abs.advertiser_id = abl.advertiser_id AND DATE(abl.created_at)=CURRENT_DATE
            WHERE abs.advertiser_id = :id
            GROUP BY abs.daily_budget
            """,
            {"id": advertiser_id},
        )
        if not budget_row:
            raise HTTPException(status_code=400, detail="예산 정보를 찾을 수 없습니다.")
        budget_remaining = float(budget_row["daily_budget"]) - float(
            budget_row["spent_today"]
        )
        if budget_remaining <= 0:
            raise HTTPException(status_code=400, detail="일일 예산이 소진되었습니다.")

        opt = await optimize_bid(
            current_advertiser=current_advertiser,
            search_query=search_query,
            quality_score=quality_score,
            match_type=match_type,
            match_score=match_score,
            competitor_count=competitor_count,
            budget_remaining=budget_remaining,
        )
        recommended_bid = float(opt["recommended_bid"])
        if recommended_bid > float(settings["max_bid_per_keyword"]):
            recommended_bid = float(settings["max_bid_per_keyword"])
        if recommended_bid > budget_remaining:
            recommended_bid = budget_remaining

        bid_result = await _execute_bid_in_auction(
            advertiser_id, search_query or "기본 검색", int(recommended_bid)
        )

        # 로그/모델 업데이트
        now = datetime.utcnow()
        context = BidContext(
            search_query=search_query or "기본 검색",
            quality_score=quality_score or 50,
            match_type=parse_match_type(match_type),
            match_score=match_score,
            competitor_count=competitor_count,
            time_of_day=now.hour,
            day_of_week=now.weekday(),
            historical_success_rate=float(
                opt.get("context", {}).get("historical_success_rate", 50.0)
            ),
            avg_winning_bid=float(
                opt.get("context", {}).get("avg_winning_bid", 1000.0)
            ),
            budget_remaining=budget_remaining,
        )
        optimizer = AutoBidOptimizer(database)
        await optimizer.update_model(
            advertiser_id, BidResult(bid_result), int(recommended_bid), context
        )

        return {
            "success": True,
            "bid_amount": int(recommended_bid),
            "bid_result": bid_result,
            "confidence_score": opt["confidence_score"],
            "reasoning": opt["reasoning"],
            "budget_remaining": budget_remaining - recommended_bid,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("execute_auto_bid error: %r", e)
        raise HTTPException(status_code=500, detail=f"자동 입찰 실행 실패: {str(e)}")


async def _execute_bid_in_auction(
    advertiser_id: int, search_query: str, bid_amount: int
) -> str:
    """경매 서비스와의 연동 시뮬레이션"""
    try:
        return "won" if random.random() < 0.6 else "lost"
    except Exception as e:
        logger.warning("execute bid in auction error: %r", e)
        return "timeout"


# ------------------------------------------------------------------------------
# 카테고리 목록
# ------------------------------------------------------------------------------
@app.get("/business-categories")
async def get_business_categories():
    try:
        rows = await database.fetch_all(
            """
            SELECT id, parent_id, name, path, level, is_active, sort_order, created_at
            FROM business_categories
            WHERE is_active = true
            ORDER BY level, sort_order, name
            """
        )
        if rows:
            return rows
        # fallback 기본 목록
        return [
            {
                "id": 1,
                "parent_id": None,
                "name": "전자제품",
                "path": "electronics",
                "level": 1,
                "is_active": True,
                "sort_order": 1,
            },
            {
                "id": 2,
                "parent_id": None,
                "name": "의류",
                "path": "clothing",
                "level": 1,
                "is_active": True,
                "sort_order": 2,
            },
            {
                "id": 3,
                "parent_id": None,
                "name": "식품",
                "path": "food",
                "level": 1,
                "is_active": True,
                "sort_order": 3,
            },
            {
                "id": 4,
                "parent_id": None,
                "name": "가구",
                "path": "furniture",
                "level": 1,
                "is_active": True,
                "sort_order": 4,
            },
            {
                "id": 5,
                "parent_id": None,
                "name": "스포츠",
                "path": "sports",
                "level": 1,
                "is_active": True,
                "sort_order": 5,
            },
        ]
    except Exception as e:
        logger.exception("get_business_categories error: %r", e)
        return [
            {
                "id": 1,
                "parent_id": None,
                "name": "전자제품",
                "path": "electronics",
                "level": 1,
                "is_active": True,
                "sort_order": 1,
            },
            {
                "id": 2,
                "parent_id": None,
                "name": "의류",
                "path": "clothing",
                "level": 1,
                "is_active": True,
                "sort_order": 2,
            },
            {
                "id": 3,
                "parent_id": None,
                "name": "식품",
                "path": "food",
                "level": 1,
                "is_active": True,
                "sort_order": 3,
            },
            {
                "id": 4,
                "parent_id": None,
                "name": "가구",
                "path": "furniture",
                "level": 1,
                "is_active": True,
                "sort_order": 4,
            },
            {
                "id": 5,
                "parent_id": None,
                "name": "스포츠",
                "path": "sports",
                "level": 1,
                "is_active": True,
                "sort_order": 5,
            },
        ]


# ------------------------------------------------------------------------------
# 삭제(관리자)
# ------------------------------------------------------------------------------
@app.delete("/admin/delete-advertiser/{advertiser_id}")
async def delete_advertiser(
    advertiser_id: int, admin_user: dict = Depends(get_current_admin)
):
    try:
        status_row = await database.fetch_val(
            "SELECT review_status FROM advertiser_reviews WHERE advertiser_id = :id",
            {"id": advertiser_id},
        )
        if not status_row:
            raise HTTPException(status_code=404, detail="Advertiser not found")
        if status_row != "rejected":
            raise HTTPException(
                status_code=400, detail="Only rejected advertisers can be deleted"
            )

        async with database.transaction():
            await database.execute(
                "DELETE FROM advertisers WHERE id = :id", {"id": advertiser_id}
            )
        return {"success": True, "message": "Advertiser deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("delete_advertiser error: %r", e)
        raise HTTPException(
            status_code=500, detail=f"Failed to delete advertiser: {str(e)}"
        )


# ------------------------------------------------------------------------------
# 로컬 실행
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8007)
