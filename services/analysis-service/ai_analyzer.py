# services/analysis-service/ai_analyzer.py
import hashlib
import json
import os
from typing import Any, List, Literal, Optional, cast
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


# --- 마스터 프롬프트 (v2.0 - 상세 가이드라인 포함) ---
MASTER_PROMPT_TEMPLATE = """
You are a world-class market analyst and data scientist working for an intent exchange
that rewards users based on the QUALITY of their search queries.

Your objective:
- Evaluate how commercially valuable and specific a user's search query is.
- Produce stable, consistent scoring based on clearly defined criteria.
- Ensure advertisers can safely bid, and users with high-quality queries can receive higher rewards.

Analyze the following search query and respond ONLY with a valid JSON object.

Search Query: "{query}"

------------------------------------------------------------
### 1) commercial_intent (0.0 ~ 1.0) — PURCHASE INTENT SCALE
------------------------------------------------------------

0.0 ~ 0.2 : SPAM / INVALID / NO VALUE
- Gibberish, random characters, single letters, keyboard mashing.
- Profanity, adult content, illegal queries.
- Bot-like patterns, repeated characters.
Examples: "ㅁㄴㅇㄹ", "asdf", "ㅋㅋㅋㅋ", "테스트", "1234"

0.2 ~ 0.4 : Very low commercial intent.
- General curiosity, news, weather, time.
- No commercial outcome possible.
Examples: "날씨", "뉴스", "시간", "hello", "오늘 몇일"

0.4 ~ 0.6 : Moderate commercial or research intent.
- User is researching but not yet ready to buy.
- Broad category, early-stage interest.
Examples: "아이폰 16 출시일", "쏘렌토 연비", "제주도 여행 코스"

0.6 ~ 0.8 : Strong commercial intent.
- Clear interest in products/services with comparison mindset.
- User is actively considering purchase.
Examples: "아이폰 16 프로 후기", "강남 눈성형 추천", "전기차 보조금"

0.8 ~ 1.0 : Very strong purchase or transaction intent.
- Clear willingness to buy, compare prices, request quotes.
- User is ready to take action NOW.
Examples: "아이폰 16 프로 자급제 최저가", "강남 눈성형 가격 비교",
          "자동차 보험 견적", "삼성화재 다이렉트 가입", "오늘 배송 가능"

------------------------------------------------------------
### 2) specificity_level (0.0 ~ 1.0) — QUERY PRECISION SCALE
------------------------------------------------------------

0.0 ~ 0.2 : Single word / extremely vague.
Examples: "보험", "여행", "신발", "폰"

0.2 ~ 0.4 : Broad category, no specifics.
Examples: "남자 신발", "해외여행", "스마트폰 추천"

0.4 ~ 0.6 : Somewhat specific — category + brand OR location.
Examples: "하와이 패키지", "나이키 러닝화", "강남 피부과"

0.6 ~ 0.8 : Specific — brand + model OR location + service.
Examples: "나이키 베이퍼플라이 3", "제주도 롯데호텔", "강남 눈성형 비용"

0.8 ~ 1.0 : Highly specific — brand + model + condition/action/size.
Examples: "나이키 베이퍼플라이 3 사이즈 270 최저가",
          "제주도 롯데호텔 조식 포함 12월 예약"

------------------------------------------------------------
### 3) value_category (ENUM SELECTION RULES)
------------------------------------------------------------
Choose the SINGLE best category that represents the main commercial domain:
- Shopping: 쇼핑/제품 구매 관련
- Travel: 여행/숙박/항공
- Finance: 보험/대출/투자/은행
- Information: 정보 탐색 중심 (상업적 가치 낮음)
- Local: 지역 기반 서비스 (예: 강남 피부과, 홍대 맛집)
- Entertainment: 공연/영화/취미/게임
- Health: 병원/시술/운동/의료/건강식품
- Other: 위에 포함되지 않는 경우

------------------------------------------------------------
### 4) buyer_journey_stage (ENUM SELECTION RULES)
------------------------------------------------------------
Classify based on user's intent depth:

- Awareness: 개념 탐색, 정보만 찾는 단계 (예: "전기차란")
- Consideration: 특정 브랜드/카테고리 후보 비교 단계 (예: "테슬라 vs 현대")
- Decision: 가격 비교, 견적 요청, 구매 직전 단계 (예: "테슬라 모델3 최저가")
- Retention: 기존 고객의 재구매/추가 구매 의도 (예: "테슬라 충전카드 재발급")

------------------------------------------------------------
### 5) primary_emotion (ENUM SELECTION RULES)
------------------------------------------------------------
Choose the emotion that best represents the user's motivation:

- Curiosity: 단순 호기심, 정보 탐색
- Urgency: 긴급한 필요 (예: 오늘 배송, 보험 당일 가입, 급처)
- Doubt: 비교/검토/리스크 고려 느낌 (예: 후기, 장단점, 부작용)
- Excitement: 새 제품/여행/구매 기대감 (예: 신상, 출시, 예약)
- Neutral: 감정적 신호 없음

------------------------------------------------------------
### 6) predicted_keywords (CRITICAL RULE)
------------------------------------------------------------
Return 3–5 keywords that would help advertisers match the query.
- MUST be written in Korean if the user's query is Korean.
- Should reflect commercial intent (brand, model, price, compare, buy, quote).
- Avoid generic terms like "정보", "검색", "추천".
- Include the main subject + action/attribute keywords.

Good examples:
["아이폰16", "자급제", "최저가", "가격비교"]
["강남", "눈성형", "후기", "비용"]
["제주도", "호텔", "조식포함", "예약"]

Bad examples:
["정보", "검색", "추천", "좋은"]

------------------------------------------------------------
### Language & output format
------------------------------------------------------------
- Return JSON only. No markdown, no code fences, no commentary.
- Enum values MUST remain in English.
- All free-text values (predicted_keywords) MUST follow the language of the original query.
- Korean query → Korean keywords.

------------------------------------------------------------
### JSON Schema to follow EXACTLY
------------------------------------------------------------
{{
  "commercial_intent": float,
  "specificity_level": float,
  "value_category": "Shopping | Travel | Finance | Information | Local | Entertainment | Health | Other",
  "buyer_journey_stage": "Awareness | Consideration | Decision | Retention",
  "primary_emotion": "Curiosity | Urgency | Doubt | Excitement | Neutral",
  "predicted_keywords": ["string", "string", "string"]
}}
"""


def _make_analysis_cache_key(query: str) -> str:
    """검색어 기반 캐시 키 생성 (analysis:keyword:{hashed_query})"""
    normalized = query.strip().lower()
    h = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"analysis:keyword:{h}"


async def analyze_query_with_ai(query: str) -> AiAnalysisReport:
    """Gemini API 호출 → Pydantic 모델 반환 (Redis 캐싱 적용)"""
    try:
        from cache import get_cached_analysis, set_cached_analysis

        cache_key = _make_analysis_cache_key(query)
        cached_json = await get_cached_analysis(cache_key)
        if cached_json:
            print("🚀 Cache Hit!")
            data = json.loads(cached_json)
            return AiAnalysisReport(**data)
    except Exception:
        pass  # Redis 실패 시 기존 Gemini API 호출로 Fallback

    # Cache Miss → Gemini API 호출 (캐시 없음 또는 Redis 미연결)
    print("📤 Cache Miss → Gemini API 호출")
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

    report = AiAnalysisReport(**data)

    # 캐시에 저장 (실패해도 결과는 반환)
    try:
        from cache import set_cached_analysis

        cache_key = _make_analysis_cache_key(query)
        await set_cached_analysis(cache_key, report.model_dump_json())
    except Exception:
        pass

    return report


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
