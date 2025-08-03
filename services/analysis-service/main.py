from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal
import re
import random
from database import (
    database,
    SearchQuery,
    User,
    UserQualityHistory,
    connect_to_database,
    disconnect_from_database,
)

app = FastAPI(title="Analysis Service", version="1.0.0")


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
class QualityReport(BaseModel):
    score: int
    suggestions: List[str]
    keywords: List[str]
    commercialValue: Literal["low", "medium", "high"]


class EvaluateRequest(BaseModel):
    query: str


class EvaluateResponse(BaseModel):
    success: bool
    data: QualityReport
    message: str


# 상업적 가치 키워드 가중치
COMMERCIAL_KEYWORDS = {
    "구매": 25,
    "가격": 20,
    "리뷰": 15,
    "브랜드": 15,
    "트렌드": 10,
    "소셜": 10,
    "인플루언서": 12,
    "콘텐츠": 8,
    "통계": 5,
    "분석": 5,
    "리서치": 8,
    "시장조사": 10,
    "마케팅": 15,
    "광고": 12,
    "판매": 18,
    "홍보": 10,
}


def calculate_search_specificity(query: str) -> int:
    """검색어의 구체성에 따른 포인트 계산 (10-100점)"""
    # 기본 포인트
    points = 10

    # 검색어 길이에 따른 포인트 증가
    if len(query) >= 15:
        points += 40
    elif len(query) >= 10:
        points += 30
    elif len(query) >= 7:
        points += 20
    elif len(query) >= 5:
        points += 15
    elif len(query) >= 3:
        points += 10

    # 숫자가 포함된 경우 (모델명, 연도 등) 포인트 대폭 증가
    if re.search(r"\d", query):
        points += 25
        # 연도가 포함된 경우 추가 포인트
        if re.search(r"\b(20\d{2}|19\d{2})\b", query):
            points += 10

    # 브랜드명 + 모델명 조합 (예: 아이폰16, 갤럭시S24)
    brand_model_patterns = [
        r"아이폰\s*\d+",
        r"iphone\s*\d+",
        r"갤럭시\s*[a-z]?\d+",
        r"galaxy\s*[a-z]?\d+",
        r"맥북\s*(프로|에어|미니)?",
        r"macbook\s*(pro|air|mini)?",
        r"삼성\s*노트북",
        r"samsung\s*laptop",
    ]

    if any(
        re.search(pattern, query, re.IGNORECASE) for pattern in brand_model_patterns
    ):
        points += 30

    # 특정 키워드 조합
    specific_combinations = [
        "아이폰16",
        "iphone16",
        "갤럭시s24",
        "galaxys24",
        "맥북프로",
        "macbookpro",
        "삼성노트북",
        "samsunglaptop",
        "아이패드",
        "ipad",
        "에어팟",
        "airpods",
    ]

    if any(combo in query.lower() for combo in specific_combinations):
        points += 20

    # 최종 포인트 범위 제한 (10-100)
    return max(10, min(100, points))


def get_quality_grade(points: int) -> str:
    """포인트에 따른 품질 등급 반환"""
    if points >= 80:
        return "Excellent"
    elif points >= 60:
        return "Very Good"
    elif points >= 40:
        return "Good"
    elif points >= 20:
        return "Fair"
    else:
        return "Poor"


def evaluate_data_value(query: str) -> QualityReport:
    """입력된 검색어를 기반으로 상업적 가치 점수와 품질 개선 제안을 반환"""
    # 구체성 포인트 계산
    specificity_points = calculate_search_specificity(query)

    lower_query = query.lower()
    score = specificity_points
    matched_keywords = []
    suggestions = []

    # 기존 키워드 매칭 및 점수 추가
    for keyword, weight in COMMERCIAL_KEYWORDS.items():
        if keyword.lower() in lower_query:
            score += weight * 0.5  # 기존 키워드의 가중치를 절반으로 줄임
            matched_keywords.append(keyword)

    # 최종 점수 범위 제한 (10-100)
    score = max(10, min(100, int(score)))

    # 상업적 가치 등급 결정
    if score >= 70:
        commercial_value = "high"
    elif score >= 40:
        commercial_value = "medium"
    else:
        commercial_value = "low"

    # 구체성에 따른 품질 개선 제안 생성
    if score < 30:
        suggestions.append("Add specific model numbers (e.g., iPhone 16, Galaxy S24)")
        suggestions.append("Include brand names and product categories")
    elif score < 60:
        suggestions.append("Add more specific product details")
        suggestions.append("Include year or generation information")
    else:
        suggestions.append(
            "Excellent specificity! Your search has high commercial value"
        )
        suggestions.append(
            "Consider adding additional specifications for even higher value"
        )

    # 구체성 수준에 따른 추가 제안
    if specificity_points < 40:
        suggestions.append(
            "More specific searches earn higher points and better rewards"
        )

    return QualityReport(
        score=score,
        suggestions=suggestions,
        keywords=matched_keywords,
        commercialValue=commercial_value,
    )


@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_query(request: EvaluateRequest):
    """검색어의 데이터 가치를 평가합니다."""
    try:
        # 검색어 유효성 검사
        if not request.query or not request.query.strip():
            raise HTTPException(status_code=400, detail="검색어를 입력해주세요.")

        if len(request.query) > 200:
            raise HTTPException(
                status_code=400, detail="검색어는 200자 이내로 입력해주세요."
            )

        # 데이터 가치 평가
        quality_report = evaluate_data_value(request.query.strip())

        # 검색어 데이터를 DB에 저장
        query = """
            INSERT INTO search_queries (user_id, query_text, quality_score, commercial_value, keywords, suggestions)
            VALUES (:user_id, :query_text, :quality_score, :commercial_value, :keywords, :suggestions)
        """

        import json

        await database.execute(
            query,
            {
                "user_id": 1,  # 하드코딩된 user_id
                "query_text": request.query.strip(),
                "quality_score": quality_report.score,
                "commercial_value": quality_report.commercialValue,
                "keywords": json.dumps(quality_report.keywords),
                "suggestions": json.dumps(quality_report.suggestions),
            },
        )

        return EvaluateResponse(
            success=True,
            data=quality_report,
            message="데이터 가치 평가가 완료되었습니다.",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"서버 오류가 발생했습니다: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "service": "analysis-service", "database": "connected"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
