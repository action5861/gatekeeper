from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Literal, Optional
import os
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
SECRET_KEY = "a_very_secret_key_for_jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# Pydantic 모델들
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class QualityHistory(BaseModel):
    name: str
    score: int


class SubmissionLimit(BaseModel):
    level: Literal["Excellent", "Good", "Average", "Needs Improvement"]
    dailyMax: int


class DashboardResponse(BaseModel):
    earnings: dict
    qualityHistory: List[QualityHistory]
    submissionLimit: SubmissionLimit
    transactions: List[dict]


class EarningsRequest(BaseModel):
    amount: int


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
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def calculate_dynamic_limit(quality_score: int) -> SubmissionLimit:
    base_limit = 20
    if quality_score >= 90:
        return SubmissionLimit(level="Excellent", dailyMax=base_limit * 2)
    elif quality_score >= 70:
        return SubmissionLimit(level="Good", dailyMax=base_limit)
    elif quality_score >= 50:
        return SubmissionLimit(level="Average", dailyMax=int(base_limit * 0.7))
    else:
        return SubmissionLimit(
            level="Needs Improvement", dailyMax=int(base_limit * 0.3)
        )


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
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
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
        # 이메일 중복 확인
        existing_user = await database.fetch_one(
            "SELECT id FROM users WHERE email = :email", {"email": user.email}
        )
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

        # 사용자명 중복 확인
        existing_username = await database.fetch_one(
            "SELECT id FROM users WHERE username = :username",
            {"username": user.username},
        )
        if existing_username:
            raise HTTPException(
                status_code=400, detail="이미 사용 중인 사용자명입니다."
            )

        # 비밀번호 해싱
        hashed_password = get_password_hash(user.password)

        # 사용자 생성
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

        return {"message": "회원가입이 성공적으로 완료되었습니다."}

    except Exception as e:
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
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )
        print("✅ Login successful")
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        print(f"💥 Login error: {str(e)}")
        print(f"💥 Error type: {type(e)}")
        import traceback

        print(f"💥 Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"로그인 실패: {str(e)}")


# 🔥 새로 추가된 /earnings 엔드포인트
@app.post("/earnings")
async def update_earnings(
    request: EarningsRequest, current_user: dict = Depends(get_current_user)
):
    """🔥 JWT에서 실제 사용자 ID 추출하여 수익 업데이트"""
    try:
        user_id = current_user["id"]  # 🚨 하드코딩 완전 제거!
        amount = request.amount

        print(f"💰 Updating earnings for user {user_id}: +{amount}")

        # 실제 사용자의 수익 업데이트
        await database.execute(
            "UPDATE users SET total_earnings = total_earnings + :amount WHERE id = :user_id",
            {"amount": amount, "user_id": user_id},
        )

        print(f"✅ Successfully updated earnings for user {user_id}")
        return {
            "success": True,
            "message": "수익이 업데이트되었습니다.",
            "user_id": user_id,
        }

    except Exception as e:
        print(f"❌ Earnings update error for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """🔥 JWT에서 실제 사용자 ID 추출하여 개인화 대시보드 제공"""
    try:
        user_id = current_user["id"]  # 🚨 하드코딩 완전 제거!
        print(
            f"🎯 Dashboard request for REAL user ID: {user_id} (email: {current_user['email']})"
        )

        # 1. 실제 사용자별 수익 계산
        earnings_query = """
        SELECT 
            COALESCE(SUM(primary_reward), 0) as primary_total,
            COALESCE(SUM(secondary_reward), 0) as secondary_total,
            COALESCE(SUM(primary_reward), 0) + COALESCE(SUM(secondary_reward), 0) as total
        FROM transactions 
        WHERE user_id = :user_id
        """
        earnings_result = await database.fetch_one(earnings_query, {"user_id": user_id})

        # earnings_result가 None인 경우 기본값 설정
        if earnings_result is None:
            earnings_result = {"primary_total": 0, "secondary_total": 0, "total": 0}

        print(f"💰 User {user_id} earnings: {dict(earnings_result)}")

        # 2. 사용자별 품질 이력 조회
        quality_history = await database.fetch_all(
            """
            SELECT week_label as name, quality_score as score 
            FROM user_quality_history 
            WHERE user_id = :user_id 
            ORDER BY recorded_at DESC LIMIT 4
            """,
            {"user_id": user_id},
        )

        # 3. 현재 사용자 품질 점수
        current_user_data = await database.fetch_one(
            "SELECT quality_score FROM users WHERE id = :user_id", {"user_id": user_id}
        )
        quality_score = current_user_data["quality_score"] if current_user_data else 75

        # 4. 동적 제출 한도 계산
        submission_limit = calculate_dynamic_limit(quality_score)

        # 5. 사용자별 거래 내역 조회
        transactions = await database.fetch_all(
            """
            SELECT id, query_text as query, buyer_name as "buyerName", 
                   primary_reward as "primaryReward", secondary_reward as "secondaryReward",
                   status, created_at as timestamp
            FROM transactions 
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            """,
            {"user_id": user_id},
        )
        print(f"📊 User {user_id} has {len(transactions)} transactions")

        # 6. 응답 데이터 구성
        response_data = DashboardResponse(
            earnings={
                "total": int(earnings_result["total"] or 0),
                "primary": int(earnings_result["primary_total"] or 0),
                "secondary": int(earnings_result["secondary_total"] or 0),
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
            submissionLimit=submission_limit,
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


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "user-service", "database": "connected"}
