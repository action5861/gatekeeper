import math
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Literal
from dataclasses import dataclass
from enum import Enum

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
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
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# bcrypt 버전 호환성을 위한 설정 수정
try:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
except Exception as e:
    print(f"Bcrypt 초기화 오류: {e}")
    # 대안으로 sha256_crypt 사용
    pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

security = HTTPBearer()


# Pydantic 모델
class PerformanceHistory(BaseModel):
    name: str
    score: int


class BiddingSummary(BaseModel):
    totalBids: int
    successfulBids: int
    totalSpent: int
    averageBidAmount: float


class DashboardResponse(BaseModel):
    biddingSummary: BiddingSummary
    performanceHistory: List[PerformanceHistory]
    recentBids: List[dict]


class BusinessSetupData(BaseModel):
    websiteUrl: str
    keywords: List[str]
    categories: List[int]
    dailyBudget: int
    bidRange: dict


class AdvertiserRegister(BaseModel):
    username: str
    email: str
    password: str
    company_name: str
    business_setup: Optional[BusinessSetupData] = None


class AdvertiserLogin(BaseModel):
    username: str
    password: str


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

        # 2. 카테고리 저장
        for category_id in business_setup.categories:
            # 카테고리 정보 조회
            category_info = await database.fetch_one(
                "SELECT name, path, level FROM business_categories WHERE id = :category_id",
                {"category_id": category_id},
            )

            if category_info:
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

        print(f"Business setup data saved for advertiser_id: {advertiser_id}")

    except Exception as e:
        print(f"Error saving business setup data: {e}")
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
    """관리자: 심사 대기 중인 광고주 목록 조회"""
    try:
        # 심사 대기 중인 광고주 조회
        query = """
        SELECT 
            ar.id,
            ar.advertiser_id,
            a.company_name,
            a.email,
            a.website_url,
            a.daily_budget,
            a.created_at,
            ar.review_status,
            ar.review_notes,
            ar.recommended_bid_min,
            ar.recommended_bid_max
        FROM advertiser_reviews ar
        JOIN advertisers a ON ar.advertiser_id = a.id
        WHERE ar.review_status = 'pending'
        ORDER BY ar.created_at ASC
        """

        reviews = await database.fetch_all(query)

        # 각 광고주의 키워드와 카테고리 정보 조회
        advertisers_data = []
        for review in reviews:
            # 키워드 조회
            keywords_query = """
            SELECT keyword FROM advertiser_keywords 
            WHERE advertiser_id = :advertiser_id
            """
            keywords_result = await database.fetch_all(
                keywords_query, {"advertiser_id": review["advertiser_id"]}
            )
            keywords = [row["keyword"] for row in keywords_result]

            # 카테고리 조회
            categories_query = """
            SELECT category_path FROM advertiser_categories 
            WHERE advertiser_id = :advertiser_id
            """
            categories_result = await database.fetch_all(
                categories_query, {"advertiser_id": review["advertiser_id"]}
            )
            categories = [row["category_path"] for row in categories_result]

            advertisers_data.append(
                {
                    "id": review["id"],
                    "advertiser_id": review["advertiser_id"],
                    "company_name": review["company_name"],
                    "email": review["email"],
                    "website_url": review["website_url"],
                    "daily_budget": float(review["daily_budget"]),
                    "created_at": review["created_at"].isoformat(),
                    "keywords": keywords,
                    "categories": categories,
                    "review_status": review["review_status"],
                    "review_notes": review["review_notes"],
                    "recommended_bid_min": review["recommended_bid_min"],
                    "recommended_bid_max": review["recommended_bid_max"],
                }
            )

        return {"advertisers": advertisers_data}

    except Exception as e:
        print(f"Error fetching pending reviews: {e}")
        raise HTTPException(
            status_code=500, detail=f"심사 대기 목록 조회 실패: {str(e)}"
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

        # 최근 입찰 내역 가져오기 (심사 승인된 경우에만)
        recent_bids = []
        if review_status == "approved":
            recent_bids = await get_recent_bids()
        print(f"Dashboard returning bids: {len(recent_bids)}")

        # 입찰 요약 계산 (시뮬레이션 데이터)
        total_bids = 150 if review_status == "approved" else 0
        successful_bids = 120 if review_status == "approved" else 0
        total_spent = 45000 if review_status == "approved" else 0
        average_bid_amount = total_spent / total_bids if total_bids > 0 else 0

        bidding_summary = BiddingSummary(
            totalBids=total_bids,
            successfulBids=successful_bids,
            totalSpent=total_spent,
            averageBidAmount=round(average_bid_amount, 2),
        )

        return DashboardResponse(
            biddingSummary=bidding_summary,
            performanceHistory=[
                PerformanceHistory(name="Week 1", score=65),
                PerformanceHistory(name="Week 2", score=70),
                PerformanceHistory(name="Week 3", score=72),
                PerformanceHistory(name="Week 4", score=75),
            ],
            recentBids=recent_bids,
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8007)
