from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import datetime
import random

app = FastAPI(title="Payment Service", version="1.0.0")

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

# 메모리 내 거래 내역 저장소 (실제로는 데이터베이스 사용)
transactions = [
    Transaction(
        id='txn_1001',
        query='아이폰16',
        buyerName='쿠팡',
        primaryReward=175,
        status='1차 완료',
        timestamp='2025-07-20T09:10:00Z',
    ),
    Transaction(
        id='txn_1002',
        query='제주도 항공권',
        buyerName='네이버',
        primaryReward=250,
        status='2차 완료',
        secondaryReward=1250,
        timestamp='2025-07-19T14:30:00Z',
    ),
    Transaction(
        id='txn_1003',
        query='나이키 운동화',
        buyerName='Google',
        primaryReward=90,
        status='검증 실패',
        timestamp='2025-07-18T18:00:00Z',
    ),
]

@app.post("/reward", response_model=RewardResponse)
async def process_reward(request: RewardRequest):
    """보상을 지급하고 거래 내역을 생성합니다."""
    try:
        print(f'Payment API called with: {request.dict()}')

        # 실제 환경에서는 여기서 결제 처리나 보상 지급 로직을 구현
        # 현재는 시뮬레이션으로 즉시 성공 응답
        
        # 보상 지급 시뮬레이션 (90% 성공률)
        is_success = random.random() > 0.1
        
        if is_success:
            # 새로운 거래 내역 생성
            new_transaction = Transaction(
                id=f"txn_{int(datetime.now().timestamp())}_{random.randint(1000, 9999)}",
                query=request.query or 'Unknown Search',
                buyerName=request.buyerName or 'Unknown Buyer',
                primaryReward=request.amount,
                status='1차 완료',
                timestamp=datetime.now().isoformat(),
            )

            print(f'Creating new transaction: {new_transaction.dict()}')

            # 거래 내역에 추가
            transactions.insert(0, new_transaction)  # 최신 거래를 맨 위에 추가

            print(f'Updated transactions count: {len(transactions)}')

            return RewardResponse(
                success=True,
                message=f"즉시 보상 {request.amount}원이 지급되었습니다!",
                amount=request.amount,
                transactionId=new_transaction.id,
                transaction=new_transaction
            )
        else:
            return RewardResponse(
                success=False,
                message="보상 지급 중 오류가 발생했습니다. 다시 시도해주세요.",
                error="PAYMENT_ERROR"
            )
            
    except Exception as e:
        print(f'Payment API error: {e}')
        return RewardResponse(
            success=False,
            message="서버 오류가 발생했습니다.",
            error="SERVER_ERROR"
        )

@app.get("/transactions", response_model=TransactionsResponse)
async def get_transactions():
    """거래 내역을 조회합니다."""
    print(f'GET transactions called, count: {len(transactions)}')
    return TransactionsResponse(
        success=True,
        transactions=transactions
    )

@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "payment-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 