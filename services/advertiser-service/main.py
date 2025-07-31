from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Literal, Optional
import httpx
import os
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# 데이터베이스 연동 추가
from database import (
    database,
    Advertiser,
    Bid,
    connect_to_database,
    disconnect_from_database,
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


class AdvertiserRegister(BaseModel):
    username: str
    email: str
    password: str
    company_name: str


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
        username: str = payload.get("sub")
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

        # 광고주 생성
        query = """
        INSERT INTO advertisers (username, email, hashed_password, company_name) 
        VALUES (:username, :email, :hashed_password, :company_name)
        """
        await database.execute(
            query,
            {
                "username": advertiser.username,
                "email": advertiser.email,
                "hashed_password": hashed_password,
                "company_name": advertiser.company_name,
            },
        )

        print(f"Registration successful for: {advertiser.username}")
        return {
            "success": True,
            "message": "Advertiser registered successfully",
            "username": advertiser.username,
        }

    except Exception as e:
        print(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


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

        # 최근 입찰 내역 가져오기
        recent_bids = await get_recent_bids()
        print(f"Dashboard returning bids: {len(recent_bids)}")

        # 입찰 요약 계산 (시뮬레이션 데이터)
        total_bids = 150
        successful_bids = 120
        total_spent = 45000
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8007)
