from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import datetime
import random
from jose import JWTError, jwt
from database import (
    database,
    connect_to_database,
    disconnect_from_database,
)

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


# Pydantic 모델
class Transaction(BaseModel):
    id: str
    query: str
    buyerName: str
    primaryReward: int
    secondaryReward: Optional[int] = None
    status: Literal["1차 완료", "검증 대기중", "2차 완료", "검증 실패"]
    timestamp: str


class RewardRequest(BaseModel):
    bidId: str
    amount: int
    query: str
    buyerName: str


class RewardResponse(BaseModel):
    success: bool
    message: str
    amount: Optional[int] = None
    transactionId: Optional[str] = None
    transaction: Optional[Transaction] = None
    error: Optional[str] = None


class TransactionsResponse(BaseModel):
    success: bool
    transactions: List[Transaction]


# JWT 설정
SECRET_KEY = "a_very_secret_key_for_jwt"
ALGORITHM = "HS256"
security = HTTPBearer()


# JWT 디코딩 함수
async def get_user_id_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """JWT 토큰에서 사용자 ID 추출"""
    try:
        payload = jwt.decode(
            credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
        )
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # 이메일로 사용자 ID 조회
        user = await database.fetch_one(
            "SELECT id FROM users WHERE email = :email", {"email": email}
        )
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

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

        # 보상 지급 시뮬레이션 (90% 성공률)
        is_success = random.random() > 0.1

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
            )
        else:
            return RewardResponse(
                success=False,
                message="보상 지급 중 오류가 발생했습니다. 다시 시도해주세요.",
                error="PAYMENT_ERROR",
            )

    except Exception as e:
        print(f"❌ Payment API error for user {user_id}: {e}")
        return RewardResponse(
            success=False, message="서버 오류가 발생했습니다.", error="SERVER_ERROR"
        )


@app.get("/transactions", response_model=TransactionsResponse)
async def get_transactions():
    """거래 내역을 조회합니다."""
    try:
        # PostgreSQL에서 거래 내역 조회
        transactions_data = await database.fetch_all(
            """
            SELECT id, query_text as query, buyer_name as "buyerName", 
                   primary_reward as "primaryReward", secondary_reward as "secondaryReward",
                   status, created_at as timestamp
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
                secondaryReward=(
                    int(row["secondaryReward"]) if row["secondaryReward"] else None
                ),
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
        return TransactionsResponse(success=True, transactions=transactions)
    except Exception as e:
        print(f"Error fetching transactions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch transactions: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "payment-service", "database": "connected"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)
