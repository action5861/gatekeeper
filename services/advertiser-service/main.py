import math
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Literal
from dataclasses import dataclass
from enum import Enum
import re
import html

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator, Field
import httpx
import os
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# 데이터베이스 연동 추가
from database import (
    database,
    connect_to_database,
    disconnect_from_database,
)

# AutoBidOptimizer import
from auto_bid_optimizer import (
    AutoBidOptimizer,
    BidContext,
    MatchType,
    BidResult,
    OptimizationResult,
)

# Load environment variables
load_dotenv()

app = FastAPI(title="Advertiser Service", version="1.0.0")


# 🚀 시작 이벤트
@app.on_event("startup")
async def startup():
    await connect_to_database()

    # 카테고리 데이터 확인 및 초기화
    try:
        # 카테고리 데이터가 있는지 확인
        category_count = await database.fetch_val(
            "SELECT COUNT(*) FROM business_categories"
        )

        if category_count == 0:
            print("카테고리 데이터가 없습니다. 기본 카테고리를 삽입합니다...")

            # 기본 카테고리 데이터 삽입
            await database.execute_many(
                """
                INSERT INTO business_categories (name, path, level, sort_order) 
                VALUES (:name, :path, :level, :sort_order)
                """,
                [
                    {
                        "name": "전자제품",
                        "path": "전자제품",
                        "level": 1,
                        "sort_order": 1,
                    },
                    {
                        "name": "패션/뷰티",
                        "path": "패션/뷰티",
                        "level": 1,
                        "sort_order": 2,
                    },
                    {
                        "name": "생활/건강",
                        "path": "생활/건강",
                        "level": 1,
                        "sort_order": 3,
                    },
                    {
                        "name": "식품/음료",
                        "path": "식품/음료",
                        "level": 1,
                        "sort_order": 4,
                    },
                    {
                        "name": "스포츠/레저/자동차",
                        "path": "스포츠/레저/자동차",
                        "level": 1,
                        "sort_order": 5,
                    },
                    {
                        "name": "유아/아동",
                        "path": "유아/아동",
                        "level": 1,
                        "sort_order": 6,
                    },
                    {
                        "name": "여행/문화",
                        "path": "여행/문화",
                        "level": 1,
                        "sort_order": 7,
                    },
                    {
                        "name": "반려동물",
                        "path": "반려동물",
                        "level": 1,
                        "sort_order": 8,
                    },
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
                ],
            )

            print(f"기본 카테고리 {category_count}개가 삽입되었습니다.")
        else:
            print(f"데이터베이스에 {category_count}개의 카테고리가 있습니다.")

    except Exception as e:
        print(f"카테고리 데이터 초기화 중 오류 발생: {e}")
        print("서비스는 계속 실행됩니다.")


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

# Security configuration
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# bcrypt 버전 호환성을 위한 설정 수정
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception as e:
    print(f"Bcrypt 초기화 오류: {e}")
    # 대안으로 sha256_crypt 사용
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

security = HTTPBearer()


# 입력값 검증 함수들
def sanitize_input(value: str) -> str:
    """XSS 방지를 위한 입력값 이스케이핑"""
    if not isinstance(value, str):
        return str(value)
    return html.escape(value.strip())


def validate_password_strength(password: str) -> bool:
    """비밀번호 강도 검증"""
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


def validate_sql_injection(value: str) -> bool:
    """SQL Injection 방지를 위한 검증"""
    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(\b(OR|AND)\b\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\b\s+['\"]?\w+['\"]?\s*=\s*['\"]?\w+['\"]?)",
        r"(--|#|/\*|\*/)",
        r"(\b(WAITFOR|DELAY)\b)",
        r"(\b(BENCHMARK|SLEEP)\b)",
    ]

    value_upper = value.upper()
    for pattern in sql_patterns:
        if re.search(pattern, value_upper, re.IGNORECASE):
            return False
    return True


def validate_url(url: str) -> bool:
    """URL 형식 검증"""
    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain...
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )
    return bool(url_pattern.match(url))


# Pydantic 모델
class PerformanceHistory(BaseModel):
    name: str = Field(..., max_length=100)
    score: int = Field(..., ge=0, le=100)

    @validator("name")
    def validate_name(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("이름에 허용되지 않는 문자가 포함되어 있습니다")
        return v


class BiddingSummary(BaseModel):
    totalBids: int = Field(..., ge=0)
    successfulBids: int = Field(..., ge=0)
    totalSpent: int = Field(..., ge=0)
    averageBidAmount: float = Field(..., ge=0)


class DashboardResponse(BaseModel):
    biddingSummary: BiddingSummary
    performanceHistory: List[PerformanceHistory]
    recentBids: List[dict]
    additionalStats: Optional[dict] = None


class BusinessSetupData(BaseModel):
    websiteUrl: str = Field(..., max_length=500)
    keywords: List[str] = Field(..., description="키워드 목록")
    categories: List[int] = Field(..., description="카테고리 ID 목록")
    dailyBudget: int = Field(..., ge=1000, le=10000000)
    bidRange: dict

    @validator("websiteUrl")
    def validate_website_url(cls, v):
        v = sanitize_input(v)
        if not validate_url(v):
            raise ValueError("올바른 URL 형식이 아닙니다")
        if not validate_sql_injection(v):
            raise ValueError("웹사이트 URL에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("keywords")
    def validate_keywords(cls, v):
        if len(v) > 100:
            raise ValueError("키워드는 최대 100개까지 입력 가능합니다")
        for keyword in v:
            keyword = sanitize_input(keyword)
            if len(keyword) > 50:
                raise ValueError("키워드는 최대 50자까지 입력 가능합니다")
            if not validate_sql_injection(keyword):
                raise ValueError("키워드에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("categories")
    def validate_categories(cls, v):
        if len(v) > 50:
            raise ValueError("카테고리는 최대 50개까지 선택 가능합니다")
        for category_id in v:
            if not isinstance(category_id, int) or category_id < 1:
                raise ValueError("올바른 카테고리 ID가 아닙니다")
        return v


class AdvertiserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="사용자명")
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=8, max_length=128, description="비밀번호")
    company_name: str = Field(..., min_length=2, max_length=100, description="회사명")
    business_setup: Optional[BusinessSetupData] = None

    @validator("username")
    def validate_username(cls, v):
        v = sanitize_input(v)
        if not re.match(r"^[a-zA-Z0-9_가-힣]+$", v):
            raise ValueError(
                "사용자명은 영문, 숫자, 언더스코어, 한글만 사용 가능합니다"
            )
        if not validate_sql_injection(v):
            raise ValueError("사용자명에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("email")
    def validate_email(cls, v):
        v = sanitize_input(v.lower())
        if not validate_sql_injection(v):
            raise ValueError("이메일에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("password")
    def validate_password(cls, v):
        if not validate_password_strength(v):
            raise ValueError(
                "비밀번호는 최소 8자 이상이며, 대문자, 소문자, 숫자, 특수문자를 포함해야 합니다"
            )
        if not validate_sql_injection(v):
            raise ValueError("비밀번호에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("company_name")
    def validate_company_name(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("회사명에 허용되지 않는 문자가 포함되어 있습니다")
        return v


class AdvertiserLogin(BaseModel):
    username: str = Field(..., description="사용자명 또는 이메일")
    password: str = Field(..., description="비밀번호")

    @validator("username")
    def validate_username(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("사용자명에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("password")
    def validate_password(cls, v):
        if not validate_sql_injection(v):
            raise ValueError("비밀번호에 허용되지 않는 문자가 포함되어 있습니다")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


# 보안 함수들
def verify_password(plain_password, hashed_password):
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # 개발 환경에서 평문 비교 fallback
        return plain_password == hashed_password


def get_password_hash(password):
    try:
        return pwd_context.hash(password)
    except Exception:
        # 개발 환경에서 평문 저장 fallback
        return password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# 수정된 인증 함수 (데이터베이스 기반)
async def get_current_advertiser(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 데이터베이스에서 광고주 조회
    advertiser = await database.fetch_one(
        "SELECT * FROM advertisers WHERE username = :username OR email = :username",
        {"username": username},
    )

    if not advertiser:
        raise credentials_exception
    return dict(advertiser)


async def get_recent_bids() -> List[dict]:
    """최근 입찰 내역을 가져오는 함수"""
    try:
        auction_service_url = os.getenv("AUCTION_SERVICE_URL", "http://localhost:8002")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{auction_service_url}/bids")
            if response.status_code == 200:
                data = response.json()
                print(f'Fetched bids: {len(data.get("bids", []))}')
                return data.get("bids", [])
    except Exception as error:
        print(f"Failed to fetch bids: {error}")
    return []


@app.post("/register", response_model=dict)
async def register_advertiser(advertiser: AdvertiserRegister):
    """광고주 회원가입"""
    try:
        print(f"Registration attempt for: {advertiser.username}")

        # 이메일 중복 확인
        existing_advertiser = await database.fetch_one(
            "SELECT id FROM advertisers WHERE email = :email",
            {"email": advertiser.email},
        )
        if existing_advertiser:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        # 사용자명 중복 확인
        existing_username = await database.fetch_one(
            "SELECT id FROM advertisers WHERE username = :username",
            {"username": advertiser.username},
        )
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        # 비밀번호 해싱
        hashed_password = get_password_hash(advertiser.password)

        # 광고주 생성 (비즈니스 설정 데이터 포함)
        website_url = None
        daily_budget = 10000.00

        if advertiser.business_setup:
            website_url = advertiser.business_setup.websiteUrl
            daily_budget = advertiser.business_setup.dailyBudget

        query = """
        INSERT INTO advertisers (username, email, hashed_password, company_name, website_url, daily_budget) 
        VALUES (:username, :email, :hashed_password, :company_name, :website_url, :daily_budget)
        RETURNING id
        """

        result = await database.fetch_one(
            query,
            {
                "username": advertiser.username,
                "email": advertiser.email,
                "hashed_password": hashed_password,
                "company_name": advertiser.company_name,
                "website_url": website_url,
                "daily_budget": daily_budget,
            },
        )

        if result is None:
            raise HTTPException(status_code=500, detail="Failed to create advertiser")
        advertiser_id = result["id"]

        # 비즈니스 설정 데이터가 있는 경우 관련 테이블에 저장
        if advertiser.business_setup:
            await save_business_setup_data(advertiser_id, advertiser.business_setup)

        # 심사 상태 생성 (pending으로 설정)
        await create_review_status(advertiser_id)

        print(f"Registration successful for: {advertiser.username}")
        return {
            "success": True,
            "message": "광고주 등록이 완료되었습니다. 24시간 내에 심사가 완료됩니다.",
            "username": advertiser.username,
            "review_status": "pending",
            "review_message": "24시간 내 심사 완료",
        }

    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


async def save_business_setup_data(
    advertiser_id: int, business_setup: BusinessSetupData
):
    """비즈니스 설정 데이터를 관련 테이블에 저장"""
    try:
        print(f"Saving business setup data for advertiser_id: {advertiser_id}")
        print(f"Keywords: {business_setup.keywords}")
        print(f"Categories: {business_setup.categories}")

        # 1. 키워드 저장
        for keyword in business_setup.keywords:
            await database.execute(
                """
                INSERT INTO advertiser_keywords (advertiser_id, keyword, priority, match_type)
                VALUES (:advertiser_id, :keyword, :priority, :match_type)
                """,
                {
                    "advertiser_id": advertiser_id,
                    "keyword": keyword,
                    "priority": 1,
                    "match_type": "broad",
                },
            )
            print(f"Saved keyword: {keyword}")

        # 2. 카테고리 저장
        for category_id in business_setup.categories:
            print(f"Processing category_id: {category_id}")

            try:
                # 카테고리 정보 조회
                category_info = await database.fetch_one(
                    "SELECT name, path, level FROM business_categories WHERE id = :category_id",
                    {"category_id": category_id},
                )

                if category_info:
                    print(f"Found category info: {category_info}")
                    await database.execute(
                        """
                        INSERT INTO advertiser_categories (advertiser_id, category_path, category_level, is_primary)
                        VALUES (:advertiser_id, :category_path, :category_level, :is_primary)
                        """,
                        {
                            "advertiser_id": advertiser_id,
                            "category_path": category_info["path"],
                            "category_level": category_info["level"],
                            "is_primary": False,  # 첫 번째 카테고리를 주 카테고리로 설정할 수 있음
                        },
                    )
                    print(
                        f"Saved category: {category_info['name']} (ID: {category_id})"
                    )
                else:
                    print(
                        f"Warning: Category info not found for category_id: {category_id}"
                    )
                    # 카테고리 정보가 없어도 기본값으로 저장
                    await database.execute(
                        """
                        INSERT INTO advertiser_categories (advertiser_id, category_path, category_level, is_primary)
                        VALUES (:advertiser_id, :category_path, :category_level, :is_primary)
                        """,
                        {
                            "advertiser_id": advertiser_id,
                            "category_path": f"Unknown Category {category_id}",
                            "category_level": 1,
                            "is_primary": False,
                        },
                    )
                    print(f"Saved category with default values for ID: {category_id}")

            except Exception as e:
                print(f"Error processing category {category_id}: {e}")
                # 에러가 발생해도 기본값으로 저장
                try:
                    await database.execute(
                        """
                        INSERT INTO advertiser_categories (advertiser_id, category_path, category_level, is_primary)
                        VALUES (:advertiser_id, :category_path, :category_level, :is_primary)
                        """,
                        {
                            "advertiser_id": advertiser_id,
                            "category_path": f"Category {category_id}",
                            "category_level": 1,
                            "is_primary": False,
                        },
                    )
                    print(
                        f"Saved category {category_id} with fallback values after error"
                    )
                except Exception as inner_e:
                    print(
                        f"Failed to save category {category_id} even with fallback: {inner_e}"
                    )

        # 3. 자동 입찰 설정 저장
        await database.execute(
            """
            INSERT INTO auto_bid_settings (
                advertiser_id, is_enabled, daily_budget, max_bid_per_keyword, 
                min_quality_score, preferred_categories, excluded_keywords
            )
            VALUES (:advertiser_id, :is_enabled, :daily_budget, :max_bid_per_keyword, 
                   :min_quality_score, :preferred_categories, :excluded_keywords)
            """,
            {
                "advertiser_id": advertiser_id,
                "is_enabled": False,  # 초기에는 비활성화
                "daily_budget": business_setup.dailyBudget,
                "max_bid_per_keyword": business_setup.bidRange["max"],
                "min_quality_score": 50,
                "preferred_categories": business_setup.categories,
                "excluded_keywords": [],
            },
        )

        print(
            f"Business setup data saved successfully for advertiser_id: {advertiser_id}"
        )

    except Exception as e:
        print(f"Error saving business setup data: {e}")
        print(f"Error details: {str(e)}")
        raise e


async def create_review_status(advertiser_id: int):
    """광고주 심사 상태 생성"""
    try:
        await database.execute(
            """
            INSERT INTO advertiser_reviews (
                advertiser_id, review_status, recommended_bid_min, recommended_bid_max
            )
            VALUES (:advertiser_id, 'pending', :min_bid, :max_bid)
            """,
            {"advertiser_id": advertiser_id, "min_bid": 100, "max_bid": 5000},
        )
        print(f"Review status created for advertiser_id: {advertiser_id}")

    except Exception as e:
        print(f"Error creating review status: {e}")
        raise e


@app.get("/review-status")
async def get_review_status(current_advertiser: dict = Depends(get_current_advertiser)):
    """광고주 심사 상태 조회"""
    try:
        advertiser_id = current_advertiser["id"]

        review_info = await database.fetch_one(
            """
            SELECT review_status, review_notes, created_at, updated_at
            FROM advertiser_reviews 
            WHERE advertiser_id = :advertiser_id
            ORDER BY created_at DESC
            LIMIT 1
            """,
            {"advertiser_id": advertiser_id},
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

    except Exception as e:
        print(f"Error getting review status: {e}")
        raise HTTPException(status_code=500, detail=f"심사 상태 조회 실패: {str(e)}")


# Admin API Endpoints
@app.get("/admin/pending-reviews")
async def get_pending_reviews():
    """심사 대기 중인 광고주 목록 조회"""
    try:
        # 심사 대기 중인 광고주 조회
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

        # 각 광고주의 키워드와 카테고리 정보 가져오기
        result = []
        for advertiser in advertisers:
            # 키워드 조회
            keywords = await database.fetch_all(
                "SELECT keyword FROM advertiser_keywords WHERE advertiser_id = :advertiser_id",
                {"advertiser_id": advertiser["advertiser_id"]},
            )

            # 카테고리 조회
            categories = await database.fetch_all(
                "SELECT category_path FROM advertiser_categories WHERE advertiser_id = :advertiser_id",
                {"advertiser_id": advertiser["advertiser_id"]},
            )

            result.append(
                {
                    "id": advertiser["id"],
                    "advertiser_id": advertiser["advertiser_id"],
                    "company_name": advertiser["company_name"],
                    "email": advertiser["email"],
                    "website_url": advertiser["website_url"],
                    "daily_budget": float(advertiser["daily_budget"]),
                    "created_at": advertiser["created_at"].isoformat(),
                    "review_status": advertiser["review_status"],
                    "review_notes": advertiser["review_notes"],
                    "recommended_bid_min": advertiser["recommended_bid_min"],
                    "recommended_bid_max": advertiser["recommended_bid_max"],
                    "keywords": [kw["keyword"] for kw in keywords],
                    "categories": [cat["category_path"] for cat in categories],
                }
            )

        return {"advertisers": result}

    except Exception as e:
        print(f"Error fetching pending reviews: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch pending reviews: {str(e)}"
        )


@app.get("/admin/rejected-advertisers")
async def get_rejected_advertisers():
    """거절된 광고주 목록 조회"""
    try:
        # 거절된 광고주 조회
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

        # 각 광고주의 키워드와 카테고리 정보 가져오기
        result = []
        for advertiser in advertisers:
            # 키워드 조회
            keywords = await database.fetch_all(
                "SELECT keyword FROM advertiser_keywords WHERE advertiser_id = :advertiser_id",
                {"advertiser_id": advertiser["advertiser_id"]},
            )

            # 카테고리 조회
            categories = await database.fetch_all(
                "SELECT category_path FROM advertiser_categories WHERE advertiser_id = :advertiser_id",
                {"advertiser_id": advertiser["advertiser_id"]},
            )

            result.append(
                {
                    "id": advertiser["id"],
                    "advertiser_id": advertiser["advertiser_id"],
                    "company_name": advertiser["company_name"],
                    "email": advertiser["email"],
                    "website_url": advertiser["website_url"],
                    "daily_budget": float(advertiser["daily_budget"]),
                    "created_at": advertiser["created_at"].isoformat(),
                    "review_status": advertiser["review_status"],
                    "review_notes": advertiser["review_notes"],
                    "recommended_bid_min": advertiser["recommended_bid_min"],
                    "recommended_bid_max": advertiser["recommended_bid_max"],
                    "keywords": [kw["keyword"] for kw in keywords],
                    "categories": [cat["category_path"] for cat in categories],
                }
            )

        return {"advertisers": result}

    except Exception as e:
        print(f"Error fetching rejected advertisers: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch rejected advertisers: {str(e)}"
        )


@app.get("/admin/approved-advertisers")
async def get_approved_advertisers():
    """승인된 광고주 목록 조회"""
    try:
        # 승인된 광고주 조회
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

        # 각 광고주의 키워드와 카테고리 정보 가져오기
        result = []
        for advertiser in advertisers:
            # 키워드 조회
            keywords = await database.fetch_all(
                "SELECT keyword FROM advertiser_keywords WHERE advertiser_id = :advertiser_id",
                {"advertiser_id": advertiser["advertiser_id"]},
            )

            # 카테고리 조회
            categories = await database.fetch_all(
                "SELECT category_path FROM advertiser_categories WHERE advertiser_id = :advertiser_id",
                {"advertiser_id": advertiser["advertiser_id"]},
            )

            result.append(
                {
                    "id": advertiser["id"],
                    "advertiser_id": advertiser["advertiser_id"],
                    "company_name": advertiser["company_name"],
                    "email": advertiser["email"],
                    "website_url": advertiser["website_url"],
                    "daily_budget": float(advertiser["daily_budget"]),
                    "created_at": advertiser["created_at"].isoformat(),
                    "review_status": advertiser["review_status"],
                    "review_notes": advertiser["review_notes"],
                    "recommended_bid_min": advertiser["recommended_bid_min"],
                    "recommended_bid_max": advertiser["recommended_bid_max"],
                    "keywords": [kw["keyword"] for kw in keywords],
                    "categories": [cat["category_path"] for cat in categories],
                }
            )

        return {"advertisers": result}

    except Exception as e:
        print(f"Error fetching approved advertisers: {e}")
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
):
    """관리자: 심사 상태 업데이트"""
    try:
        # 심사 상태 업데이트
        query = """
        UPDATE advertiser_reviews 
        SET review_status = :review_status,
            review_notes = :review_notes,
            recommended_bid_min = :recommended_bid_min,
            recommended_bid_max = :recommended_bid_max,
            updated_at = CURRENT_TIMESTAMP
        WHERE advertiser_id = :advertiser_id
        """

        await database.execute(
            query,
            {
                "advertiser_id": advertiser_id,
                "review_status": review_status,
                "review_notes": review_notes,
                "recommended_bid_min": recommended_bid_min,
                "recommended_bid_max": recommended_bid_max,
            },
        )

        return {"success": True, "message": "심사 상태가 업데이트되었습니다."}

    except Exception as e:
        print(f"Error updating review status: {e}")
        raise HTTPException(
            status_code=500, detail=f"심사 상태 업데이트 실패: {str(e)}"
        )


@app.patch("/admin/update-advertiser-data")
async def update_advertiser_data(
    advertiser_id: int, keywords: List[str], categories: List[str]
):
    """관리자: 광고주 키워드/카테고리 수정"""
    try:
        # 기존 키워드 삭제
        await database.execute(
            "DELETE FROM advertiser_keywords WHERE advertiser_id = :advertiser_id",
            {"advertiser_id": advertiser_id},
        )

        # 새 키워드 추가
        for keyword in keywords:
            await database.execute(
                """
                INSERT INTO advertiser_keywords (advertiser_id, keyword, priority, match_type)
                VALUES (:advertiser_id, :keyword, :priority, :match_type)
                """,
                {
                    "advertiser_id": advertiser_id,
                    "keyword": keyword,
                    "priority": 1,
                    "match_type": "broad",
                },
            )

        # 기존 카테고리 삭제
        await database.execute(
            "DELETE FROM advertiser_categories WHERE advertiser_id = :advertiser_id",
            {"advertiser_id": advertiser_id},
        )

        # 새 카테고리 추가
        for category_path in categories:
            # 카테고리 레벨 계산
            level = len(category_path.split(" > "))

            await database.execute(
                """
                INSERT INTO advertiser_categories (advertiser_id, category_path, category_level, is_primary)
                VALUES (:advertiser_id, :category_path, :category_level, :is_primary)
                """,
                {
                    "advertiser_id": advertiser_id,
                    "category_path": category_path,
                    "category_level": level,
                    "is_primary": False,
                },
            )

        return {"success": True, "message": "광고주 데이터가 업데이트되었습니다."}

    except Exception as e:
        print(f"Error updating advertiser data: {e}")
        raise HTTPException(
            status_code=500, detail=f"광고주 데이터 업데이트 실패: {str(e)}"
        )


@app.post("/additional-info")
async def submit_additional_info(additional_info: dict):
    """광고주 추가 정보 제출"""
    try:
        # 추가 정보를 저장하는 로직
        # 예: 추가 문서, 설명 등

        return {
            "success": True,
            "message": "추가 정보가 제출되었습니다. 검토 후 연락드리겠습니다.",
        }

    except Exception as e:
        print(f"Error submitting additional info: {e}")
        raise HTTPException(status_code=500, detail=f"추가 정보 제출 실패: {str(e)}")


@app.post("/login", response_model=Token)
async def login_advertiser(advertiser: AdvertiserLogin):
    """광고주 로그인"""
    try:
        print(f"Login attempt for username: {advertiser.username}")

        # 데이터베이스에서 광고주 조회 (username 또는 email로)
        stored_advertiser = await database.fetch_one(
            "SELECT * FROM advertisers WHERE username = :username OR email = :username",
            {"username": advertiser.username},
        )

        if not stored_advertiser:
            print(f"Advertiser not found: {advertiser.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        print(f"Found advertiser: {stored_advertiser['username']}")

        # 비밀번호 검증
        password_match = verify_password(
            advertiser.password, stored_advertiser["hashed_password"]
        )
        print(f"Password verification result: {password_match}")

        if not password_match:
            print("Password verification failed")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        # JWT 토큰 생성
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": stored_advertiser["username"]},
            expires_delta=access_token_expires,
        )

        print(f"Login successful for: {advertiser.username}")
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(current_advertiser: dict = Depends(get_current_advertiser)):
    """광고주 대시보드 데이터를 조회합니다."""
    try:
        print(f"Dashboard request for advertiser: {current_advertiser['username']}")

        # 심사 상태 확인
        advertiser_id = current_advertiser["id"]
        review_info = await database.fetch_one(
            """
            SELECT review_status FROM advertiser_reviews 
            WHERE advertiser_id = :advertiser_id
            ORDER BY created_at DESC
            LIMIT 1
            """,
            {"advertiser_id": advertiser_id},
        )

        review_status = review_info["review_status"] if review_info else "pending"

        # 실제 입찰 데이터 조회 (심사 승인된 경우에만)
        if review_status == "approved":
            print(f"🔍 심사 승인됨 - 실제 데이터 조회 시작")

            try:
                # 1. 실제 입찰 요약 계산
                bid_summary_query = """
                    SELECT 
                        COUNT(*) as total_bids,
                        COUNT(CASE WHEN bid_result = 'won' THEN 1 END) as successful_bids,
                        SUM(bid_amount) as total_spent,
                        AVG(bid_amount) as avg_bid_amount
                    FROM auto_bid_logs 
                    WHERE advertiser_id = :advertiser_id
                    AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                """
                bid_summary = await database.fetch_one(
                    bid_summary_query, {"advertiser_id": advertiser_id}
                )

                print(f"🔍 DB 조회 결과: {bid_summary}")

                if bid_summary:
                    total_bids = int(bid_summary["total_bids"] or 0)
                    successful_bids = int(bid_summary["successful_bids"] or 0)
                    total_spent = int(bid_summary["total_spent"] or 0)
                    average_bid_amount = float(bid_summary["avg_bid_amount"] or 0)
                    print(
                        f"🔍 실제 데이터: 총입찰={total_bids}, 성공={successful_bids}, 지출={total_spent}"
                    )
                else:
                    total_bids = 0
                    successful_bids = 0
                    total_spent = 0
                    average_bid_amount = 0
                    print(f"🔍 DB 데이터 없음 - 기본값 사용")
            except Exception as e:
                print(f"🔍 입찰 요약 계산 오류: {e}")
                raise e

            try:
                # 2. 자동입찰 설정 및 예산 현황
                auto_bid_settings_query = """
                    SELECT 
                        is_enabled,
                        daily_budget,
                        max_bid_per_keyword,
                        min_quality_score
                    FROM auto_bid_settings 
                    WHERE advertiser_id = :advertiser_id
                """
                auto_bid_settings = await database.fetch_one(
                    auto_bid_settings_query, {"advertiser_id": advertiser_id}
                )

                # 오늘 지출액 계산
                today_spent_query = """
                    SELECT COALESCE(SUM(bid_amount), 0) as today_spent
                    FROM auto_bid_logs 
                    WHERE advertiser_id = :advertiser_id
                    AND DATE(created_at) = CURRENT_DATE
                """
                today_spent_result = await database.fetch_one(
                    today_spent_query, {"advertiser_id": advertiser_id}
                )
                today_spent = int(
                    today_spent_result["today_spent"] if today_spent_result else 0
                )

                # 예산 사용률 계산
                daily_budget = float(
                    auto_bid_settings["daily_budget"] if auto_bid_settings else 10000
                )
                budget_usage_percent = (
                    (today_spent / daily_budget * 100) if daily_budget > 0 else 0
                )
            except Exception as e:
                print(f"🔍 자동입찰 설정 조회 오류: {e}")
                raise e

            try:
                # 3. 최근 입찰 내역 조회
                recent_bids_query = """
                    SELECT 
                        id,
                        search_query,
                        bid_amount as amount,
                        created_at as timestamp,
                        bid_result as status,
                        match_score,
                        quality_score
                    FROM auto_bid_logs 
                    WHERE advertiser_id = :advertiser_id
                    ORDER BY created_at DESC
                    LIMIT 10
                """
                recent_bids_data = await database.fetch_all(
                    recent_bids_query, {"advertiser_id": advertiser_id}
                )

                recent_bids = []
                print(f"🔍 최근 입찰 데이터 개수: {len(recent_bids_data)}")
                for i, bid in enumerate(recent_bids_data):
                    print(f"🔍 입찰 {i+1}: {bid}")
                    try:
                        recent_bids.append(
                            {
                                "id": bid["id"],
                                "auctionId": bid["search_query"],
                                "amount": bid["amount"],
                                "timestamp": (
                                    bid["timestamp"].isoformat()
                                    if bid["timestamp"]
                                    else ""
                                ),
                                "status": bid["status"],
                                "highestBid": bid[
                                    "amount"
                                ],  # 실제로는 경매에서 최고가를 가져와야 함
                                "myBid": bid["amount"],
                            }
                        )
                    except Exception as e:
                        print(f"🔍 입찰 {i+1} 처리 오류: {e}")
                        print(f"🔍 bid 객체: {bid}")
                        raise e
            except Exception as e:
                print(f"🔍 최근 입찰 내역 조회 오류: {e}")
                raise e

            try:
                # 4. 성과 이력 (주차별 성공률)
                performance_query = """
                    SELECT 
                        DATE_TRUNC('week', created_at) as week_start,
                        COUNT(*) as total_bids,
                        COUNT(CASE WHEN bid_result = 'won' THEN 1 END) as won_bids,
                        AVG(match_score) as avg_match_score
                    FROM auto_bid_logs 
                    WHERE advertiser_id = :advertiser_id
                    AND created_at >= CURRENT_DATE - INTERVAL '4 weeks'
                    GROUP BY DATE_TRUNC('week', created_at)
                    ORDER BY week_start DESC
                """
                performance_data = await database.fetch_all(
                    performance_query, {"advertiser_id": advertiser_id}
                )

                performance_history = []
                for i, week_data in enumerate(performance_data):
                    total = int(week_data["total_bids"] or 0)
                    won = int(week_data["won_bids"] or 0)
                    success_rate = (won / total * 100) if total > 0 else 0
                    performance_history.append(
                        PerformanceHistory(
                            name=f"Week {i+1}", score=int(round(success_rate, 1))
                        )
                    )

                # 기본 성과 데이터가 없으면 기본값 제공
                if not performance_history:
                    performance_history = [
                        PerformanceHistory(name="Week 1", score=65),
                        PerformanceHistory(name="Week 2", score=70),
                        PerformanceHistory(name="Week 3", score=72),
                        PerformanceHistory(name="Week 4", score=75),
                    ]

                # 5. 추가 통계 데이터
                additional_stats = {
                    "autoBidEnabled": (
                        auto_bid_settings["is_enabled"] if auto_bid_settings else False
                    ),
                    "dailyBudget": daily_budget,
                    "todaySpent": today_spent,
                    "budgetUsagePercent": round(budget_usage_percent, 1),
                    "maxBidPerKeyword": (
                        auto_bid_settings["max_bid_per_keyword"]
                        if auto_bid_settings
                        else 3000
                    ),
                    "minQualityScore": (
                        auto_bid_settings["min_quality_score"]
                        if auto_bid_settings
                        else 50
                    ),
                    "remainingBudget": daily_budget - today_spent,
                }

                # 6. BiddingSummary 객체 생성
                bidding_summary = BiddingSummary(
                    totalBids=total_bids,
                    successfulBids=successful_bids,
                    totalSpent=total_spent,
                    averageBidAmount=round(average_bid_amount, 2),
                )

            except Exception as e:
                print(f"🔍 성과 이력 및 추가 통계 오류: {e}")
                raise e

        else:
            # 심사 승인되지 않은 경우 기본값
            total_bids = 0
            successful_bids = 0
            total_spent = 0
            average_bid_amount = 0
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

        print(f"Dashboard data for advertiser {advertiser_id}:")
        print(f"  - Total bids: {total_bids}")
        print(f"  - Successful bids: {successful_bids}")
        print(f"  - Total spent: ₩{total_spent:,}")
        print(f"  - Recent bids: {len(recent_bids)}")

        return DashboardResponse(
            biddingSummary=bidding_summary,
            performanceHistory=performance_history,
            recentBids=recent_bids,
            additionalStats=additional_stats,
        )

    except Exception as e:
        print(f"Dashboard error: {e}")
        raise HTTPException(
            status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {
        "status": "healthy",
        "service": "advertiser-service",
        "database": "connected",
    }


# 자동 입찰 관련 엔드포인트들


@app.get("/me")
async def get_current_advertiser_info(
    current_advertiser: dict = Depends(get_current_advertiser),
):
    """현재 광고주 정보 조회"""
    try:
        advertiser_id = current_advertiser["id"]

        # 광고주 정보 조회
        advertiser_query = """
            SELECT id, username, email, company_name, website_url
            FROM advertisers
            WHERE id = :advertiser_id
        """
        advertiser = await database.fetch_one(
            advertiser_query, {"advertiser_id": advertiser_id}
        )

        if not advertiser:
            raise HTTPException(status_code=404, detail="광고주를 찾을 수 없습니다")

        return advertiser

    except Exception as e:
        print(f"Error getting advertiser info: {e}")
        raise HTTPException(status_code=500, detail=f"광고주 정보 조회 실패: {str(e)}")


@app.get("/auto-bid-settings/{advertiser_id}")
async def get_auto_bid_settings(advertiser_id: int):
    """자동 입찰 설정 조회"""
    try:
        settings_query = """
            SELECT is_enabled, daily_budget, max_bid_per_keyword, 
                   min_quality_score, preferred_categories, excluded_keywords
            FROM auto_bid_settings
            WHERE advertiser_id = :advertiser_id
        """
        settings = await database.fetch_one(
            settings_query, {"advertiser_id": advertiser_id}
        )

        if not settings:
            # 기본 설정 생성
            default_settings = {
                "is_enabled": False,
                "daily_budget": 10000.00,
                "max_bid_per_keyword": 3000,
                "min_quality_score": 50,
                "preferred_categories": [],
                "excluded_keywords": [],
            }

            # DB에 기본 설정 저장
            insert_query = """
                INSERT INTO auto_bid_settings (advertiser_id, is_enabled, daily_budget, 
                                             max_bid_per_keyword, min_quality_score)
                VALUES (:advertiser_id, :is_enabled, :daily_budget, :max_bid_per_keyword, :min_quality_score)
            """
            await database.execute(
                insert_query, {"advertiser_id": advertiser_id, **default_settings}
            )

            return default_settings

        return settings

    except Exception as e:
        print(f"Error getting auto bid settings: {e}")
        raise HTTPException(
            status_code=500, detail=f"자동 입찰 설정 조회 실패: {str(e)}"
        )


@app.put("/auto-bid-settings/{advertiser_id}")
async def update_auto_bid_settings(
    advertiser_id: int,
    is_enabled: bool,
    daily_budget: float,
    max_bid_per_keyword: int,
    min_quality_score: int,
    excluded_keywords: List[str] = [],
):
    """자동 입찰 설정 업데이트"""
    try:
        update_query = """
            UPDATE auto_bid_settings
            SET is_enabled = :is_enabled,
                daily_budget = :daily_budget,
                max_bid_per_keyword = :max_bid_per_keyword,
                min_quality_score = :min_quality_score,
                excluded_keywords = :excluded_keywords,
                updated_at = CURRENT_TIMESTAMP
            WHERE advertiser_id = :advertiser_id
        """

        await database.execute(
            update_query,
            {
                "advertiser_id": advertiser_id,
                "is_enabled": is_enabled,
                "daily_budget": daily_budget,
                "max_bid_per_keyword": max_bid_per_keyword,
                "min_quality_score": min_quality_score,
                "excluded_keywords": excluded_keywords,
            },
        )

        return {"success": True, "message": "자동 입찰 설정이 업데이트되었습니다"}

    except Exception as e:
        print(f"Error updating auto bid settings: {e}")
        raise HTTPException(
            status_code=500, detail=f"자동 입찰 설정 업데이트 실패: {str(e)}"
        )


@app.get("/keywords/{advertiser_id}")
async def get_advertiser_keywords(advertiser_id: int):
    """광고주 키워드 목록 조회"""
    try:
        keywords_query = """
            SELECT id, keyword, priority, match_type, created_at
            FROM advertiser_keywords
            WHERE advertiser_id = :advertiser_id
            ORDER BY priority DESC, created_at ASC
        """
        keywords = await database.fetch_all(
            keywords_query, {"advertiser_id": advertiser_id}
        )
        return keywords

    except Exception as e:
        print(f"Error getting keywords: {e}")
        raise HTTPException(status_code=500, detail=f"키워드 조회 실패: {str(e)}")


@app.put("/keywords/{advertiser_id}")
async def update_advertiser_keywords(advertiser_id: int, keywords: List[dict]):
    """광고주 키워드 업데이트"""
    try:
        # 기존 키워드 삭제
        delete_query = (
            "DELETE FROM advertiser_keywords WHERE advertiser_id = :advertiser_id"
        )
        await database.execute(delete_query, {"advertiser_id": advertiser_id})

        # 새 키워드 추가
        for keyword_data in keywords:
            insert_query = """
                INSERT INTO advertiser_keywords (advertiser_id, keyword, priority, match_type)
                VALUES (:advertiser_id, :keyword, :priority, :match_type)
            """
            await database.execute(
                insert_query,
                {
                    "advertiser_id": advertiser_id,
                    "keyword": keyword_data["keyword"],
                    "priority": keyword_data["priority"],
                    "match_type": keyword_data["match_type"],
                },
            )

        return {"success": True, "message": "키워드가 업데이트되었습니다"}

    except Exception as e:
        print(f"Error updating keywords: {e}")
        raise HTTPException(status_code=500, detail=f"키워드 업데이트 실패: {str(e)}")


@app.post("/excluded-keywords/{advertiser_id}")
async def update_excluded_keywords(advertiser_id: int, action: str, keyword: str):
    """제외 키워드 추가/삭제"""
    try:
        if action == "add":
            # 제외 키워드 추가
            update_query = """
                UPDATE auto_bid_settings
                SET excluded_keywords = array_append(excluded_keywords, :keyword)
                WHERE advertiser_id = :advertiser_id
            """
        elif action == "remove":
            # 제외 키워드 삭제
            update_query = """
                UPDATE auto_bid_settings
                SET excluded_keywords = array_remove(excluded_keywords, :keyword)
                WHERE advertiser_id = :advertiser_id
            """
        else:
            raise HTTPException(status_code=400, detail="잘못된 액션입니다")

        await database.execute(
            update_query, {"advertiser_id": advertiser_id, "keyword": keyword}
        )

        return {"success": True, "message": f"제외 키워드가 {action}되었습니다"}

    except Exception as e:
        print(f"Error updating excluded keywords: {e}")
        raise HTTPException(
            status_code=500, detail=f"제외 키워드 업데이트 실패: {str(e)}"
        )


@app.get("/bid-history/{advertiser_id}")
async def get_bid_history(
    advertiser_id: int,
    timeRange: str = "week",
    filter: str = "all",
    resultFilter: str = "all",
):
    """입찰 내역 조회"""
    try:
        # 시간 범위 조건 설정
        time_conditions = {
            "today": "AND created_at >= CURRENT_DATE",
            "week": "AND created_at >= CURRENT_DATE - INTERVAL '7 days'",
            "month": "AND created_at >= CURRENT_DATE - INTERVAL '30 days'",
        }
        time_condition = time_conditions.get(timeRange, time_conditions["week"])

        # 필터 조건 설정
        filter_conditions = {
            "all": "",
            "auto": "AND is_auto_bid = true",
            "manual": "AND is_auto_bid = false",
        }
        filter_condition = filter_conditions.get(filter, "")

        # 결과 필터 조건 설정
        result_conditions = {
            "all": "",
            "won": "AND result = 'won'",
            "lost": "AND result = 'lost'",
        }
        result_condition = result_conditions.get(resultFilter, "")

        # 입찰 내역 조회 (auction-service의 bids 테이블에서)
        bid_history_query = f"""
            SELECT b.id, b.auction_id, b.buyer_name, b.price as bid_amount,
                   b.created_at as timestamp, b.result,
                   a.query_text as search_query,
                   COALESCE(b.match_score, 0.5) as match_score,
                   COALESCE(b.quality_score, 50) as quality_score,
                   COALESCE(b.is_auto_bid, false) as is_auto_bid
            FROM bids b
            JOIN auctions a ON b.auction_id = a.id
            WHERE b.buyer_name = (SELECT company_name FROM advertisers WHERE id = :advertiser_id)
            {time_condition}
            {filter_condition}
            {result_condition}
            ORDER BY b.created_at DESC
            LIMIT 100
        """

        bid_history = await database.fetch_all(
            bid_history_query, {"advertiser_id": advertiser_id}
        )

        return bid_history

    except Exception as e:
        print(f"Error getting bid history: {e}")
        raise HTTPException(status_code=500, detail=f"입찰 내역 조회 실패: {str(e)}")


# 머신러닝 기반 분석 엔드포인트들


@app.get("/analytics/auto-bidding/{advertiser_id}")
async def get_auto_bidding_analytics(advertiser_id: int, timeRange: str = "week"):
    """자동 입찰 성과 분석"""
    try:
        # 시간 범위 조건 설정
        time_conditions = {
            "day": "AND created_at >= CURRENT_DATE",
            "week": "AND created_at >= CURRENT_DATE - INTERVAL '7 days'",
            "month": "AND created_at >= CURRENT_DATE - INTERVAL '30 days'",
        }
        time_condition = time_conditions.get(timeRange, time_conditions["week"])

        # 시계열 데이터 조회
        time_series_query = f"""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as total_bids,
                AVG(CASE WHEN bid_result = 'won' THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                AVG(bid_amount) as avg_bid_amount,
                SUM(CASE WHEN bid_result = 'won' THEN bid_amount ELSE 0 END) as total_spent
            FROM auto_bid_logs
            WHERE advertiser_id = :advertiser_id {time_condition}
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """

        time_series = await database.fetch_all(
            time_series_query, {"advertiser_id": advertiser_id}
        )

        # 키워드별 성과 분석
        keyword_performance_query = f"""
            SELECT 
                search_query as keyword,
                COUNT(*) as total_bids,
                AVG(CASE WHEN bid_result = 'won' THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                AVG(bid_amount) as avg_bid_amount,
                (AVG(CASE WHEN bid_result = 'won' THEN 1.0 ELSE 0.0 END) * 100) * 2 as roi
            FROM auto_bid_logs
            WHERE advertiser_id = :advertiser_id {time_condition}
            GROUP BY search_query
            HAVING COUNT(*) >= 3
            ORDER BY success_rate DESC
            LIMIT 10
        """

        keyword_performance = await database.fetch_all(
            keyword_performance_query, {"advertiser_id": advertiser_id}
        )

        # 매칭 타입별 분석
        match_type_query = f"""
            SELECT 
                match_type,
                COUNT(*) as total_bids,
                AVG(CASE WHEN bid_result = 'won' THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                AVG(bid_amount) as avg_bid_amount
            FROM auto_bid_logs
            WHERE advertiser_id = :advertiser_id {time_condition}
            GROUP BY match_type
            ORDER BY success_rate DESC
        """

        match_type_analysis = await database.fetch_all(
            match_type_query, {"advertiser_id": advertiser_id}
        )

        # AI 최적화 제안 생성
        optimization_suggestions = await generate_optimization_suggestions(
            advertiser_id, time_condition
        )

        # 성과 비교 데이터
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

    except Exception as e:
        print(f"Error getting auto bidding analytics: {e}")
        raise HTTPException(status_code=500, detail=f"자동 입찰 분석 실패: {str(e)}")


@app.get("/optimization/suggestions/{advertiser_id}")
async def get_optimization_suggestions_endpoint(advertiser_id: int):
    """머신러닝 기반 최적화 제안"""
    try:
        time_condition = "AND created_at >= CURRENT_DATE - INTERVAL '7 days'"
        suggestions = await generate_optimization_suggestions(
            advertiser_id, time_condition
        )

        return {"suggestions": suggestions, "generated_at": datetime.now().isoformat()}

    except Exception as e:
        print(f"Error getting optimization suggestions: {e}")
        raise HTTPException(status_code=500, detail=f"최적화 제안 조회 실패: {str(e)}")


@app.get("/performance/comparison/{advertiser_id}")
async def get_performance_comparison_endpoint(
    advertiser_id: int, timeRange: str = "week"
):
    """자동 vs 수동 입찰 성과 비교"""
    try:
        time_conditions = {
            "day": "AND created_at >= CURRENT_DATE",
            "week": "AND created_at >= CURRENT_DATE - INTERVAL '7 days'",
            "month": "AND created_at >= CURRENT_DATE - INTERVAL '30 days'",
        }
        time_condition = time_conditions.get(timeRange, time_conditions["week"])

        comparison = await get_performance_comparison(advertiser_id, time_condition)

        return {"comparison": comparison, "timeRange": timeRange}

    except Exception as e:
        print(f"Error getting performance comparison: {e}")
        raise HTTPException(status_code=500, detail=f"성과 비교 조회 실패: {str(e)}")


# 머신러닝 헬퍼 함수들


async def generate_optimization_suggestions(advertiser_id: int, time_condition: str):
    """AI 기반 최적화 제안 생성"""
    suggestions = []

    try:
        # 키워드 성과 분석
        keyword_analysis_query = f"""
            SELECT 
                search_query,
                COUNT(*) as bid_count,
                AVG(CASE WHEN bid_result = 'won' THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                AVG(bid_amount) as avg_bid,
                AVG(match_score) as avg_match_score
            FROM auto_bid_logs
            WHERE advertiser_id = :advertiser_id {time_condition}
            GROUP BY search_query
            HAVING COUNT(*) >= 2
        """

        keyword_data = await database.fetch_all(
            keyword_analysis_query, {"advertiser_id": advertiser_id}
        )

        for keyword in keyword_data:
            if keyword["success_rate"] < 30:
                suggestions.append(
                    {
                        "type": "keyword",
                        "priority": "high",
                        "title": f"키워드 '{keyword['search_query']}' 성과 개선 필요",
                        "description": f"성공률이 {keyword['success_rate']:.1f}%로 매우 낮습니다. 키워드 매칭 타입을 조정하거나 입찰가를 낮춰보세요.",
                        "expectedImpact": "성공률 20% 향상",
                        "action": "키워드 설정 조정",
                    }
                )
            elif keyword["success_rate"] < 50:
                suggestions.append(
                    {
                        "type": "keyword",
                        "priority": "medium",
                        "title": f"키워드 '{keyword['search_query']}' 최적화 기회",
                        "description": f"성공률이 {keyword['success_rate']:.1f}%입니다. 입찰가를 약간 조정하면 성과가 개선될 수 있습니다.",
                        "expectedImpact": "성공률 10% 향상",
                        "action": "입찰가 조정",
                    }
                )

        # 입찰가 분석
        bid_analysis_query = f"""
            SELECT 
                AVG(bid_amount) as avg_bid,
                AVG(CASE WHEN bid_result = 'won' THEN bid_amount ELSE NULL END) as avg_winning_bid,
                AVG(CASE WHEN bid_result = 'lost' THEN bid_amount ELSE NULL END) as avg_losing_bid
            FROM auto_bid_logs
            WHERE advertiser_id = :advertiser_id {time_condition}
        """

        bid_data = await database.fetch_one(
            bid_analysis_query, {"advertiser_id": advertiser_id}
        )

        if bid_data and bid_data["avg_winning_bid"] and bid_data["avg_losing_bid"]:
            if bid_data["avg_winning_bid"] > bid_data["avg_losing_bid"] * 1.5:
                suggestions.append(
                    {
                        "type": "bid",
                        "priority": "high",
                        "title": "입찰가 최적화 필요",
                        "description": "성공한 입찰가가 실패한 입찰가보다 50% 이상 높습니다. 입찰가를 낮춰서 효율성을 높여보세요.",
                        "expectedImpact": "비용 30% 절약",
                        "action": "입찰가 하향 조정",
                    }
                )

        # 시간대 분석
        time_analysis_query = f"""
            SELECT 
                EXTRACT(HOUR FROM created_at) as hour,
                COUNT(*) as bid_count,
                AVG(CASE WHEN bid_result = 'won' THEN 1.0 ELSE 0.0 END) * 100 as success_rate
            FROM auto_bid_logs
            WHERE advertiser_id = :advertiser_id {time_condition}
            GROUP BY EXTRACT(HOUR FROM created_at)
            ORDER BY success_rate DESC
        """

        time_data = await database.fetch_all(
            time_analysis_query, {"advertiser_id": advertiser_id}
        )

        if time_data:
            best_hour = time_data[0]
            worst_hour = time_data[-1]

            if best_hour["success_rate"] - worst_hour["success_rate"] > 30:
                suggestions.append(
                    {
                        "type": "timing",
                        "priority": "medium",
                        "title": "시간대별 입찰 최적화",
                        "description": f"{best_hour['hour']}시대 성공률이 {worst_hour['hour']}시대보다 {best_hour['success_rate'] - worst_hour['success_rate']:.1f}% 높습니다.",
                        "expectedImpact": "성공률 15% 향상",
                        "action": "시간대 설정 조정",
                    }
                )

        # 예산 분석
        budget_analysis_query = f"""
            SELECT 
                SUM(CASE WHEN bid_result = 'won' THEN bid_amount ELSE 0 END) as total_spent,
                COUNT(CASE WHEN bid_result = 'won' THEN 1 END) as won_bids,
                COUNT(*) as total_bids
            FROM auto_bid_logs
            WHERE advertiser_id = :advertiser_id {time_condition}
        """

        budget_data = await database.fetch_one(
            budget_analysis_query, {"advertiser_id": advertiser_id}
        )

        if budget_data and budget_data["total_bids"] > 0:
            success_rate = (budget_data["won_bids"] / budget_data["total_bids"]) * 100
            if success_rate < 40:
                suggestions.append(
                    {
                        "type": "budget",
                        "priority": "high",
                        "title": "예산 효율성 개선 필요",
                        "description": f"전체 성공률이 {success_rate:.1f}%로 낮습니다. 예산을 키워드별로 더 효율적으로 분배해보세요.",
                        "expectedImpact": "ROI 25% 향상",
                        "action": "예산 재분배",
                    }
                )

        return suggestions[:5]  # 상위 5개 제안만 반환

    except Exception as e:
        print(f"Error generating optimization suggestions: {e}")
        return []


async def get_performance_comparison(advertiser_id: int, time_condition: str):
    """자동 vs 수동 입찰 성과 비교"""
    try:
        # 자동 입찰 성과
        auto_performance_query = f"""
            SELECT 
                COUNT(*) as total_bids,
                AVG(CASE WHEN bid_result = 'won' THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                AVG(bid_amount) as avg_bid_amount,
                SUM(CASE WHEN bid_result = 'won' THEN bid_amount ELSE 0 END) as total_spent
            FROM auto_bid_logs
            WHERE advertiser_id = :advertiser_id {time_condition}
        """

        auto_performance = await database.fetch_one(
            auto_performance_query, {"advertiser_id": advertiser_id}
        )

        # 수동 입찰 성과 (auction-service의 bids 테이블에서)
        manual_performance_query = f"""
            SELECT 
                COUNT(*) as total_bids,
                AVG(CASE WHEN result = 'won' THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                AVG(price) as avg_bid_amount,
                SUM(CASE WHEN result = 'won' THEN price ELSE 0 END) as total_spent
            FROM bids b
            JOIN auctions a ON b.auction_id = a.id
            WHERE b.buyer_name = (SELECT company_name FROM advertisers WHERE id = :advertiser_id)
            AND b.is_auto_bid = false {time_condition.replace('created_at', 'b.created_at')}
        """

        manual_performance = await database.fetch_one(
            manual_performance_query, {"advertiser_id": advertiser_id}
        )

        # 비교 데이터 생성
        comparison = []

        if auto_performance and manual_performance:
            # 성공률 비교
            auto_success = auto_performance["success_rate"] or 0
            manual_success = manual_performance["success_rate"] or 0
            success_improvement = (
                auto_success - manual_success if manual_success > 0 else 0
            )

            comparison.append(
                {
                    "metric": "성공률",
                    "autoBid": round(auto_success, 1),
                    "manualBid": round(manual_success, 1),
                    "improvement": round(success_improvement, 1),
                }
            )

            # 평균 입찰가 비교
            auto_avg = auto_performance["avg_bid_amount"] or 0
            manual_avg = manual_performance["avg_bid_amount"] or 0
            avg_improvement = (
                ((manual_avg - auto_avg) / manual_avg * 100) if manual_avg > 0 else 0
            )

            comparison.append(
                {
                    "metric": "평균 입찰가",
                    "autoBid": round(auto_avg),
                    "manualBid": round(manual_avg),
                    "improvement": round(avg_improvement, 1),
                }
            )

            # 총 지출 비교
            auto_spent = auto_performance["total_spent"] or 0
            manual_spent = manual_performance["total_spent"] or 0
            spent_improvement = (
                ((manual_spent - auto_spent) / manual_spent * 100)
                if manual_spent > 0
                else 0
            )

            comparison.append(
                {
                    "metric": "총 지출",
                    "autoBid": round(auto_spent),
                    "manualBid": round(manual_spent),
                    "improvement": round(spent_improvement, 1),
                }
            )

            # 입찰 횟수 비교
            auto_bids = auto_performance["total_bids"] or 0
            manual_bids = manual_performance["total_bids"] or 0
            bids_improvement = (
                ((auto_bids - manual_bids) / manual_bids * 100)
                if manual_bids > 0
                else 0
            )

            comparison.append(
                {
                    "metric": "입찰 횟수",
                    "autoBid": auto_bids,
                    "manualBid": manual_bids,
                    "improvement": round(bids_improvement, 1),
                }
            )

        return comparison

    except Exception as e:
        print(f"Error getting performance comparison: {e}")
        return []


# 자동 입찰 최적화 엔드포인트


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
    """머신러닝 기반 최적 입찰가 계산"""
    try:
        advertiser_id = current_advertiser["id"]

        # 현재 시간 정보
        now = datetime.now()
        time_of_day = now.hour
        day_of_week = now.weekday()

        # 과거 성과 데이터 조회
        historical_query = f"""
            SELECT 
                AVG(CASE WHEN bid_result = 'won' THEN 1.0 ELSE 0.0 END) * 100 as historical_success_rate,
                AVG(CASE WHEN bid_result = 'won' THEN bid_amount ELSE NULL END) as avg_winning_bid
            FROM auto_bid_logs
            WHERE advertiser_id = :advertiser_id
            AND created_at >= CURRENT_DATE - INTERVAL '30 days'
        """

        historical_data = await database.fetch_one(
            historical_query, {"advertiser_id": advertiser_id}
        )

        historical_success_rate = (
            historical_data["historical_success_rate"] if historical_data else 50.0
        )
        avg_winning_bid = (
            historical_data["avg_winning_bid"] if historical_data else 1000.0
        )

        # BidContext 생성
        context = BidContext(
            search_query=search_query or "기본 검색",
            quality_score=quality_score or 50,
            match_type=MatchType(match_type),
            match_score=match_score,
            competitor_count=competitor_count,
            time_of_day=time_of_day,
            day_of_week=day_of_week,
            historical_success_rate=historical_success_rate,
            avg_winning_bid=avg_winning_bid,
            budget_remaining=budget_remaining,
        )

        # 자동 입찰 최적화기 생성
        optimizer = AutoBidOptimizer(database)

        # 최적 입찰가 계산
        optimization_result = await optimizer.get_optimal_bid(advertiser_id, context)

        return {
            "recommended_bid": optimization_result.recommended_bid,
            "confidence_score": optimization_result.confidence_score,
            "reasoning": optimization_result.reasoning,
            "expected_success_rate": optimization_result.expected_success_rate,
            "cost_efficiency": optimization_result.cost_efficiency,
            "context": {
                "search_query": context.search_query,
                "quality_score": context.quality_score,
                "match_type": context.match_type.value,
                "match_score": context.match_score,
                "competitor_count": context.competitor_count,
                "time_of_day": context.time_of_day,
                "budget_remaining": context.budget_remaining,
            },
        }

    except Exception as e:
        print(f"Error optimizing bid: {e}")
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
    """자동 입찰 실행"""
    try:
        advertiser_id = current_advertiser["id"]

        # 자동 입찰 설정 확인
        settings_query = """
            SELECT is_enabled, daily_budget, max_bid_per_keyword, min_quality_score
            FROM auto_bid_settings
            WHERE advertiser_id = :advertiser_id
        """

        settings = await database.fetch_one(
            settings_query, {"advertiser_id": advertiser_id}
        )

        if not settings or not settings["is_enabled"]:
            raise HTTPException(
                status_code=400, detail="자동 입찰이 비활성화되어 있습니다."
            )

        if quality_score < settings["min_quality_score"]:
            raise HTTPException(
                status_code=400, detail="품질 점수가 최소 기준을 만족하지 않습니다."
            )

        # 예산 확인
        budget_query = """
            SELECT 
                daily_budget,
                COALESCE(SUM(CASE WHEN bid_result = 'won' THEN bid_amount ELSE 0 END), 0) as spent_today
            FROM auto_bid_settings abs
            LEFT JOIN auto_bid_logs abl ON abs.advertiser_id = abl.advertiser_id 
                AND DATE(abl.created_at) = CURRENT_DATE
            WHERE abs.advertiser_id = :advertiser_id
            GROUP BY abs.daily_budget
        """

        budget_data = await database.fetch_one(
            budget_query, {"advertiser_id": advertiser_id}
        )

        if not budget_data:
            raise HTTPException(status_code=400, detail="예산 정보를 찾을 수 없습니다.")

        budget_remaining = budget_data["daily_budget"] - budget_data["spent_today"]

        if budget_remaining <= 0:
            raise HTTPException(status_code=400, detail="일일 예산이 소진되었습니다.")

        # 최적 입찰가 계산
        optimization_response = await optimize_bid(
            current_advertiser=current_advertiser,
            search_query=search_query,
            quality_score=quality_score,
            match_type=match_type,
            match_score=match_score,
            competitor_count=competitor_count,
            budget_remaining=budget_remaining,
        )

        recommended_bid = optimization_response["recommended_bid"]

        # 최대 입찰가 제한 확인
        if recommended_bid > settings["max_bid_per_keyword"]:
            recommended_bid = settings["max_bid_per_keyword"]

        # 예산 제한 확인
        if recommended_bid > budget_remaining:
            recommended_bid = budget_remaining

        # 입찰 실행 (실제로는 auction-service와 연동)
        bid_result = await _execute_bid_in_auction(
            advertiser_id, search_query or "기본 검색", recommended_bid
        )

        # 결과 로깅
        now = datetime.now()
        context = BidContext(
            search_query=search_query or "기본 검색",
            quality_score=quality_score or 50,
            match_type=MatchType(match_type),
            match_score=match_score,
            competitor_count=competitor_count,
            time_of_day=now.hour,
            day_of_week=now.weekday(),
            historical_success_rate=optimization_response["context"][
                "historical_success_rate"
            ],
            avg_winning_bid=optimization_response["context"]["avg_winning_bid"],
            budget_remaining=budget_remaining,
        )

        optimizer = AutoBidOptimizer(database)
        await optimizer.update_model(
            advertiser_id, BidResult(bid_result), recommended_bid, context
        )

        return {
            "success": True,
            "bid_amount": recommended_bid,
            "bid_result": bid_result,
            "confidence_score": optimization_response["confidence_score"],
            "reasoning": optimization_response["reasoning"],
            "budget_remaining": budget_remaining - recommended_bid,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error executing auto bid: {e}")
        raise HTTPException(status_code=500, detail=f"자동 입찰 실행 실패: {str(e)}")


async def _execute_bid_in_auction(
    advertiser_id: int, search_query: str, bid_amount: int
) -> str:
    """경매 서비스에서 입찰 실행 (시뮬레이션)"""
    try:
        # 실제로는 auction-service와 연동
        # 여기서는 시뮬레이션으로 성공/실패 결정

        # 성공률 시뮬레이션 (실제로는 경매 결과에 따라 결정)
        success_probability = 0.6  # 60% 성공률

        if random.random() < success_probability:
            return "won"
        else:
            return "lost"

    except Exception as e:
        print(f"Error executing bid in auction: {e}")
        return "timeout"


@app.get("/business-categories")
async def get_business_categories():
    """비즈니스 카테고리 목록 조회"""
    try:
        # 데이터베이스에서 카테고리 조회
        categories = await database.fetch_all(
            """
            SELECT id, parent_id, name, path, level, is_active, sort_order, created_at
            FROM business_categories 
            WHERE is_active = true 
            ORDER BY level, sort_order, name
            """
        )

        if not categories:
            # 기본 카테고리 데이터 반환
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
                {
                    "id": 6,
                    "parent_id": 1,
                    "name": "스마트폰",
                    "path": "electronics/smartphones",
                    "level": 2,
                    "is_active": True,
                    "sort_order": 1,
                },
                {
                    "id": 7,
                    "parent_id": 1,
                    "name": "노트북",
                    "path": "electronics/laptops",
                    "level": 2,
                    "is_active": True,
                    "sort_order": 2,
                },
                {
                    "id": 8,
                    "parent_id": 2,
                    "name": "남성의류",
                    "path": "clothing/mens",
                    "level": 2,
                    "is_active": True,
                    "sort_order": 1,
                },
                {
                    "id": 9,
                    "parent_id": 2,
                    "name": "여성의류",
                    "path": "clothing/womens",
                    "level": 2,
                    "is_active": True,
                    "sort_order": 2,
                },
                {
                    "id": 10,
                    "parent_id": 3,
                    "name": "신선식품",
                    "path": "food/fresh",
                    "level": 2,
                    "is_active": True,
                    "sort_order": 1,
                },
                {
                    "id": 11,
                    "parent_id": 3,
                    "name": "가공식품",
                    "path": "food/processed",
                    "level": 2,
                    "is_active": True,
                    "sort_order": 2,
                },
            ]

        return categories

    except Exception as e:
        print(f"Error fetching business categories: {e}")
        # 에러 시 기본 카테고리 반환
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


@app.delete("/admin/delete-advertiser/{advertiser_id}")
async def delete_advertiser(advertiser_id: int):
    """광고주 완전 삭제 (거절된 광고주만)"""
    try:
        # 광고주가 거절 상태인지 확인
        review_status = await database.fetch_val(
            "SELECT review_status FROM advertiser_reviews WHERE advertiser_id = :advertiser_id",
            {"advertiser_id": advertiser_id},
        )

        if not review_status:
            raise HTTPException(status_code=404, detail="Advertiser not found")

        if review_status != "rejected":
            raise HTTPException(
                status_code=400, detail="Only rejected advertisers can be deleted"
            )

        # 트랜잭션으로 모든 관련 데이터 삭제
        async with database.transaction():
            # 관련 테이블에서 데이터 삭제 (CASCADE로 자동 삭제됨)
            await database.execute(
                "DELETE FROM advertisers WHERE id = :advertiser_id",
                {"advertiser_id": advertiser_id},
            )

        return {"success": True, "message": "Advertiser deleted successfully"}

    except Exception as e:
        print(f"Error deleting advertiser: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete advertiser: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8007)
