from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, Field
from typing import List, Literal, Optional
from datetime import datetime
import random
from jose import JWTError, jwt
from database import (
    database,
    connect_to_database,
    disconnect_from_database,
)
import os
import re
import html

app = FastAPI(title="Payment Service", version="1.0.0")


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


# Pydantic 모델
class Transaction(BaseModel):
    id: str = Field(..., max_length=100)
    query: str = Field(..., max_length=500)
    buyerName: str = Field(..., max_length=100)
    primaryReward: int = Field(..., ge=0, le=1000000)
    status: str = Field(..., max_length=50)
    timestamp: str = Field(..., max_length=50)

    @validator("id")
    def validate_id(cls, v):
        v = sanitize_input(v)
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "거래 ID는 영문, 숫자, 언더스코어, 하이픈만 사용 가능합니다"
            )
        if not validate_sql_injection(v):
            raise ValueError("거래 ID에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("query")
    def validate_query(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("검색어에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("buyerName")
    def validate_buyer_name(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("구매자명에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("status")
    def validate_status(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("상태에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("timestamp")
    def validate_timestamp(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("타임스탬프에 허용되지 않는 문자가 포함되어 있습니다")
        return v


class RewardRequest(BaseModel):
    query: str = Field(..., max_length=500)
    buyerName: str = Field(..., max_length=100)
    amount: int = Field(..., ge=0, le=1000000)

    @validator("query")
    def validate_query(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("검색어에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("buyerName")
    def validate_buyer_name(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("구매자명에 허용되지 않는 문자가 포함되어 있습니다")
        return v


class RewardResponse(BaseModel):
    success: bool
    message: str = Field(..., max_length=500)
    amount: Optional[int] = Field(None, ge=0, le=1000000)
    transactionId: Optional[str] = Field(None, max_length=100)
    transaction: Optional[Transaction] = None
    error: Optional[str] = Field(None, max_length=100)

    @validator("message")
    def validate_message(cls, v):
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("메시지에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("transactionId")
    def validate_transaction_id(cls, v):
        if v is None:
            return v
        v = sanitize_input(v)
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "거래 ID는 영문, 숫자, 언더스코어, 하이픈만 사용 가능합니다"
            )
        if not validate_sql_injection(v):
            raise ValueError("거래 ID에 허용되지 않는 문자가 포함되어 있습니다")
        return v

    @validator("error")
    def validate_error(cls, v):
        if v is None:
            return v
        v = sanitize_input(v)
        if not validate_sql_injection(v):
            raise ValueError("에러 코드에 허용되지 않는 문자가 포함되어 있습니다")
        return v


class TransactionsResponse(BaseModel):
    transactions: List[Transaction]
    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=100)


class AwardRequest(BaseModel):
    userId: int
    bidId: str
    type: str  # "PLATFORM" | "ADVERTISER"
    amount: int
    reason: str  # "click"


# JWT 설정
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
security = HTTPBearer()


# JWT 디코딩 함수
async def get_user_id_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """JWT 토큰에서 사용자 ID 추출"""
    try:
        print(f"🔍 JWT Token received: {credentials.credentials[:20]}...")
        print(f"🔍 SECRET_KEY: {SECRET_KEY[:10]}...")

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
        print(f"🔍 JWT Payload: {payload}")

        email = payload.get("sub")
        if email is None:
            print("❌ No email in JWT payload")
            raise HTTPException(status_code=401, detail="Invalid token")

        # 이메일로 사용자 ID 조회
        user = await database.fetch_one(
            "SELECT id FROM users WHERE email = :email", {"email": email}
        )
        if not user:
            print(f"❌ User not found for email: {email}")
            raise HTTPException(status_code=401, detail="User not found")

        print(f"✅ User found: {user['id']} for email: {email}")
        return user["id"]
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# 메모리 내 거래 내역 저장소 (실제로는 데이터베이스 사용)
# 이제 PostgreSQL에서 데이터를 가져옵니다


@app.post("/reward", response_model=RewardResponse)
async def process_reward(
    request: RewardRequest, user_id: int = Depends(get_user_id_from_token)
):
    """🔥 JWT에서 실제 사용자 ID 추출하여 거래 생성"""
    try:
        print(f"🎯 Payment API called for user {user_id}: {request.dict()}")

        # 보상 지급 시뮬레이션 (100% 성공률로 임시 변경)
        is_success = True  # random.random() > 0.1 대신 True로 고정

        if is_success:
            # 새로운 거래 내역 생성
            new_transaction = Transaction(
                id=f"txn_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}",
                query=request.query or "Unknown Search",
                buyerName=request.buyerName or "Unknown Buyer",
                primaryReward=request.amount,
                status="1차 완료",
                timestamp=datetime.now().isoformat(),
            )

            print(
                f"💾 Creating transaction for user {user_id}: {new_transaction.dict()}"
            )

            # PostgreSQL에 거래 내역 저장 (실제 사용자 ID 사용)
            query = """
            INSERT INTO transactions (id, user_id, query_text, buyer_name, primary_reward, status) 
            VALUES (:id, :user_id, :query_text, :buyer_name, :primary_reward, :status)
            """
            await database.execute(
                query,
                {
                    "id": new_transaction.id,
                    "user_id": user_id,  # 🔥 실제 JWT에서 추출한 사용자 ID!
                    "query_text": new_transaction.query,
                    "buyer_name": new_transaction.buyerName,
                    "primary_reward": new_transaction.primaryReward,
                    "status": new_transaction.status,
                },
            )

            print(f"✅ Transaction saved for user {user_id}: {new_transaction.id}")

            return RewardResponse(
                success=True,
                message=f"즉시 보상 {request.amount}원이 지급되었습니다!",
                amount=request.amount,
                transactionId=new_transaction.id,
                transaction=new_transaction,
                error=None,
            )
        else:
            return RewardResponse(
                success=False,
                message="보상 지급 중 오류가 발생했습니다. 다시 시도해주세요.",
                amount=None,
                transactionId=None,
                transaction=None,
                error="PAYMENT_ERROR",
            )

    except Exception as e:
        import traceback

        error_traceback = traceback.format_exc()
        print(f"❌ Payment API error: {e}")
        print(f"❌ Full traceback: {error_traceback}")

        # user_id가 정의되지 않았을 수 있으므로 안전하게 처리
        user_info = f"user {user_id}" if "user_id" in locals() else "unknown user"
        print(f"❌ Error occurred for {user_info}")

        return RewardResponse(
            success=False,
            message="서버 오류가 발생했습니다.",
            amount=None,
            transactionId=None,
            transaction=None,
            error="SERVER_ERROR",
        )


@app.get("/transactions", response_model=TransactionsResponse)
async def get_transactions():
    """거래 내역을 조회합니다."""
    try:
        # PostgreSQL에서 거래 내역 조회
        transactions_data = await database.fetch_all(
            """
            SELECT id, query_text as query, buyer_name as "buyerName", 
                   primary_reward as "primaryReward", status, created_at as timestamp
            FROM transactions 
            ORDER BY created_at DESC
            """
        )

        # Pydantic 모델로 변환
        transactions = [
            Transaction(
                id=row["id"],
                query=row["query"],
                buyerName=row["buyerName"],
                primaryReward=int(row["primaryReward"]),
                status=row["status"],
                timestamp=(
                    row["timestamp"].isoformat()
                    if row["timestamp"]
                    else datetime.now().isoformat()
                ),
            )
            for row in transactions_data
        ]

        print(f"GET transactions called, count: {len(transactions)}")
        return TransactionsResponse(
            transactions=transactions,
            total=len(transactions),
            page=1,
            limit=len(transactions),
        )
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch transactions: {str(e)}"
        )


@app.post("/award")
async def award(request: AwardRequest):
    """클릭 적립 처리 (PLATFORM 및 ADVERTISER 모두 지원)"""
    try:
        print(f"🎯 Award request: {request.dict()}")

        # 1. 광고주 ID 조회 (ADVERTISER 타입인 경우)
        advertiser_id = None
        if request.type == "ADVERTISER":
            # bid_id에서 광고주 ID 추출 시도
            try:
                if request.bidId.startswith("bid_real_"):
                    parts = request.bidId.split("_")
                    if len(parts) >= 3:
                        advertiser_id = int(parts[2])
            except (ValueError, IndexError):
                advertiser_id = None

        # 2. 거래 내역 생성
        transaction_id = f"TXN_{request.bidId}_{int(datetime.now().timestamp())}"

        insert_query = """
            INSERT INTO transactions (
                id, user_id, bid_id, advertiser_id, amount, source, reason, status, created_at
            ) VALUES (
                :transaction_id, :user_id, :bid_id, :advertiser_id, :amount, :source, :reason, 'completed', CURRENT_TIMESTAMP
            )
        """

        await database.execute(
            insert_query,
            {
                "transaction_id": transaction_id,
                "user_id": request.userId,
                "bid_id": request.bidId,
                "advertiser_id": advertiser_id,
                "amount": request.amount,
                "source": request.type,
                "reason": request.reason,
            },
        )

        print(f"✅ Transaction created: {transaction_id}")

        # 3. user-service에 거래 알림 (선택적)
        try:
            import httpx

            user_tx_url = "http://user-service:8005/transactions/record"
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    user_tx_url,
                    json={
                        "userId": request.userId,
                        "transactionId": transaction_id,
                        "amount": request.amount,
                        "source": request.type,
                        "reason": request.reason,
                    },
                )
            print(f"✅ User service notified")
        except Exception as e:
            print(f"⚠️ User service notification failed: {e}")
            # 알림 실패는 전체 프로세스에 영향을 주지 않음

        return {"ok": True, "transactionId": transaction_id}

    except Exception as e:
        print(f"❌ Award error: {e}")
        raise HTTPException(status_code=500, detail=f"Award error: {str(e)}")


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "payment-service", "database": "connected"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
