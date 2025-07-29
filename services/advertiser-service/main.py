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

# Load environment variables
load_dotenv()

app = FastAPI(title="Advertiser Service", version="1.0.0")

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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
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


# 임시 저장소 (실제로는 데이터베이스 사용)
advertisers_db = {}
total_bids = 150
successful_bids = 120
total_spent = 45000


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
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    if username not in advertisers_db:
        raise credentials_exception
    return advertisers_db[username]


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
        if advertiser.username in advertisers_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered",
            )

        hashed_password = get_password_hash(advertiser.password)
        advertisers_db[advertiser.username] = {
            "username": advertiser.username,
            "email": advertiser.email,
            "hashed_password": hashed_password,
            "company_name": advertiser.company_name,
            "created_at": datetime.utcnow(),
        }

        return {
            "success": True,
            "message": "Advertiser registered successfully",
            "username": advertiser.username,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/login", response_model=Token)
async def login_advertiser(advertiser: AdvertiserLogin):
    """광고주 로그인"""
    try:
        if advertiser.username not in advertisers_db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        stored_advertiser = advertisers_db[advertiser.username]
        if not verify_password(
            advertiser.password, stored_advertiser["hashed_password"]
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )

        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": advertiser.username}, expires_delta=access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(current_advertiser: dict = Depends(get_current_advertiser)):
    """광고주 대시보드 데이터를 조회합니다."""
    try:
        # 최근 입찰 내역 가져오기
        recent_bids = await get_recent_bids()
        print(f"Dashboard returning bids: {len(recent_bids)}")

        # 입찰 요약 계산
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
        raise HTTPException(
            status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "advertiser-service"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8007)
