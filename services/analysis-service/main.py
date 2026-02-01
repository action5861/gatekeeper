# services/analysis-service/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import json
import asyncio
from dotenv import load_dotenv

load_dotenv()

from database import database, connect_to_database, disconnect_from_database
from cache import connect_redis, disconnect_redis
from ai_analyzer import (
    analyze_query_with_ai,
    generate_improved_queries,
    AiAnalysisReport,
)
from legacy_analyzer import (
    evaluate_data_value as evaluate_data_value_legacy,
    LegacyQualityReport,
)

app = FastAPI(
    title="AI-Powered Analysis Service",
    description="A service that analyzes search query value using a hybrid AI and rule-based model.",
    version="2.0.0",
)


@app.on_event("startup")
async def startup():
    await connect_to_database()
    await connect_redis()


@app.on_event("shutdown")
async def shutdown():
    await disconnect_from_database()
    await disconnect_redis()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EvaluateRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)
    user_id: int = Field(..., description="로그인한 사용자의 ID")


class ImprovedQuery(BaseModel):
    """AI가 제안한 개선된 검색어"""

    query: str
    reason: str
    score: Optional[int] = None  # 빠른 평가 후 추가
    commercialValue: Optional[str] = None


class FinalQualityReport(BaseModel):
    score: int
    suggestions: List[str]
    keywords: List[str]
    commercialValue: Literal["low", "medium", "high"]
    ai_analysis: Optional[AiAnalysisReport] = None
    needsImprovement: bool = False  # ⭐ 개선 필요 플래그
    aiSuggestions: Optional[List[ImprovedQuery]] = None  # ⭐ AI 개선 제안


class EvaluateResponse(BaseModel):
    success: bool
    data: FinalQualityReport
    message: str


def blend_reports(
    legacy_report: LegacyQualityReport, ai_report: Optional[AiAnalysisReport]
) -> FinalQualityReport:
    if not ai_report:
        return FinalQualityReport(**legacy_report.dict())

    final_score = int(
        (
            ai_report.commercial_intent * 100 * 0.5
            + ai_report.specificity_level * 100 * 0.3
        )
        + (legacy_report.score * 0.2)
    )
    final_score = max(10, min(100, final_score))
    if final_score >= 75:
        commercial_value = "high"
    elif final_score >= 45:
        commercial_value = "medium"
    else:
        commercial_value = "low"

    suggestions = []
    if ai_report.specificity_level < 0.4:
        if ai_report.predicted_keywords:
            suggestions.append(
                f"'{ai_report.predicted_keywords[0]}'와 같은 구체적인 제품명을 사용해보세요."
            )
        else:
            suggestions.append("구체적인 제품명이나 브랜드를 포함해보세요.")
    if ai_report.buyer_journey_stage == "Consideration":
        suggestions.append(
            "'비교', '리뷰', '추천'과 같은 키워드를 추가하면 더 가치있는 정보를 얻을 수 있습니다."
        )
    else:
        suggestions.append("훌륭한 검색어입니다! 잠재적 가치가 높게 평가되었습니다.")
    return FinalQualityReport(
        score=final_score,
        suggestions=suggestions,
        keywords=list(set(legacy_report.keywords + ai_report.predicted_keywords)),
        commercialValue=commercial_value,
        ai_analysis=ai_report,
    )


@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_query(request: EvaluateRequest):
    query_text = request.query.strip()

    # AI 분석 (느림: ~5초)과 Legacy 분석 (빠름: ~0.1초)을 동시 시작
    ai_task = asyncio.create_task(analyze_query_with_ai(query_text))
    legacy_task = asyncio.to_thread(evaluate_data_value_legacy, query_text)

    # Legacy는 반드시 기다림 (매우 빠름)
    legacy_report = await legacy_task

    # AI는 충분한 시간(10초)을 주고 기다림 (품질 우선, 프론트엔드에서 로딩 표시)
    try:
        ai_report = await asyncio.wait_for(ai_task, timeout=10.0)
        print(f"✓ AI 분석 완료: {query_text[:30]}... (고품질 결과)")
    except asyncio.TimeoutError:
        print(f"⚠ AI 타임아웃 (10초 초과): {query_text[:30]}... → Legacy 사용")
        ai_report = None
    except Exception as e:
        print(f"❌ AI 분석 실패: {e} → Legacy 사용")
        ai_report = None

    final_report = blend_reports(legacy_report, ai_report)

    # ⭐ 30점 미만 또는 low 값이면 AI 개선 제안 생성
    if final_report.score < 30 or final_report.commercialValue == "low":
        print(
            f"🔄 저품질 검색어 감지 ({final_report.score}점) - AI 개선 제안 생성 중..."
        )
        try:
            improved_suggestions = await asyncio.wait_for(
                generate_improved_queries(query_text), timeout=10.0
            )

            if improved_suggestions:
                # 각 제안 검색어도 빠르게 평가 (Legacy만 사용)
                evaluated_suggestions = []
                for sugg in improved_suggestions:
                    quick_eval = evaluate_data_value_legacy(sugg["query"])
                    evaluated_suggestions.append(
                        ImprovedQuery(
                            query=sugg["query"],
                            reason=sugg.get("reason", "개선됨"),
                            score=quick_eval.score,
                            commercialValue=quick_eval.commercialValue,
                        )
                    )

                final_report.needsImprovement = True
                final_report.aiSuggestions = evaluated_suggestions
                print(f"✨ AI 개선 제안 생성 완료: {len(evaluated_suggestions)}개")
        except Exception as e:
            print(f"⚠️ 개선 제안 생성 실패: {e}")
    db_query = """
        INSERT INTO search_queries (user_id, query_text, quality_score, commercial_value, keywords, suggestions, ai_analysis_data)
        VALUES (:user_id, :query_text, :quality_score, :commercial_value, :keywords, :suggestions, :ai_analysis_data)
    """
    values = {
        "user_id": request.user_id,
        "query_text": query_text,
        "quality_score": final_report.score,
        "commercial_value": final_report.commercialValue,
        "keywords": json.dumps(final_report.keywords),
        "suggestions": json.dumps(final_report.suggestions),
        "ai_analysis_data": (
            final_report.ai_analysis.json() if final_report.ai_analysis else None
        ),
    }
    try:
        await database.execute(db_query, values)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    return EvaluateResponse(
        success=True,
        data=final_report,
        message="AI 기반 데이터 가치 평가가 완료되었습니다.",
    )


# ⭐ 빠른 평가 요청 모델 (user_id 선택적)
class QuickEvaluateRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=200)


# ⭐ 빠른 평가 응답 모델
class QuickEvaluateResponse(BaseModel):
    success: bool
    data: FinalQualityReport
    message: str
    stage: str  # "quick" 또는 "final"


@app.post("/evaluate-quick", response_model=QuickEvaluateResponse)
async def evaluate_query_quick(request: QuickEvaluateRequest):
    """
    빠른 품질 평가 (Legacy만 사용, ~0.1초)
    - AI 분석 없이 즉시 결과 반환
    - 점진적 UI를 위한 1단계 평가
    """
    query_text = request.query.strip()
    
    # Legacy 분석만 실행 (매우 빠름: ~0.1초)
    legacy_report = evaluate_data_value_legacy(query_text)
    
    # Legacy 결과를 FinalQualityReport 형식으로 변환
    quick_report = FinalQualityReport(
        score=legacy_report.score,
        suggestions=legacy_report.suggestions,
        keywords=legacy_report.keywords,
        commercialValue=legacy_report.commercialValue,
        ai_analysis=None,
        needsImprovement=False,
        aiSuggestions=None,
    )
    
    print(f"⚡ 빠른 평가 완료: {query_text[:30]}... → {quick_report.score}점")
    
    return QuickEvaluateResponse(
        success=True,
        data=quick_report,
        message="빠른 평가가 완료되었습니다. AI 정밀 분석 중...",
        stage="quick",
    )


@app.get("/health")
async def health_check():
    from cache import get_redis

    db_status = "connected" if database.is_connected else "disconnected"
    redis_status = "connected" if await get_redis() else "disconnected"
    return {
        "status": "healthy",
        "service": "Analysis Service v2.0",
        "database": db_status,
        "redis": redis_status,
        "ai_model": "models/gemini-flash-latest",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
