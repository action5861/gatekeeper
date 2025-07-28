from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal

app = FastAPI(title="Quality Service", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic 모델
class SubmissionLimit(BaseModel):
    level: Literal["Excellent", "Good", "Average", "Needs Improvement"]
    dailyMax: int

class CalculateLimitRequest(BaseModel):
    qualityScore: int

class CalculateLimitResponse(BaseModel):
    success: bool
    data: SubmissionLimit
    message: str

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

@app.post("/calculate-limit", response_model=CalculateLimitResponse)
async def calculate_submission_limit(request: CalculateLimitRequest):
    """품질 점수에 따른 동적 제출 한도를 계산합니다."""
    try:
        # 품질 점수 유효성 검사
        if not (0 <= request.qualityScore <= 100):
            raise HTTPException(status_code=400, detail="품질 점수는 0-100 사이여야 합니다.")
        
        # 동적 제출 한도 계산
        submission_limit = calculate_dynamic_limit(request.qualityScore)
        
        return CalculateLimitResponse(
            success=True,
            data=submission_limit,
            message="동적 제출 한도가 계산되었습니다."
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}")

@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "quality-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006) 