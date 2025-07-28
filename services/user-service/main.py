from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal
import httpx
import os

app = FastAPI(title="User Service", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델
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

class UpdateEarningsRequest(BaseModel):
    amount: int

class UpdateEarningsResponse(BaseModel):
    success: bool
    message: str
    newTotal: int

# 임시 저장소 (실제로는 데이터베이스 사용)
total_earnings = 1500

def calculate_dynamic_limit(quality_score: int) -> SubmissionLimit:
    """동적 제출 한도를 계산합니다."""
    base_limit = 20  # Base daily limit
    
    if quality_score >= 90:
        # 'Excellent' grade: 200% of base limit
        return SubmissionLimit(level="Excellent", dailyMax=base_limit * 2)
    elif quality_score >= 70:
        # 'Good' grade: Maintain base limit (100%)
        return SubmissionLimit(level="Good", dailyMax=base_limit)
    elif quality_score >= 50:
        # 'Average' grade: 70% of base limit
        return SubmissionLimit(level="Average", dailyMax=int(base_limit * 0.7))
    else:
        # 'Needs Improvement' grade: 30% of base limit
        return SubmissionLimit(level="Needs Improvement", dailyMax=int(base_limit * 0.3))

async def get_transactions() -> List[dict]:
    """거래 내역을 가져오는 함수"""
    try:
        payment_service_url = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8003")
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{payment_service_url}/transactions")
            if response.status_code == 200:
                data = response.json()
                print(f'Fetched transactions: {len(data.get("transactions", []))}')
                return data.get("transactions", [])
    except Exception as error:
        print(f'Failed to fetch transactions: {error}')
    return []

@app.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard():
    """사용자 대시보드 데이터를 조회합니다."""
    try:
        user_quality_score = 75  # 가상 사용자 품질 점수
        submission_limit = calculate_dynamic_limit(user_quality_score)
        
        # 거래 내역 가져오기
        transactions = await get_transactions()
        print(f'Dashboard returning transactions: {len(transactions)}')

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
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")

@app.post("/earnings", response_model=UpdateEarningsResponse)
async def update_earnings(request: UpdateEarningsRequest):
    """보상 누적을 위한 POST 메서드"""
    try:
        global total_earnings
        
        # 총 수익에 보상 금액 추가
        total_earnings += request.amount
        
        return UpdateEarningsResponse(
            success=True,
            message=f"보상 {request.amount}원이 대시보드에 누적되었습니다.",
            newTotal=total_earnings
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")

@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "user-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005) 