from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Optional
import httpx
import os
from datetime import datetime, timedelta

# --- 보안 및 인증을 위한 라이브러리 임포트 ---
from passlib.context import CryptContext
from jose import JWTError, jwt

app = FastAPI(title="User Service", version="1.0.0")

# --- 환경 변수 및 보안 설정 ---
SECRET_KEY = (
    "a_very_secret_key_for_jwt"  # 실제 프로덕션에서는 환경 변수로 관리해야 합니다.
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 비밀번호 해싱을 위한 설정
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic 모델 정의 ---


# 사용자 정보 저장을 위한 모델
class UserInDB(BaseModel):
    username: str
    email: str
    hashed_password: str


# 회원가입 요청 모델
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


# 로그인 요청 모델
class UserLogin(BaseModel):
    email: str
    password: str


# JWT 토큰 응답 모델
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


# --- 임시 데이터베이스 ---
# 실제 프로덕션에서는 PostgreSQL, MySQL 등의 DB를 사용해야 합니다.
fake_users_db = {}
total_earnings = 1500

# --- 보안 관련 함수 ---


def verify_password(plain_password, hashed_password):
    """일반 비밀번호와 해시된 비밀번호를 비교합니다."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """비밀번호를 해시 처리합니다."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """JWT 액세스 토큰을 생성합니다."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- 유틸리티 함수 ---


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


async def get_transactions() -> List[dict]:
    try:
        payment_service_url = os.getenv(
            "PAYMENT_SERVICE_URL", "http://payment-service:8003"
        )
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{payment_service_url}/transactions")
            response.raise_for_status()
            data = response.json()
            return data.get("transactions", [])
    except httpx.RequestError as exc:
        print(f"Payment service 연결 오류: {exc}")
    except Exception as e:
        print(f"거래 내역 조회 중 알 수 없는 오류: {e}")
    return []


# --- API 엔드포인트 ---


@app.post("/register", status_code=201)
async def register_user(user: UserCreate):
    """신규 사용자 등록"""
    if user.email in fake_users_db:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

    hashed_password = get_password_hash(user.password)
    user_in_db = UserInDB(
        username=user.username, email=user.email, hashed_password=hashed_password
    )
    fake_users_db[user.email] = user_in_db.dict()
    return {"message": "회원가입이 성공적으로 완료되었습니다."}


@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: UserLogin):
    """사용자 로그인 및 JWT 토큰 발급"""
    user = fake_users_db.get(form_data.email)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="이메일 또는 비밀번호가 잘못되었습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    """사용자 대시보드 데이터 조회"""
    try:
        user_quality_score = 75
        submission_limit = calculate_dynamic_limit(user_quality_score)
        transactions = await get_transactions()

        return DashboardResponse(
            earnings={
                "total": total_earnings,
                "primary": 1200,
                "secondary": 300,
            },
            qualityHistory=[
                QualityHistory(name="Week 1", score=65),
                QualityHistory(name="Week 2", score=70),
                QualityHistory(name="Week 3", score=72),
                QualityHistory(name="Week 4", score=user_quality_score),
            ],
            submissionLimit=submission_limit,
            transactions=transactions,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류: {str(e)}")


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "user-service"}
