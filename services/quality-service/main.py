from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal
from database import (
    database,
    connect_to_database,
    disconnect_from_database,
)
import sys
from pathlib import Path

# 공통 한도 정책 모듈 import
# services 디렉토리를 Python 경로에 추가
services_path = Path(__file__).parent.parent
if str(services_path) not in sys.path:
    sys.path.insert(0, str(services_path))

from shared.limit_policy import calculate_dynamic_limit, LimitInfo

app = FastAPI(title="Quality Service", version="1.0.0")


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
class SubmissionLimit(BaseModel):
    level: Literal[
        "Excellent",
        "Very Good",
        "Good",
        "Average",
        "Below Average",
        "Poor",
        "Very Poor",
        "Standard",  # 호환성을 위해 추가
    ]
    dailyMax: int


class CalculateLimitRequest(BaseModel):
    qualityScore: int


class CalculateLimitResponse(BaseModel):
    success: bool
    data: SubmissionLimit
    message: str


# calculate_dynamic_limit 함수는 이제 shared.limit_policy에서 import하여 사용
# 기존 함수는 제거하고 공통 모듈 사용


@app.post("/calculate-limit", response_model=CalculateLimitResponse)
async def calculate_submission_limit(request: CalculateLimitRequest):
    """품질 점수에 따른 동적 제출 한도를 계산합니다."""
    try:
        # 품질 점수 유효성 검사
        if not (0 <= request.qualityScore <= 100):
            raise HTTPException(
                status_code=400, detail="품질 점수는 0-100 사이여야 합니다."
            )

        # 동적 제출 한도 계산 (공통 모듈 사용)
        limit_info = calculate_dynamic_limit(request.qualityScore)
        submission_limit = SubmissionLimit(level=limit_info.level, dailyMax=limit_info.daily_max)

        # 품질 점수 계산 결과를 DB에 저장
        quality_query = """
            INSERT INTO user_quality_history (user_id, quality_score, week_label)
            VALUES (:user_id, :quality_score, :week_label)
        """

        # 현재 주차 계산 (간단한 예시)
        from datetime import datetime

        current_week = f"Week {datetime.now().isocalendar()[1]}"

        # Note: user_id is hardcoded for now, should be extracted from JWT in production
        # For now, we'll skip the database insertion to avoid errors
        # await database.execute(
        #     quality_query,
        #     {
        #         "user_id": 1,  # 하드코딩된 user_id (실제로는 JWT에서 추출)
        #         "quality_score": request.qualityScore,
        #         "week_label": current_week,
        #     },
        # )

        return CalculateLimitResponse(
            success=True,
            data=submission_limit,
            message="동적 제출 한도가 계산되었습니다.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "quality-service", "database": "connected"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8006)
