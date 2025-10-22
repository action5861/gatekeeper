from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, validator, Field
from typing import List, Literal, Optional
import os
import re
import html
import random
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from database import (
    database,
    User,
    UserQualityHistory,
    connect_to_database,
    disconnect_from_database,
)
import json

app = FastAPI(title="User Service", version="1.0.0")


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

# 보안 설정
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# 입력값 검증 함수들
def sanitize_input(value: str, is_url: bool = False) -> str:
    """XSS 방지를 위한 입력값 이스케이핑"""
    if not isinstance(value, str):
        return str(value)

    value = value.strip()

    # URL인 경우 특수 문자 보존
    if is_url:
        # URL에서 허용되는 특수 문자들을 보존
        # : / ? & = # 등은 URL에서 필수이므로 이스케이프하지 않음
        return value

    # 일반 텍스트는 HTML 이스케이프 적용
    return html.escape(value)


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


# Pydantic 모델들
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="사용자명")
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=8, max_length=128, description="비밀번호")

    @validator("username")
    def validate_username(cls, v):
        v = v.strip()  # sanitize_input 대신 strip만 사용
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


class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., description="비밀번호")

    @validator("email")
    def validate_email(cls, v):
        v = sanitize_input(v.lower())
        if not validate_sql_injection(v):
            raise ValueError("이메일에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("password")
    def validate_password(cls, v):
        if not validate_sql_injection(v):
            raise ValueError("비밀번호에 허용되지 않는 문자가 포함되어 있습니다")
        return v


class Token(BaseModel):
    access_token: str
    token_type: str


class QualityHistory(BaseModel):
    name: str = Field(..., max_length=100)
    score: int = Field(..., ge=0, le=100)

    @validator("name")
    def validate_name(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("이름에 허용되지 않는 문자가 포함되어 있습니다")
        return v


class SubmissionLimit(BaseModel):
    level: Literal[
        "Excellent",
        "Very Good",
        "Good",
        "Average",
        "Below Average",
        "Poor",
        "Very Poor",
        "Standard",  # 임시로 추가
    ]
    dailyMax: int = Field(..., ge=0, le=1000)


class DashboardResponse(BaseModel):
    earnings: dict
    qualityHistory: List[QualityHistory]
    qualityStats: dict
    submissionLimit: SubmissionLimit
    dailySubmission: dict
    stats: dict
    transactions: List[dict]


class DetailedEarningsRequest(BaseModel):
    """Enhanced earnings request with detailed transaction information"""

    userId: Optional[str] = Field(
        None, description="User ID (optional, will use JWT if not provided)"
    )
    amount: int = Field(..., ge=0, le=1000000, description="Reward amount")
    query: Optional[str] = Field(None, max_length=500, description="Search query")
    adType: Optional[str] = Field(None, description="Ad type (bidded/fallback)")
    searchId: Optional[str] = Field(None, max_length=100, description="Search ID")
    bidId: Optional[str] = Field(None, max_length=100, description="Bid ID")

    @validator("query")
    def validate_query(cls, v):
        if v:
            v = sanitize_input(v)
            if not validate_sql_injection(v):
                raise ValueError("검색어에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("searchId", "bidId")
    def validate_id(cls, v):
        if v:
            v = sanitize_input(v)
            if not re.match(r"^[가-힣a-zA-Z0-9_-]+$", v):
                raise ValueError(
                    "ID는 한글, 영문, 숫자, 언더스코어, 하이픈만 사용 가능합니다"
                )
            if not validate_sql_injection(v):
                raise ValueError("ID에 허용되지 않는 문자가 포함되어 있습니다")
        return v


class QualityScoreRequest(BaseModel):
    score: int = Field(..., ge=0, le=100)
    week_label: str = Field(..., max_length=50)

    @validator("week_label")
    def validate_week_label(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("주차 라벨에 허용되지 않는 문자가 포함되어 있습니다")
        return v


class SubmissionRequest(BaseModel):
    quality_score: int = Field(..., ge=0, le=100)


class SearchCompletedRequest(BaseModel):
    query: str = Field(..., max_length=500)
    quality_score: int = Field(..., ge=0, le=100)
    commercial_value: str = Field(..., max_length=100)
    keywords: dict
    suggestions: dict
    auction_id: str = Field(..., max_length=100)

    @validator("query")
    def validate_query(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("검색어에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("commercial_value")
    def validate_commercial_value(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("상업적 가치에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("auction_id")
    def validate_auction_id(cls, v):
        v = sanitize_input(v)
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "경매 ID는 영문, 숫자, 언더스코어, 하이픈만 사용 가능합니다"
            )
        if not validate_sql_injection(v):
            raise ValueError("경매 ID에 허용되지 않는 문자가 포함되어 있습니다")
        return v


class AuctionCompletedRequest(BaseModel):
    search_id: str = Field(..., max_length=100)
    selected_bid_id: str = Field(..., max_length=100)
    reward_amount: int = Field(..., ge=0, le=1000000)

    @validator("search_id", "selected_bid_id")
    def validate_id(cls, v):
        v = sanitize_input(v)
        # 한글, 영문, 숫자, 언더스코어, 하이픈을 허용하도록 수정
        if not re.match(r"^[가-힣a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "ID는 한글, 영문, 숫자, 언더스코어, 하이픈만 사용 가능합니다"
            )
        if not validate_sql_injection(v):
            raise ValueError("ID에 허용되지 않는 문자가 포함되어 있습니다")
        return v


class TxRecord(BaseModel):
    userId: int
    transactionId: str
    amount: int
    source: str
    reason: str


# 🔐 보안 함수들
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})

    # JWT 표준 클레임 추가
    to_encode.update(
        {
            "iss": os.getenv("JWT_ISSUER", "digisafe-api"),
            "aud": os.getenv("JWT_AUDIENCE", "digisafe-client"),
        }
    )

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def calculate_dynamic_limit(quality_score: int) -> SubmissionLimit:
    """일일 제출 한도를 환경 변수에서 가져옵니다."""
    # 환경 변수에서 일일 한도 가져오기 (기본값: 5)
    daily_limit = int(os.getenv("DEFAULT_DAILY_LIMIT", "5"))
    # 모든 사용자에게 동일하게 하루 제출 한도 제공
    # 추후 quality_score에 따라 동적으로 변경 가능
    return SubmissionLimit(level="Standard", dailyMax=daily_limit)


# 🔥 새로운 헬퍼 함수들 - 트랜잭션 기준으로 통일
async def _used_today_from_tx(user_id: int) -> int:
    """오늘 생성된 트랜잭션 수를 기준으로 사용량 계산"""
    row = await database.fetch_one(
        """
        SELECT COUNT(*) AS c
        FROM transactions
        WHERE user_id = :uid
          AND created_at::date = CURRENT_DATE
        """,
        {"uid": user_id},
    )
    return int(row["c"] or 0) if row else 0


async def _today_quality_avg(user_id: int) -> int:
    """오늘의 품질 점수 평균 계산"""
    row = await database.fetch_one(
        """
        SELECT AVG(quality_score) AS avg_q
        FROM search_queries
        WHERE user_id = :uid
          AND created_at::date = CURRENT_DATE
        """,
        {"uid": user_id},
    )
    return int(round(float(row["avg_q"])) if row and row["avg_q"] is not None else 50)


async def _remaining_from_tx(user_id: int, quality_score: int = 0) -> dict:
    """트랜잭션 기준으로 남은 사용량 계산"""
    limit = calculate_dynamic_limit(quality_score).dailyMax
    used = await _used_today_from_tx(user_id)
    return {
        "count": used,
        "limit": limit,
        "remaining": max(0, limit - used),
        "qualityScoreAvg": await _today_quality_avg(user_id),
    }


# JWT 인증 함수
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=(
                os.getenv("JWT_AUDIENCE", "digisafe-client")
                if os.getenv("JWT_AUDIENCE")
                else None
            ),
            issuer=(
                os.getenv("JWT_ISSUER", "digisafe-api")
                if os.getenv("JWT_ISSUER")
                else None
            ),
            options={
                "require_exp": True,
                "verify_aud": bool(os.getenv("JWT_AUDIENCE")),
                "verify_iss": bool(os.getenv("JWT_ISSUER")),
            },
        )
        email = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await database.fetch_one(
        "SELECT * FROM users WHERE email = :email", {"email": email}
    )
    if user is None:
        raise credentials_exception
    return dict(user)


# 📊 API 엔드포인트들
@app.post("/register", status_code=201)
async def register_user(user: UserCreate):
    """신규 사용자 등록"""
    try:
        print(
            f"📝 Registration attempt for email: {user.email}, username: {user.username}"
        )

        # 이메일 중복 확인
        print("🔍 Checking email duplication...")
        existing_user = await database.fetch_one(
            "SELECT id FROM users WHERE email = :email", {"email": user.email}
        )
        if existing_user:
            print(f"❌ Email already exists: {user.email}")
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

        # 사용자명 중복 확인
        print("🔍 Checking username duplication...")
        existing_username = await database.fetch_one(
            "SELECT id FROM users WHERE username = :username",
            {"username": user.username},
        )
        if existing_username:
            print(f"❌ Username already exists: {user.username}")
            raise HTTPException(
                status_code=400, detail="이미 사용 중인 사용자명입니다."
            )

        # 비밀번호 해싱
        print("🔐 Hashing password...")
        hashed_password = get_password_hash(user.password)

        # 사용자 생성
        print("💾 Creating user in database...")
        query = """
        INSERT INTO users (username, email, hashed_password) 
        VALUES (:username, :email, :hashed_password)
        """
        await database.execute(
            query,
            {
                "username": user.username,
                "email": user.email,
                "hashed_password": hashed_password,
            },
        )

        print(f"✅ Registration successful for: {user.email}")
        return {"message": "회원가입이 성공적으로 완료되었습니다."}

    except Exception as e:
        print(f"💥 Registration error: {str(e)}")
        print(f"💥 Error type: {type(e)}")
        import traceback

        print(f"💥 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"등록 실패: {str(e)}")


@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: UserLogin):
    """사용자 로그인 및 JWT 토큰 발급"""
    try:
        print(f"🔐 Login attempt for email: {form_data.email}")

        # 사용자 조회
        user = await database.fetch_one(
            "SELECT * FROM users WHERE email = :email", {"email": form_data.email}
        )

        print(f"👤 User found: {user is not None}")

        if not user:
            print("❌ User not found")
            raise HTTPException(
                status_code=401,
                detail="이메일 또는 비밀번호가 잘못되었습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 비밀번호 검증
        password_valid = verify_password(form_data.password, user["hashed_password"])
        print(f"🔑 Password valid: {password_valid}")

        if not password_valid:
            print("❌ Invalid password")
            raise HTTPException(
                status_code=401,
                detail="이메일 또는 비밀번호가 잘못되었습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 토큰 생성
        print("🎫 Creating access token...")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={
                "sub": user["email"],
                "user_id": user["id"],
                "username": (
                    user["username"]
                    if "username" in user
                    else user["email"].split("@")[0]
                ),
                "userType": "user",
            },
            expires_delta=access_token_expires,
        )
        print("✅ Login successful")
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        print(f"💥 Login error: {str(e)}")
        print(f"💥 Error type: {type(e)}")
        import traceback

        print(f"💥 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"로그인 실패: {str(e)}")


@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """🔥 JWT에서 실제 사용자 ID 추출하여 개인화 대시보드 제공"""
    try:
        user_id = current_user["id"]  # 🚨 하드코딩 완전 제거!
        print(
            f"🎯 Dashboard request for REAL user ID: {user_id} (email: {current_user['email']})"
        )

        # 1. 실제 사용자별 수익 계산 (이번달, 지난달, 전체)
        # ⭐ 중요: SETTLED 상태의 거래만 수익으로 계산 (PENDING_VERIFICATION 제외)
        earnings_query = """
        SELECT 
            -- 전체 수익 (정산 완료된 거래만)
            COALESCE(SUM(CASE WHEN status IN ('SETTLED', '1차 완료', '2차 완료') THEN primary_reward ELSE 0 END), 0) as primary_total,
            COALESCE(SUM(CASE WHEN status IN ('SETTLED', '1차 완료', '2차 완료') THEN secondary_reward ELSE 0 END), 0) as secondary_total,
            COALESCE(SUM(CASE WHEN status IN ('SETTLED', '1차 완료', '2차 완료') THEN primary_reward + COALESCE(secondary_reward, 0) ELSE 0 END), 0) as total,
            
            -- 이번달 수익 (정산 완료된 거래만)
            COALESCE(SUM(CASE 
                WHEN DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE) 
                AND status IN ('SETTLED', '1차 완료', '2차 완료')
                THEN primary_reward ELSE 0 END), 0) as this_month_primary,
            COALESCE(SUM(CASE 
                WHEN DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE) 
                AND status IN ('SETTLED', '1차 완료', '2차 완료')
                THEN secondary_reward ELSE 0 END), 0) as this_month_secondary,
            COALESCE(SUM(CASE 
                WHEN DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE) 
                AND status IN ('SETTLED', '1차 완료', '2차 완료')
                THEN primary_reward + COALESCE(secondary_reward, 0) ELSE 0 END), 0) as this_month_total,
            
            -- 지난달 수익 (정산 완료된 거래만)
            COALESCE(SUM(CASE 
                WHEN DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') 
                AND status IN ('SETTLED', '1차 완료', '2차 완료')
                THEN primary_reward ELSE 0 END), 0) as last_month_primary,
            COALESCE(SUM(CASE 
                WHEN DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') 
                AND status IN ('SETTLED', '1차 완료', '2차 완료')
                THEN secondary_reward ELSE 0 END), 0) as last_month_secondary,
            COALESCE(SUM(CASE 
                WHEN DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') 
                AND status IN ('SETTLED', '1차 완료', '2차 완료')
                THEN primary_reward + COALESCE(secondary_reward, 0) ELSE 0 END), 0) as last_month_total
        FROM transactions 
        WHERE user_id = :user_id
        """
        earnings_result = await database.fetch_one(earnings_query, {"user_id": user_id})

        # earnings_result가 None인 경우 기본값 설정
        if earnings_result is None:
            earnings_result = {
                "primary_total": 0,
                "secondary_total": 0,
                "total": 0,
                "this_month_primary": 0,
                "this_month_secondary": 0,
                "this_month_total": 0,
                "last_month_primary": 0,
                "last_month_secondary": 0,
                "last_month_total": 0,
            }

        # 월별 성장률 계산
        this_month_total = int(earnings_result["this_month_total"] or 0)
        last_month_total = int(earnings_result["last_month_total"] or 0)

        if last_month_total > 0:
            growth_rate = (
                (this_month_total - last_month_total) / last_month_total
            ) * 100
            growth_percentage = f"{growth_rate:+.1f}%"
            is_positive_growth = growth_rate >= 0
        else:
            growth_percentage = "N/A"
            is_positive_growth = True

        print(f"💰 User {user_id} earnings: {dict(earnings_result)}")
        print(
            f"📈 Growth: {growth_percentage} (this month: {this_month_total}, last month: {last_month_total})"
        )

        # 2. 사용자별 품질 이력 조회 (최근 4주간)
        quality_history = await database.fetch_all(
            """
            SELECT 
                week_label as name, 
                quality_score as score,
                recorded_at
            FROM user_quality_history 
            WHERE user_id = :user_id 
            ORDER BY recorded_at DESC LIMIT 4
            """,
            {"user_id": user_id},
        )

        # 품질 통계 계산
        if quality_history:
            scores = [row["score"] for row in quality_history]
            average_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)

            # 성장률 계산 (최신 vs 이전)
            if len(scores) >= 2:
                recent_score = scores[0]
                previous_score = scores[1]
                if previous_score > 0:
                    growth_rate = (
                        (recent_score - previous_score) / previous_score
                    ) * 100
                    growth_percentage = f"{growth_rate:+.1f}%"
                    is_positive_growth = growth_rate >= 0
                else:
                    growth_percentage = "N/A"
                    is_positive_growth = True
            else:
                growth_percentage = "N/A"
                is_positive_growth = True
        else:
            average_score = 75
            max_score = 75
            min_score = 75
            growth_percentage = "N/A"
            is_positive_growth = True

        # 3. 현재 사용자 품질 점수
        current_user_data = await database.fetch_one(
            "SELECT quality_score FROM users WHERE id = :user_id", {"user_id": user_id}
        )
        quality_score = current_user_data["quality_score"] if current_user_data else 75

        # 4. 트랜잭션 기준으로 일일 사용량 계산 (기존 daily_submissions 대신)
        submission_limit = calculate_dynamic_limit(quality_score)
        daily_submission = await _remaining_from_tx(user_id, quality_score)

        # 5. 사용자별 거래 내역 조회 (광고주 이름 포함)
        transactions = await database.fetch_all(
            """
            SELECT 
                t.id, 
                t.query_text as query, 
                COALESCE(a.company_name, t.buyer_name) as "buyerName",
                t.primary_reward as "primaryReward", 
                t.secondary_reward as "secondaryReward",
                t.status, 
                t.created_at as timestamp
            FROM transactions t
            LEFT JOIN bids b ON t.bid_id = b.id
            LEFT JOIN advertisers a ON b.advertiser_id = a.id
            WHERE t.user_id = :user_id
            ORDER BY t.created_at DESC
            """,
            {"user_id": user_id},
        )
        print(f"📊 User {user_id} has {len(transactions)} transactions")

        # 6. 추가 통계 계산
        # 이번달 검색 횟수
        monthly_searches = await database.fetch_one(
            """
            SELECT COUNT(*) as count
            FROM search_queries 
            WHERE user_id = :user_id 
            AND created_at >= date_trunc('month', CURRENT_DATE)
            """,
            {"user_id": user_id},
        )
        monthly_search_count = (
            int(monthly_searches["count"] or 0) if monthly_searches else 0
        )

        # 경매 성공률
        auction_stats = await database.fetch_one(
            """
            SELECT 
                COUNT(*) as total_auctions,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_auctions
            FROM auctions 
            WHERE user_id = :user_id
            """,
            {"user_id": user_id},
        )

        if (
            auction_stats
            and auction_stats["total_auctions"]
            and auction_stats["total_auctions"] > 0
        ):
            success_rate = round(
                (auction_stats["completed_auctions"] / auction_stats["total_auctions"])
                * 100,
                1,
            )
        else:
            success_rate = 0.0

        # 평균 품질 점수
        avg_quality = await database.fetch_one(
            """
            SELECT AVG(quality_score) as avg_score
            FROM search_queries 
            WHERE user_id = :user_id
            """,
            {"user_id": user_id},
        )
        average_quality_score = (
            round(float(avg_quality["avg_score"] or 0), 1) if avg_quality else 0.0
        )

        print(
            f"📈 User {user_id} stats: searches={monthly_search_count}, success_rate={success_rate}%, avg_quality={average_quality_score}"
        )

        # 7. 응답 데이터 구성
        response_data = DashboardResponse(
            earnings={
                "total": int(earnings_result["total"] or 0),
                "primary": int(earnings_result["primary_total"] or 0),
                "secondary": int(earnings_result["secondary_total"] or 0),
                "thisMonth": {
                    "total": int(earnings_result["this_month_total"] or 0),
                    "primary": int(earnings_result["this_month_primary"] or 0),
                    "secondary": int(earnings_result["this_month_secondary"] or 0),
                },
                "lastMonth": {
                    "total": int(earnings_result["last_month_total"] or 0),
                    "primary": int(earnings_result["last_month_primary"] or 0),
                    "secondary": int(earnings_result["last_month_secondary"] or 0),
                },
                "growth": {
                    "percentage": growth_percentage,
                    "isPositive": is_positive_growth,
                },
            },
            qualityHistory=(
                [
                    QualityHistory(name=row["name"], score=row["score"])
                    for row in quality_history
                ]
                if quality_history
                else [
                    QualityHistory(name="Week 1", score=65),
                    QualityHistory(name="Week 2", score=70),
                    QualityHistory(name="Week 3", score=72),
                    QualityHistory(name="Week 4", score=quality_score),
                ]
            ),
            qualityStats={
                "average": round(average_score, 1),
                "max": max_score,
                "min": min_score,
                "growth": {
                    "percentage": growth_percentage,
                    "isPositive": is_positive_growth,
                },
                "recentScore": (
                    quality_history[0]["score"] if quality_history else quality_score
                ),
            },
            submissionLimit=submission_limit,
            dailySubmission=daily_submission,
            stats={
                "monthlySearches": monthly_search_count,
                "successRate": success_rate,
                "avgQualityScore": average_quality_score,
            },
            transactions=[
                {
                    "id": row["id"],
                    "query": row["query"],
                    "buyerName": row["buyerName"],
                    "primaryReward": int(row["primaryReward"]),
                    "secondaryReward": (
                        int(row["secondaryReward"]) if row["secondaryReward"] else None
                    ),
                    "status": row["status"],
                    "timestamp": (
                        row["timestamp"].isoformat()
                        if row["timestamp"]
                        else datetime.now().isoformat()
                    ),
                }
                for row in transactions
            ],
        )

        print(
            f"✅ Returning dashboard for user {user_id}: earnings={response_data.earnings}"
        )
        return response_data

    except Exception as e:
        print(f"❌ Dashboard error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")


@app.post("/quality-score")
async def update_quality_score(
    request: QualityScoreRequest, current_user: dict = Depends(get_current_user)
):
    """품질 점수 업데이트 및 이력 저장"""
    try:
        user_id = current_user["id"]
        score = request.score
        week_label = request.week_label

        print(f"📊 Updating quality score for user {user_id}: {score} ({week_label})")

        # 1. 현재 사용자의 품질 점수 업데이트
        await database.execute(
            "UPDATE users SET quality_score = :score WHERE id = :user_id",
            {"score": score, "user_id": user_id},
        )

        # 2. 품질 이력에 저장
        await database.execute(
            """
            INSERT INTO user_quality_history (user_id, week_label, quality_score, recorded_at)
            VALUES (:user_id, :week_label, :score, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, week_label) 
            DO UPDATE SET 
                quality_score = :score,
                recorded_at = CURRENT_TIMESTAMP
            """,
            {"user_id": user_id, "week_label": week_label, "score": score},
        )

        print(f"✅ Successfully updated quality score for user {user_id}")
        return {
            "success": True,
            "message": "품질 점수가 업데이트되었습니다.",
            "user_id": user_id,
            "score": score,
            "week_label": week_label,
        }

    except Exception as e:
        print(f"❌ Quality score update error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/update-daily-submission")
async def update_daily_submission(
    request: SubmissionRequest, current_user: dict = Depends(get_current_user)
):
    """
    일일 제출 카운트를 업데이트합니다. (계산 로직 수정 및 안정화 버전)
    """
    user_id = current_user["id"]
    quality_score = request.quality_score
    today = datetime.now().date()

    print(
        f"📝 Updating daily submission for user {user_id} with quality score {quality_score}"
    )

    try:
        # 트랜잭션 시작 (선택적이지만 데이터 정합성에 좋음)
        async with database.transaction():
            # 1. 오늘 날짜의 기록을 먼저 조회합니다.
            existing_record = await database.fetch_one(
                """
                SELECT id, submission_count, quality_score_avg
                FROM daily_submissions 
                WHERE user_id = :user_id AND submission_date = :today
                """,
                {"user_id": user_id, "today": today},
            )

            if existing_record:
                # 2-A. 기록이 있으면, 카운트를 1 증가시키고 평균 점수를 다시 계산합니다.
                current_count = existing_record["submission_count"]
                current_avg = existing_record["quality_score_avg"]

                new_count = current_count + 1
                new_avg = round(
                    ((current_avg * current_count) + quality_score) / new_count, 1
                )

                await database.execute(
                    """
                    UPDATE daily_submissions 
                    SET submission_count = :new_count, quality_score_avg = :new_avg
                    WHERE id = :record_id
                    """,
                    {
                        "new_count": new_count,
                        "new_avg": new_avg,
                        "record_id": existing_record["id"],
                    },
                )
                updated_count = new_count
            else:
                # 2-B. 기록이 없으면, 새로운 기록을 생성합니다.
                await database.execute(
                    """
                    INSERT INTO daily_submissions (user_id, submission_date, submission_count, quality_score_avg)
                    VALUES (:user_id, :today, 1, :quality_score)
                    """,
                    {
                        "user_id": user_id,
                        "today": today,
                        "quality_score": quality_score,
                    },
                )
                updated_count = 1

        # 3. 사용자의 현재 품질 점수를 기준으로 제출 한도를 다시 계산합니다.
        user_quality_score_record = await database.fetch_one(
            "SELECT quality_score FROM users WHERE id = :user_id", {"user_id": user_id}
        )
        current_quality_score = (
            user_quality_score_record["quality_score"]
            if user_quality_score_record
            else 75
        )
        submission_limit = calculate_dynamic_limit(current_quality_score)

        # 4. 최종적으로 남은 작업량을 계산하여 응답을 구성합니다.
        remaining = max(0, submission_limit.dailyMax - updated_count)

        # 최종 품질 점수 평균 조회
        final_quality_record = await database.fetch_one(
            "SELECT quality_score_avg FROM daily_submissions WHERE user_id = :user_id AND submission_date = :today",
            {"user_id": user_id, "today": today},
        )
        final_quality_avg = (
            final_quality_record["quality_score_avg"]
            if final_quality_record
            else quality_score
        )

        daily_submission_status = {
            "count": updated_count,
            "limit": submission_limit.dailyMax,
            "remaining": remaining,
            "qualityScoreAvg": final_quality_avg,
        }

        print(
            f"✅ Daily submission updated for user {user_id}: {daily_submission_status}"
        )

        return {
            "success": True,
            "message": "일일 제출 카운트가 업데이트되었습니다.",
            "dailySubmission": daily_submission_status,
        }

    except Exception as e:
        import traceback

        print(f"❌ Update daily submission error for user {user_id}: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search-completed")
async def search_completed(
    request: SearchCompletedRequest, current_user: dict = Depends(get_current_user)
):
    """검색 완료 시 데이터 저장 (제출 횟수 카운트 제외)"""
    try:
        user_id = current_user["id"]

        print(f"🔍 Search completed for user {user_id} (Data logging only)")
        print(f"   Query: {request.query}")

        # 1. search_queries 테이블에 검색 데이터 저장
        await database.execute(
            """
            INSERT INTO search_queries (user_id, query_text, quality_score, commercial_value, keywords, suggestions)
            VALUES (:user_id, :query, :quality_score, :commercial_value, :keywords, :suggestions)
            """,
            {
                "user_id": user_id,
                "query": request.query,
                "quality_score": request.quality_score,
                "commercial_value": request.commercial_value,
                "keywords": json.dumps(request.keywords),
                "suggestions": json.dumps(request.suggestions),
            },
        )

        # 2. 품질 이력에 저장 (주차별)
        from datetime import datetime

        current_week = f"Week {datetime.now().isocalendar()[1]}"
        await database.execute(
            """
            INSERT INTO user_quality_history (user_id, week_label, quality_score, recorded_at)
            VALUES (:user_id, :week_label, :quality_score, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, week_label) 
            DO UPDATE SET 
                quality_score = :quality_score,
                recorded_at = CURRENT_TIMESTAMP
            """,
            {
                "user_id": user_id,
                "week_label": current_week,
                "quality_score": request.quality_score,
            },
        )

        # ❗️❗️❗️ REMOVED ❗️❗️❗️
        # 아래 두 개의 카운트 업데이트 로직이 의도적으로 제거되었습니다.
        # - daily_submissions 업데이트
        # - users 테이블의 submission_count 업데이트

        print(
            f"✅ Search data saved for user {user_id}. Submission count is not affected."
        )
        return {
            "success": True,
            "message": "검색 데이터가 저장되었습니다. 제출 횟수는 변경되지 않습니다.",
            "user_id": user_id,
        }

    except Exception as e:
        print(f"❌ Search completed error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/auction-completed")
async def auction_completed(
    request: AuctionCompletedRequest, current_user: dict = Depends(get_current_user)
):
    """경매 완료 시 상태 업데이트 및 거래 내역 생성"""
    try:
        user_id = current_user["id"]

        print(f"🏆 Auction completed for user {user_id}: {request.search_id}")

        # 1. 경매 상태를 'completed'로 업데이트
        await database.execute(
            """
            UPDATE auctions 
            SET status = 'completed', selected_bid_id = :selected_bid_id
            WHERE search_id = :search_id AND user_id = :user_id
            """,
            {
                "search_id": request.search_id,
                "selected_bid_id": request.selected_bid_id,
                "user_id": user_id,
            },
        )

        # 2. 선택된 입찰 정보 가져오기
        bid_info = await database.fetch_one(
            """
            SELECT buyer_name, price, bonus_description, landing_url, advertiser_id
            FROM bids 
            WHERE id = :bid_id
            """,
            {"bid_id": request.selected_bid_id},
        )

        if not bid_info:
            raise HTTPException(
                status_code=404, detail="선택된 입찰 정보를 찾을 수 없습니다."
            )

        # 3. 거래 내역 생성
        transaction_id = f"TXN_{request.search_id}_{int(datetime.now().timestamp())}"

        await database.execute(
            """
            INSERT INTO transactions (
                id, user_id, auction_id, bid_id, advertiser_id, query_text, buyer_name, 
                primary_reward, status, created_at
            )
            VALUES (
                :transaction_id, :user_id, 
                (SELECT id FROM auctions WHERE search_id = :search_id),
                :bid_id, :advertiser_id,
                (SELECT query_text FROM auctions WHERE search_id = :search_id),
                :buyer_name, :primary_reward, '1차 완료', CURRENT_TIMESTAMP
            )
            """,
            {
                "transaction_id": transaction_id,
                "user_id": user_id,
                "search_id": request.search_id,
                "bid_id": request.selected_bid_id,
                "advertiser_id": (
                    bid_info["advertiser_id"]
                    if bid_info["advertiser_id"] is not None
                    else None
                ),
                "buyer_name": bid_info["buyer_name"],
                "primary_reward": request.reward_amount,
            },
        )

        # 4. 사용자의 총 수익 업데이트
        await database.execute(
            """
            UPDATE users 
            SET total_earnings = total_earnings + :reward_amount 
            WHERE id = :user_id
            """,
            {
                "user_id": user_id,
                "reward_amount": request.reward_amount,
            },
        )

        print(f"✅ Auction completed and transaction created for user {user_id}")
        return {
            "success": True,
            "message": "경매가 완료되었습니다.",
            "transaction_id": transaction_id,
            "reward_amount": request.reward_amount,
        }

    except Exception as e:
        print(f"❌ Auction completed error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reset-password")
async def reset_password(request: Request):
    """비밀번호 재설정 (개발용)"""
    try:
        body = await request.json()
        email = body.get("email")
        new_password = body.get("new_password")

        if not email or not new_password:
            raise HTTPException(
                status_code=400, detail="이메일과 새 비밀번호가 필요합니다."
            )

        # 사용자 확인
        user = await database.fetch_one(
            "SELECT id, email FROM users WHERE email = :email", {"email": email}
        )

        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

        # 새 비밀번호 해시
        hashed_password = get_password_hash(new_password)

        # 비밀번호 업데이트
        await database.execute(
            "UPDATE users SET hashed_password = :hashed_password WHERE email = :email",
            {"hashed_password": hashed_password, "email": email},
        )

        return {"success": True, "message": "비밀번호가 성공적으로 재설정되었습니다."}

    except Exception as e:
        print(f"비밀번호 재설정 오류: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transactions/record")
async def record_tx(body: TxRecord):
    """거래 수신 엔드포인트 (payment-service 호출 수신)"""
    try:
        print(f"📝 Transaction record received: {body.dict()}")

        # 필요 시 로컬 캐시/미러 테이블에 반영 (선택적)
        # 현재는 단순히 수신 확인만 함
        print(f"✅ Transaction recorded for user {body.userId}: {body.transactionId}")

        return {"ok": True}

    except Exception as e:
        print(f"❌ Transaction record error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/user/earnings", status_code=202)
async def register_trade_for_verification(
    request: DetailedEarningsRequest, current_user: dict = Depends(get_current_user)
):
    """
    광고 클릭 시 거래를 'SLA 검증 대기' 상태로 등록합니다.
    - 멱등성을 보장하며, 일일 한도를 체크합니다.
    - 이 함수는 더 이상 사용자 잔고를 직접 업데이트하지 않습니다.
    - 동일한 (user_id, search_id, bid_id) 조합이 있으면 기존 트랜잭션 반환
    - 일일 제출 한도를 초과하면 에러를 반환합니다.
    - 모든 DB 작업은 트랜잭션으로 처리됩니다.
    """
    user_id = current_user["id"]
    user_quality_score = current_user.get("quality_score", 75)
    submission_limit = calculate_dynamic_limit(user_quality_score).dailyMax

    try:
        # 멱등성 체크: 동일한 (user_id, search_id, bid_id) 조합이 오늘 이미 존재하는지 확인
        existing = None
        if request.searchId and request.bidId:
            existing = await database.fetch_one(
                """
                SELECT *
                FROM transactions
                WHERE user_id = :uid AND search_id = :sid AND bid_id = :bid
                  AND created_at::date = CURRENT_DATE
                """,
                {"uid": user_id, "sid": request.searchId, "bid": request.bidId},
            )

        if existing:
            # 기존 트랜잭션이 있으면 그대로 반환 (멱등성)
            daily_after = await _remaining_from_tx(user_id)
            print(f"🔄 Returning existing transaction for user {user_id} (idempotent)")
            return {
                "success": True,
                "message": "거래가 이미 등록되어 있으며, SLA 검증 대기 중입니다.",
                "transaction": dict(existing),
                "user_id": user_id,
                "amount": existing["primary_reward"],
                "dailySubmission": daily_after,
                "trade_id": existing["bid_id"],
            }

        # 트랜잭션 기준으로 현재 사용량 확인
        current_used = await _used_today_from_tx(user_id)

        # 한도 초과 확인
        if current_used >= submission_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"일일 제출 한도({submission_limit}회)를 초과했습니다. 내일 다시 시도해주세요.",
            )

        # 신규 트랜잭션 생성
        amount = request.amount
        query = request.query or "광고 클릭 보상"
        ad_type = request.adType or "unknown"
        search_id = request.searchId or ""
        bid_id = request.bidId or ""

        print(
            f"📝 Registering trade for verification for user {user_id} (Count: {current_used+1}/{submission_limit})"
        )

        transaction_id = (
            f"txn_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}"
        )

        # DB 작업을 트랜잭션으로 묶어 데이터 정합성을 보장
        async with database.transaction():
            # 1. transactions 테이블에 'PENDING_VERIFICATION' 상태로 저장
            await database.execute(
                """
                INSERT INTO transactions (
                    id, user_id, query_text, buyer_name, primary_reward, status, 
                    source, search_id, bid_id, ad_type
                )
                VALUES (
                    :id, :user_id, :query_text, :buyer_name, :primary_reward, 'PENDING_VERIFICATION', 
                    'PLATFORM', :search_id, :bid_id, :ad_type
                )
                """,
                {
                    "id": transaction_id,
                    "user_id": user_id,
                    "query_text": query,
                    "buyer_name": "시스템",
                    "primary_reward": amount,
                    "search_id": search_id,
                    "bid_id": bid_id,
                    "ad_type": ad_type,
                },
            )
            # 2. 사용자 잔고 업데이트 로직 제거됨 - Settlement Service에서 처리

        # 생성된 트랜잭션 조회
        created_transaction = await database.fetch_one(
            "SELECT * FROM transactions WHERE id = :transaction_id",
            {"transaction_id": transaction_id},
        )

        # 트랜잭션 기준으로 업데이트된 사용량 계산
        daily_after = await _remaining_from_tx(user_id)

        print(f"✅ Successfully registered trade for verification: {transaction_id}")
        return {
            "success": True,
            "message": "거래가 등록되었으며, SLA 검증 대기 중입니다.",
            "transaction": dict(created_transaction) if created_transaction else None,
            "user_id": user_id,
            "amount": amount,
            "dailySubmission": daily_after,
            "trade_id": bid_id,  # 프론트엔드가 SLA 검증 요청에 사용할 ID
        }

    except HTTPException as http_exc:
        # 한도 초과 예외는 그대로 전달
        print(f"🚫 Limit exceeded for user {user_id}: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        # 그 외 모든 예외는 서버 오류로 처리
        print(
            f"❌ Critical error in register_trade_for_verification for user {user_id}: {e}"
        )
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"거래 등록 중 서버 오류가 발생했습니다: {str(e)}",
        )


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "user-service", "database": "connected"}
