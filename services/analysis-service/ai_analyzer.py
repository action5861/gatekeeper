# services/analysis-service/ai_analyzer.py
import os
import json
from typing import Any, Optional, List, Literal, cast
from pydantic import BaseModel, Field

# Gemini SDK (pyright가 이 경로를 더 잘 인식)
from google import generativeai as genai

# (선택) .env 사용 시 환경변수 로드
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass


# --- AI 응답을 위한 Pydantic 모델 ---
class AiAnalysisReport(BaseModel):
    commercial_intent: float = Field(..., description="상업적 의도 점수 (0.0 ~ 1.0)")
    specificity_level: float = Field(..., description="검색어 구체성 점수 (0.0 ~ 1.0)")
    value_category: Literal[
        "Shopping",
        "Travel",
        "Finance",
        "Information",
        "Local",
        "Entertainment",
        "Health",
        "Other",
    ]
    buyer_journey_stage: Literal[
        "Awareness", "Consideration", "Decision", "Retention"
    ] = Field(..., description="구매 여정 단계")
    primary_emotion: Literal[
        "Curiosity", "Urgency", "Doubt", "Excitement", "Neutral"
    ] = Field(..., description="검색어에 담긴 주된 감정")
    predicted_keywords: List[str] = Field(
        ..., description="AI가 예측한 연관 핵심 키워드"
    )


# --- Gemini API 설정 ---
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
MODEL_NAME = os.getenv("GEMINI_MODEL", "models/gemini-flash-latest")

_model: Optional[Any] = None  # 전역 캐시


def _init_model() -> Any:
    """모델 초기화 (린터 친화적으로 attr-defined 무시)"""
    global _model
    if not API_KEY.strip():
        raise RuntimeError("GEMINI_API_KEY/GOOGLE_API_KEY 가 설정되지 않았습니다.")
    genai.configure(api_key=API_KEY)  # type: ignore[attr-defined]
    _model = cast(Any, genai).GenerativeModel(MODEL_NAME)  # type: ignore[attr-defined]
    return _model


def _get_model() -> Any:
    """Optional 제거를 위해 지역 변수로 확정"""
    global _model
    if _model is None:
        return _init_model()
    return _model


# --- 마스터 프롬프트 ---
MASTER_PROMPT_TEMPLATE = """
You are a world-class market analyst and data scientist. Your task is to analyze the commercial value of a user's search query.
Analyze the following query based on multiple dimensions and respond ONLY with a valid JSON object that conforms to the provided schema.

Search Query: "{query}"

JSON Schema to follow:
{{
"commercial_intent": "float (0.0 to 1.0)",
"specificity_level": "float (0.0 to 1.0)",
"value_category": "string (Choose one from: 'Shopping', 'Travel', 'Finance', 'Information', 'Local', 'Entertainment', 'Health', 'Other')",
"buyer_journey_stage": "string (Choose one from: 'Awareness', 'Consideration', 'Decision', 'Retention')",
"primary_emotion": "string (Choose one from: 'Curiosity', 'Urgency', 'Doubt', 'Excitement', 'Neutral')",
"predicted_keywords": "array of strings (Predict 3-5 core keywords)"
}}
Return JSON only, without any extra commentary or code fences.
"""


async def analyze_query_with_ai(query: str) -> AiAnalysisReport:
    """Gemini API 호출 → Pydantic 모델 반환"""
    model = _get_model()  # Optional 아님

    prompt = MASTER_PROMPT_TEMPLATE.format(query=query)

    try:
        responder = getattr(model, "generate_content_async", None)
        if callable(responder):
            response = await model.generate_content_async(prompt)  # type: ignore[attr-defined]
        else:
            response = model.generate_content(prompt)  # type: ignore[attr-defined]
    except Exception as e:
        raise ConnectionError(f"Gemini 호출 실패: {e}")

    # --- 응답 텍스트 추출 (버전 호환) ---
    text = getattr(response, "text", None)
    if not text or not text.strip():
        candidates = getattr(response, "candidates", []) or []
        for c in candidates:
            content = getattr(c, "content", None)
            parts = getattr(content, "parts", []) if content else []
            if parts and hasattr(parts[0], "text"):
                text = parts[0].text
                if text and text.strip():
                    break

    if not text or not text.strip():
        raise ValueError("Gemini 응답이 비어있습니다.")

    raw = text.strip()
    # 혹시 모델이 ```json 코드블록을 붙였다면 방어적으로 제거
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # 마지막 방어: 중괄호 범위 추출
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            data = json.loads(raw[start : end + 1])
        else:
            raise

    return AiAnalysisReport(**data)


# --- 검색어 개선 제안 생성 (30점 미만 검색어용) ---
IMPROVEMENT_PROMPT_TEMPLATE = """
You are a search query optimization expert for an ad marketplace.

Original Query: "{query}"

This query has LOW commercial value. Generate 3 improved alternatives that:
1. Add clear purchase/shopping intent (words like: buy, purchase, recommend, compare, best)
2. Include specific product names or brands
3. Are highly commercial and specific
4. Are naturally related to the original query
5. Return in Korean if original query is Korean

Return ONLY valid JSON (no code fences):
{{
  "suggestions": [
    {{"query": "improved query 1", "reason": "구매 의도 추가"}},
    {{"query": "improved query 2", "reason": "구체적 제품명 포함"}},
    {{"query": "improved query 3", "reason": "브랜드명 + 구매 키워드"}}
  ]
}}

Examples:
- "날씨" → "날씨 앱 추천 2024", "스마트 온도계 구매", "실내 온습도계"
- "뉴스" → "뉴스 구독 서비스 비교", "뉴스 앱 프리미엄", "조선일보 구독"
- "시간" → "손목시계 추천", "애플워치 최저가", "벽시계 구매"
"""


async def generate_improved_queries(original_query: str) -> List[dict]:
    """저품질 검색어를 개선된 검색어 3개로 변환"""
    model = _get_model()

    prompt = IMPROVEMENT_PROMPT_TEMPLATE.format(query=original_query)

    try:
        responder = getattr(model, "generate_content_async", None)
        if callable(responder):
            response = await model.generate_content_async(prompt)  # type: ignore[attr-defined]
        else:
            response = model.generate_content(prompt)  # type: ignore[attr-defined]
    except Exception as e:
        print(f"⚠️ Improvement generation failed: {e}")
        return []

    # 응답 텍스트 추출
    text = getattr(response, "text", None)
    if not text or not text.strip():
        candidates = getattr(response, "candidates", []) or []
        for c in candidates:
            content = getattr(c, "content", None)
            parts = getattr(content, "parts", []) if content else []
            if parts and hasattr(parts[0], "text"):
                text = parts[0].text
                if text and text.strip():
                    break

    if not text or not text.strip():
        print("⚠️ Empty improvement response")
        return []

    raw = text.strip()
    # 코드블록 제거
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # JSON 추출 시도
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            data = json.loads(raw[start : end + 1])
        else:
            print(f"⚠️ Failed to parse improvement JSON: {raw[:100]}")
            return []

    suggestions = data.get("suggestions", [])
    return suggestions[:3]  # 최대 3개
