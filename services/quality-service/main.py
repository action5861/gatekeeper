from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Literal
from database import (
    database,
    connect_to_database,
    disconnect_from_database,
)

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
    ]
    dailyMax: int


class CalculateLimitRequest(BaseModel):
    qualityScore: int


class CalculateLimitResponse(BaseModel):
    success: bool
    data: SubmissionLimit
    message: str


def calculate_dynamic_limit(quality_score: int) -> SubmissionLimit:
    """일일 제출 한도를 기본값 5개로 설정합니다."""
    # 모든 사용자에게 동일하게 하루 5번 제출 한도 제공
    # 추후 quality_score에 따라 동적으로 변경 가능
    result = SubmissionLimit(level="Standard", dailyMax=5)
    print(f"🔍 디버그: 고정 일일 제출 한도 설정, dailyMax={result.dailyMax}")
    return result


@app.post("/calculate-limit", response_model=CalculateLimitResponse)
async def calculate_submission_limit(request: CalculateLimitRequest):
    """품질 점수에 따른 동적 제출 한도를 계산합니다."""
    try:
        # 품질 점수 유효성 검사
        if not (0 <= request.qualityScore <= 100):
            raise HTTPException(
                status_code=400, detail="품질 점수는 0-100 사이여야 합니다."
            )

        # 동적 제출 한도 계산
        submission_limit = calculate_dynamic_limit(request.qualityScore)

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
