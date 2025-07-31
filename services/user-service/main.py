from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Optional
import os
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from database import (
    database,
    User,
    Transaction,
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
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


# Pydantic 모델들 (기존과 동일)
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
        # 사용자 조회
        user = await database.fetch_one(
            "SELECT * FROM users WHERE email = :email", {"email": form_data.email}
        )

        if not user or not verify_password(form_data.password, user["hashed_password"]):
            raise HTTPException(
                status_code=401,
                detail="이메일 또는 비밀번호가 잘못되었습니다.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 토큰 생성
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["email"]}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"로그인 실패: {str(e)}")


@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    """사용자 대시보드 데이터 조회"""
    try:
        # 품질 이력 조회
        quality_history = await database.fetch_all(
            "SELECT week_label as name, quality_score as score FROM user_quality_history WHERE user_id = 1 ORDER BY id"
        )

        # 거래 내역 조회
        transactions = await database.fetch_all(
            """
            SELECT id, query_text as query, buyer_name as "buyerName", 
                   primary_reward as "primaryReward", secondary_reward as "secondaryReward",
                   status, created_at as timestamp
            FROM transactions 
            ORDER BY created_at DESC
            """
        )

        # 총 수익 계산
        total_earnings = await database.fetch_one(
            "SELECT COALESCE(SUM(primary_reward), 0) + COALESCE(SUM(secondary_reward), 0) as total FROM transactions"
        )

        user_quality_score = 75
        submission_limit = calculate_dynamic_limit(user_quality_score)

        return DashboardResponse(
            earnings={
                "total": int(total_earnings["total"] or 1500),
                "primary": 1200,
                "secondary": 300,
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
                    QualityHistory(name="Week 4", score=user_quality_score),
                ]
            ),
            submissionLimit=submission_limit,
            transactions=[dict(row) for row in transactions] if transactions else [],
        )

    except Exception as e:
        print(f"Dashboard error: {e}")
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "user-service", "database": "connected"}
