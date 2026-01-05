# services/website-analysis-service/main.py
"""
웹사이트 분석 서비스 - Gemini AI를 사용하여 광고주 웹사이트를 분석하고
키워드/카테고리를 추천합니다. 키워드는 임베딩 벡터와 함께 저장됩니다.

=== 필수 데이터베이스 설정 (pgvector) ===

1. PostgreSQL에 pgvector 확장 설치:
   CREATE EXTENSION IF NOT EXISTS vector;

2. advertiser_keywords 테이블에 embedding 컬럼 추가:
   ALTER TABLE advertiser_keywords
   ADD COLUMN IF NOT EXISTS embedding vector(768);

3. (선택) 유사도 검색을 위한 인덱스 생성:
   CREATE INDEX IF NOT EXISTS idx_advertiser_keywords_embedding
   ON advertiser_keywords USING ivfflat (embedding vector_cosine_ops)
   WITH (lists = 100);

================================================
"""
import os
import json
import logging
import asyncio
from typing import Any, List, cast

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright  # type: ignore
from bs4 import BeautifulSoup  # type: ignore

# Gemini SDK (pyright가 이 경로를 더 잘 인식)
from google import generativeai as genai  # type: ignore

# 안전설정 enum (버전에 따라 없을 수 있어 try/except)
try:
    from google.generativeai.types import HarmCategory, HarmBlockThreshold  # type: ignore
except Exception:
    HarmCategory = None  # type: ignore[assignment]
    HarmBlockThreshold = None  # type: ignore[assignment]

# Database
from database import database, connect_to_database, disconnect_from_database

# --- 로깅 설정 ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- 환경 변수 및 모델 설정 ---
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
MODEL_NAME = os.getenv("GEMINI_MODEL", "models/gemini-2.5-pro")
EMBEDDING_MODEL_NAME = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")

if not API_KEY.strip():
    raise RuntimeError("GEMINI_API_KEY/GOOGLE_API_KEY 가 설정되지 않았습니다.")

genai.configure(api_key=API_KEY)  # type: ignore[attr-defined]
model: Any = cast(Any, genai).GenerativeModel(MODEL_NAME)  # type: ignore[attr-defined]

app = FastAPI()


# --- Pydantic 모델 ---
class AnalysisRequest(BaseModel):
    advertiser_id: int
    url: str


# --- 데이터베이스 연결 ---
@app.on_event("startup")
async def startup():
    await connect_to_database()
    logger.info("✅ Website Analysis Service started successfully")
    logger.info(f"[Gemini] KEY_SET={bool(API_KEY)}, MODEL={MODEL_NAME}")
    logger.info(f"[Gemini] EMBEDDING_MODEL={EMBEDDING_MODEL_NAME}")


@app.on_event("shutdown")
async def shutdown():
    await disconnect_from_database()


# --- 핵심 로직: 웹사이트 스크래핑 ---
async def scrape_website_text(url: str) -> str:
    """
    Playwright를 사용하여 웹사이트에서 텍스트를 스크래핑합니다.
    networkidle 타임아웃 시 domcontentloaded로 폴백합니다.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            # 1차 시도: networkidle (최대 60초)
            try:
                await page.goto(url, wait_until="networkidle", timeout=60000)
                logger.info(f"✅ networkidle로 페이지 로드 완료: {url}")
            except Exception as e:
                logger.warning(
                    f"⚠️ networkidle 타임아웃, domcontentloaded로 재시도: {url} - {str(e)}"
                )
                # 2차 시도: domcontentloaded (최대 30초)
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    logger.info(f"✅ domcontentloaded로 페이지 로드 완료: {url}")
                    # 추가 대기: JavaScript 실행을 위해 3초 대기
                    await page.wait_for_timeout(3000)
                except Exception as e2:
                    logger.warning(
                        f"⚠️ domcontentloaded도 실패, load로 재시도: {url} - {str(e2)}"
                    )
                    # 3차 시도: load (최대 30초)
                    try:
                        await page.goto(url, wait_until="load", timeout=30000)
                        logger.info(f"✅ load로 페이지 로드 완료: {url}")
                        # 추가 대기: JavaScript 실행을 위해 2초 대기
                        await page.wait_for_timeout(2000)
                    except Exception as e3:
                        logger.error(f"❌ 모든 로드 전략 실패: {url} - {str(e3)}")
                        # 마지막 시도: 타임아웃 없이 최소한의 콘텐츠라도 가져오기
                        try:
                            await page.goto(url, wait_until="commit", timeout=10000)
                            await page.wait_for_timeout(5000)  # 5초 대기
                            logger.info(f"⚠️ commit으로 최소 콘텐츠 로드: {url}")
                        except Exception as e4:
                            logger.error(f"❌ 최종 로드 실패: {url} - {str(e4)}")
                            return ""

            html_content = await page.content()
            soup = BeautifulSoup(html_content, "html.parser")
            # 불필요한 태그 제거
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
            # 최대 15000자로 제한
            result = " ".join(text.split())[:15000]
            logger.info(f"✅ 텍스트 추출 완료: {len(result)}자")
            return result
        except Exception as e:
            logger.error(f"❌ 스크래핑 중 예외 발생: {url} - {str(e)}", exc_info=True)
            return ""
        finally:
            await browser.close()


# --- Gemini 분석 로직 (업그레이드된 SEO 프롬프트) ---
async def analyze_with_gemini(text_content: str) -> dict:
    """
    Gemini AI를 사용하여 웹사이트 텍스트를 분석합니다.
    (업그레이드된 Search Intent 기반 프롬프트 적용)

    Returns:
        - business_summary: 80~150자 비즈니스 요약
        - recommended_keywords: 30~40개 검색 의도 기반 키워드
        - recommended_categories: 3~7개 상위 카테고리
    """
    # 텍스트가 너무 짧으면 분석 불가
    if not text_content or len(text_content.strip()) < 50:
        logger.warning("⚠️ 분석할 텍스트가 너무 짧습니다.")
        return {}

    # 표준 카테고리 (auction-service 및 advertiser-service와 통일)
    STANDARD_CATEGORIES = [
        "전자제품",
        "패션/뷰티",
        "생활/건강",
        "식품/음료",
        "스포츠/레저/자동차",
        "유아/아동",
        "여행/문화",
        "반려동물",
        "디지털 콘텐츠",
        "부동산/인테리어",
        "의료/건강",
        "서비스",
        "교육/도서",
        "비영리/공공",
    ]

    # 🔥 업그레이드된 SEO 프롬프트 (Search Intent + 표준 카테고리 기반)
    prompt = f"""
당신은 최고의 검색 엔진 최적화(SEO) 및 데이터 분석가입니다.
아래 웹사이트 텍스트를 분석하여, 잠재 고객이 실제로 검색할 만한 **검색 의도(Search Intent)** 기반 키워드를 추출하고,
해당 비즈니스를 아래에 주어진 **표준 카테고리 목록 중 정확히 하나**로 분류하세요.

반드시 아래 형식의 **유효한 JSON만** 출력하세요.
설명 문장, 주석, 코드 블록, 백틱(```)은 절대 포함하지 마세요.

출력 형식:
{{
  "business_summary": "이 비즈니스를 한국어로 80~150자 사이로 요약한 문장",
  "primary_category": "표준 카테고리 중 하나",
  "recommended_keywords": ["키워드1", "키워드2", ...],
  "recommended_categories": ["카테고리1", "카테고리2", ...]
}}

요구사항:
- 모든 출력은 **한국어**로 작성합니다.
- primary_category는 반드시 아래 **표준 카테고리 목록(STANDARD_CATEGORIES)** 중 **정확히 하나만** 선택하여 사용합니다.
- "recommended_keywords"에는 **총 30~40개**의 키워드를 넣습니다.
- 각 키워드는 **1~7단어 이내의 짧은 표현**으로 작성합니다.
- 검색 사용자가 실제로 입력할 법한 **자연스러운 검색어/프레이즈** 위주로 작성합니다.

[키워드 구성 전략 (중요)]
recommended_keywords 배열 하나에, 아래 비율을 참고하여 30~40개를 모두 섞어서 넣으세요.
1) 핵심 상품/서비스명 (약 40%)
   - 구체적인 제품명, 서비스명, 모델명
   - 예: "강남역 회식 가능한 고깃집", "프리미엄 달리기 운동화"
2) 사용자의 상황/고민/니즈 (약 30%)
   - 사용자의 문제, 욕구, 상황을 표현하는 문장형/구문형 검색어
   - 예: "발이 안 아픈 출퇴근용 신발", "가성비 좋은 야근용 도시락"
3) 타겟 페르소나 (약 10%)
   - 이 서비스를 사용할만한 사람/집단
   - 예: "자취생 필수템", "신혼부부 추천", "30대 직장인 운동화"
4) 업계 전문 용어 및 카테고리 키워드 (약 20%)
   - 해당 산업에서 실제로 사용하는 전문 용어, 서비스 유형
   - 예: "러닝화 쿠션 안정성", "탄소강 그릴", "기업 단체 회식 패키지"

[카테고리 추출 가이드]
웹사이트 비즈니스를 아래 **표준 카테고리 목록(STANDARD_CATEGORIES)** 중에서만 분류해야 합니다.
절대로 새로운 카테고리 이름을 만들지 마세요.

STANDARD_CATEGORIES:
- 전자제품
- 패션/뷰티
- 생활/건강
- 식품/음료
- 스포츠/레저/자동차
- 유아/아동
- 여행/문화
- 반려동물
- 디지털 콘텐츠
- 부동산/인테리어
- 의료/건강
- 서비스
- 교육/도서
- 비영리/공공

규칙:
1) primary_category:
   - 위 STANDARD_CATEGORIES 중 이 비즈니스를 가장 잘 대표하는 **단 하나**만 선택하세요.
   - 예: 안경점, 안과, 렌즈 쇼핑몰 → "의료/건강" 또는 "패션/뷰티" 중 더 적합한 하나.
   - 예: 해외 아동 후원, NGO, 기부 단체 → "비영리/공공".
2) recommended_categories:
   - STANDARD_CATEGORIES 중 이 비즈니스와 밀접하게 관련된 1~4개 정도를 선택하세요.
   - primary_category를 반드시 포함시키거나, primary_category만 단독으로 둘 수도 있습니다.
   - STANDARD_CATEGORIES에 없는 이름은 절대로 사용하지 마세요.

[제약 사항]
- "문의하기", "로그인", "회원가입", "장바구니", "홈페이지" 같은 일반적인 UI 텍스트는 절대 포함하지 마세요.
- 회사명 그대로만 반복하지 말고, 실제 사용자가 검색할 표현으로 변형하세요.
- 의미가 거의 같은 키워드를 과도하게 중복 생성하지 마세요.
- 출력은 반드시 위에서 정의한 JSON 형식 하나만 포함해야 합니다.

---
웹사이트 텍스트:
{text_content[:15000]}
---
"""

    # safety_settings: 버전 호환을 위해 list[dict] 형태 권장
    safety_settings = None
    if HarmCategory and HarmBlockThreshold:
        safety_settings = [
            {
                "category": HarmCategory.HARM_CATEGORY_HARASSMENT,
                "threshold": HarmBlockThreshold.BLOCK_NONE,
            },  # type: ignore[attr-defined]
            {
                "category": HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            },  # type: ignore[attr-defined]
            {
                "category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                "threshold": HarmBlockThreshold.BLOCK_NONE,
            },  # type: ignore[attr-defined]
            {
                "category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            },  # type: ignore[attr-defined]
        ]

    try:
        responder = getattr(model, "generate_content_async", None)
        if callable(responder):
            response = await model.generate_content_async(  # type: ignore[attr-defined]
                prompt, safety_settings=safety_settings
            )
        else:
            response = model.generate_content(prompt, safety_settings=safety_settings)  # type: ignore[attr-defined]

        text = getattr(response, "text", "") or ""
        if not text.strip():
            # candidates 기반 방어
            candidates = getattr(response, "candidates", []) or []
            for c in candidates:
                content = getattr(c, "content", None)
                parts = getattr(content, "parts", []) if content else []
                if parts and hasattr(parts[0], "text"):
                    text = parts[0].text or ""
                    if text.strip():
                        break

        if not text.strip():
            logger.error("❌ Gemini 응답이 비어있습니다.")
            return {}

        raw = text.strip()

        # 마크다운 코드블록 제거 (프롬프트에서 막았지만 혹시 몰라 한 번 더 방어)
        if raw.startswith("```json"):
            raw = raw[7:]
        if raw.startswith("```"):
            raw = raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 부분 추출 시도
            start, end = raw.find("{"), raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                result = json.loads(raw[start : end + 1])
            else:
                raise

        # 유효성 보정 + 개수 제한 (프롬프트가 30~40개 목표이므로 넉넉하게)
        result.setdefault("business_summary", "AI 분석 요약 없음")
        result.setdefault("recommended_keywords", [])
        result.setdefault("recommended_categories", [])
        result.setdefault("primary_category", "")

        # 키워드 최대 50개, 카테고리 최대 10개까지 허용
        result["recommended_keywords"] = result["recommended_keywords"][:50]
        result["recommended_categories"] = result["recommended_categories"][:10]

        # 로깅: Gemini 응답 확인
        logger.info(
            f"🤖 Gemini 분석 결과: summary={len(result.get('business_summary', ''))}자, "
            f"keywords={len(result.get('recommended_keywords', []))}개, "
            f"categories={len(result.get('recommended_categories', []))}개"
        )
        logger.info(f"🤖 primary_category: {result.get('primary_category')}")
        logger.info(f"🤖 키워드 샘플: {result.get('recommended_keywords', [])[:5]}")
        logger.info(f"🤖 카테고리 샘플: {result.get('recommended_categories', [])[:3]}")

        return result

    except Exception as e:
        logger.error(f"❌ Error calling/parsing Gemini API: {e}", exc_info=True)
        return {}


# --- 임베딩 생성 함수 (최적화: asyncio.to_thread + 방어적 파싱) ---
async def get_text_embedding(text: str) -> List[float]:
    """
    Google Gemini 임베딩 모델을 사용하여 텍스트 임베딩 벡터를 생성합니다.

    - 환경변수 GEMINI_EMBEDDING_MODEL로 모델 설정 가능 (기본: models/text-embedding-004)
    - task_type: 'retrieval_document' (DB 저장용)
    - asyncio.to_thread()로 동기 API를 논블로킹으로 실행
    - 실패 시 빈 리스트([]) 반환

    Note:
        검색 시에는 task_type='retrieval_query'를 사용해야 함
    """
    clean = (text or "").strip()
    if not clean:
        logger.warning("⚠️ 임베딩 생성 요청 텍스트가 비어있습니다.")
        return []

    def _embed_sync() -> List[float]:
        """동기 임베딩 함수 (스레드에서 실행됨)"""
        try:
            # 최신 SDK 기준: genai.embed_content 사용
            embed_fn = getattr(cast(Any, genai), "embed_content", None)
            if not callable(embed_fn):
                logger.error("❌ genai.embed_content 함수를 찾을 수 없습니다.")
                return []

            res = embed_fn(
                model=EMBEDDING_MODEL_NAME,
                content=clean,
                task_type="retrieval_document",
            )

            # 응답 구조 방어적 파싱 (SDK 버전에 따라 다를 수 있음)
            embedding: Any = None

            # dict 형태 응답
            if isinstance(res, dict):
                emb = res.get("embedding")
                if isinstance(emb, dict) and "values" in emb:
                    embedding = emb["values"]
                elif isinstance(emb, list):
                    embedding = emb
                elif "values" in res:
                    embedding = res["values"]
            else:
                # 객체 형태 응답
                emb_obj = getattr(res, "embedding", None)
                if emb_obj is not None:
                    if isinstance(emb_obj, list):
                        embedding = emb_obj
                    else:
                        vals = getattr(emb_obj, "values", None)
                        if vals is not None:
                            embedding = vals

            if embedding is None:
                logger.warning("⚠️ 임베딩 응답에서 벡터를 찾지 못했습니다.")
                return []

            return list(embedding)
        except Exception as e:
            logger.error(f"❌ 임베딩 생성 중 오류 (sync): {e}", exc_info=True)
            return []

    try:
        # asyncio.to_thread로 동기 함수를 논블로킹으로 실행
        vector = await asyncio.to_thread(_embed_sync)

        if not vector:
            logger.warning(f"⚠️ 임베딩 생성 결과가 비었습니다. text='{clean[:30]}...'")
        else:
            logger.info(
                f"📐 임베딩 생성 완료: 길이={len(vector)}, text='{clean[:30]}...'"
            )

        return vector
    except Exception as e:
        logger.error(f"❌ 임베딩 생성 중 오류 (async): {e}", exc_info=True)
        return []


# --- 분석 결과 저장 ---
async def save_analysis_results(advertiser_id: int, results: dict):
    """
    분석 결과를 데이터베이스에 저장합니다.
    - website_analysis: advertiser_reviews
    - recommended_keywords: advertiser_keywords (+ 임베딩)
    - recommended_categories: advertiser_categories

    Note:
        - 임베딩은 pgvector 형식으로 저장됨 (vector(768))
        - 임베딩 생성 실패 시 키워드만 저장 (embedding = NULL)
    """
    logger.info(f"💾 [{advertiser_id}] 분석 결과 저장 시작")
    logger.info(f"💾 [{advertiser_id}] results keys: {list(results.keys())}")

    summary = results.get("business_summary", "AI 분석 요약 없음")
    logger.info(f"💾 [{advertiser_id}] summary: {summary[:100]}...")

    # 리뷰 요약 저장
    await database.execute(
        """
        UPDATE advertiser_reviews
        SET website_analysis = :summary,
            review_status = 'pending'
        WHERE advertiser_id = :advertiser_id
        """,
        {"summary": summary, "advertiser_id": advertiser_id},
    )

    # --- 키워드 + 임베딩 저장 ---
    keywords = results.get("recommended_keywords", [])
    logger.info(
        f"💾 [{advertiser_id}] 키워드 개수: {len(keywords)}, 키워드: {keywords}"
    )

    keyword_count = 0
    embedding_count = 0

    for keyword in keywords:
        if not (keyword and isinstance(keyword, str) and keyword.strip()):
            continue

        clean_keyword = keyword.strip()
        logger.info(
            f"💾 [{advertiser_id}] 키워드 저장 준비: '{clean_keyword}' (임베딩 생성 시도)"
        )

        # 1) 임베딩 생성 시도
        embedding_vector = await get_text_embedding(clean_keyword)

        if embedding_vector:
            # 임베딩 성공: pgvector 형식으로 저장
            # [수정 전] VALUES (..., :embedding::vector, 'ai_suggested', 'broad', 1)
            # [수정 후] VALUES (..., CAST(:embedding AS vector), 'ai_suggested', 'broad', 1)
            embedding_str = str(embedding_vector)

            await database.execute(
                """
                INSERT INTO advertiser_keywords
                    (advertiser_id, keyword, embedding, source, match_type, priority)
                VALUES
                    (:advertiser_id,
                     :keyword,
                     CAST(:embedding AS vector),
                     'ai_suggested',
                     'broad',
                     1)
                """,
                {
                    "advertiser_id": advertiser_id,
                    "keyword": clean_keyword,
                    "embedding": embedding_str,
                },
            )
            embedding_count += 1
            logger.info(
                f"✅ [{advertiser_id}] 키워드+임베딩 저장: '{clean_keyword}' ({len(embedding_vector)}차원)"
            )
        else:
            # 임베딩 실패: 키워드만 저장 (embedding = NULL)
            await database.execute(
                """
                INSERT INTO advertiser_keywords
                    (advertiser_id, keyword, source, match_type, priority)
                VALUES
                    (:advertiser_id, :keyword, 'ai_suggested', 'broad', 1)
                """,
                {
                    "advertiser_id": advertiser_id,
                    "keyword": clean_keyword,
                },
            )
            logger.warning(
                f"⚠️ [{advertiser_id}] 키워드만 저장 (임베딩 실패): '{clean_keyword}'"
            )

        keyword_count += 1

    logger.info(
        f"💾 [{advertiser_id}] 저장된 키워드: {keyword_count}개 (임베딩 포함: {embedding_count}개)"
    )

    # --- 카테고리 저장 (AI가 추천한 카테고리를 business_categories ID로 변환하여 저장) ---
    primary_category_name = results.get("primary_category", "")
    recommended_categories = results.get("recommended_categories", [])
    
    # primary_category를 첫 번째로 추가 (중복 제거)
    all_category_names = []
    if primary_category_name:
        all_category_names.append(primary_category_name)
    for cat_name in recommended_categories:
        if cat_name and cat_name not in all_category_names:
            all_category_names.append(cat_name)
    
    category_count = 0
    primary_category_id = None
    
    for idx, category_name in enumerate(all_category_names):
        if not category_name or not isinstance(category_name, str):
            continue
        
        # business_categories 테이블에서 이름으로 검색 (정확히 일치하는 것 우선, 부분 일치도 시도)
        category_info = await database.fetch_one(
            """
            SELECT id, name, path, level
            FROM business_categories
            WHERE is_active = true
            AND (
                name = :name
                OR name ILIKE :name_pattern
                OR path ILIKE :name_pattern
            )
            ORDER BY 
                CASE WHEN name = :name THEN 1 ELSE 2 END,
                level ASC
            LIMIT 1
            """,
            {
                "name": category_name.strip(),
                "name_pattern": f"%{category_name.strip()}%",
            },
        )
        
        if category_info:
            category_id = category_info["id"]
            is_primary = (idx == 0)  # 첫 번째 카테고리를 primary로 설정
            
            if is_primary:
                primary_category_id = category_id
            
            try:
                # advertiser_categories에 저장 (중복 체크)
                existing = await database.fetch_one(
                    """
                    SELECT id FROM advertiser_categories
                    WHERE advertiser_id = :advertiser_id
                    AND category_path = :path
                    """,
                    {
                        "advertiser_id": advertiser_id,
                        "path": category_info["path"],
                    },
                )
                
                if not existing:
                    await database.execute(
                        """
                        INSERT INTO advertiser_categories
                            (advertiser_id, category_path, category_level, is_primary, source)
                        VALUES
                            (:advertiser_id, :path, :level, :is_primary, 'ai_suggested')
                        """,
                        {
                            "advertiser_id": advertiser_id,
                            "path": category_info["path"],
                            "level": category_info["level"],
                            "is_primary": is_primary,
                        },
                    )
                    category_count += 1
                    logger.info(
                        f"✅ [{advertiser_id}] AI 추천 카테고리 저장: '{category_info['name']}' "
                        f"(ID: {category_id}, primary: {is_primary})"
                    )
                else:
                    logger.info(
                        f"ℹ️ [{advertiser_id}] 카테고리 이미 존재: '{category_info['name']}'"
                    )
            except Exception as e:
                logger.error(
                    f"❌ [{advertiser_id}] 카테고리 저장 실패 '{category_name}': {e}"
                )
        else:
            logger.warning(
                f"⚠️ [{advertiser_id}] 카테고리를 찾을 수 없음: '{category_name}' "
                f"(business_categories 테이블에 존재하지 않음)"
            )
    
    logger.info(
        f"💾 [{advertiser_id}] 저장된 카테고리: {category_count}개 "
        f"(primary_category: {primary_category_name})"
    )

    # --- advertisers 상태 업데이트 ---
    await database.execute(
        """
        UPDATE advertisers
        SET approval_status = 'pending'
        WHERE id = :advertiser_id
        """,
        {"advertiser_id": advertiser_id},
    )

    logger.info(
        f"💾 [{advertiser_id}] 분석 결과 저장 완료: 키워드 {keyword_count}개, 카테고리 {category_count}개"
    )


# --- 백그라운드 전체 태스크 ---
async def run_analysis_task(advertiser_id: int, url: str):
    """
    백그라운드에서 실행되는 웹사이트 분석 태스크입니다.
    """
    try:
        logger.info(f"🔍 [{advertiser_id}] 웹사이트 분석 시작: {url}")

        # 1) 상태 변경
        await database.execute(
            """
            UPDATE advertisers
            SET approval_status = 'pending_analysis'
            WHERE id = :advertiser_id
            """,
            {"advertiser_id": advertiser_id},
        )

        # 2) 스크래핑
        scraped_text = await scrape_website_text(url)
        if not scraped_text:
            await database.execute(
                """
                UPDATE advertisers
                SET approval_status = 'pending'
                WHERE id = :advertiser_id
                """,
                {"advertiser_id": advertiser_id},
            )
            await database.execute(
                """
                UPDATE advertiser_reviews
                SET website_analysis = '웹사이트 분석 실패: 사이트 접근 불가',
                    review_status = 'pending'
                WHERE advertiser_id = :advertiser_id
                """,
                {"advertiser_id": advertiser_id},
            )
            return

        # 3) Gemini 분석
        logger.info(f"🔍 [{advertiser_id}] Gemini AI 분석 시작...")
        analysis_results = await analyze_with_gemini(scraped_text)
        logger.info(
            f"🔍 [{advertiser_id}] Gemini AI 분석 완료. 결과 키: "
            f"{list(analysis_results.keys()) if analysis_results else 'None'}"
        )
        if not analysis_results:
            await database.execute(
                """
                UPDATE advertisers
                SET approval_status = 'pending'
                WHERE id = :advertiser_id
                """,
                {"advertiser_id": advertiser_id},
            )
            await database.execute(
                """
                UPDATE advertiser_reviews
                SET website_analysis = '웹사이트 분석 실패: AI 분석 오류',
                    review_status = 'pending'
                WHERE advertiser_id = :advertiser_id
                """,
                {"advertiser_id": advertiser_id},
            )
            return

        # 4) 결과 저장 (키워드 + 임베딩 + 카테고리)
        await save_analysis_results(advertiser_id, analysis_results)
        logger.info(f"✨ [{advertiser_id}] 전체 분석 프로세스 완료")

    except Exception as e:
        logger.error(f"💥 [{advertiser_id}] 분석 중 예외 발생: {e}", exc_info=True)
        try:
            await database.execute(
                """
                UPDATE advertisers
                SET approval_status = 'pending'
                WHERE id = :advertiser_id
                """,
                {"advertiser_id": advertiser_id},
            )
            await database.execute(
                """
                UPDATE advertiser_reviews
                SET website_analysis = :analysis,
                    review_status = 'pending'
                WHERE advertiser_id = :advertiser_id
                """,
                {
                    "analysis": f"웹사이트 분석 실패: {str(e)}",
                    "advertiser_id": advertiser_id,
                },
            )
        except Exception as inner_e:
            logger.error(
                f"💥 [{advertiser_id}] 에러 처리 중 추가 예외: {inner_e}", exc_info=True
            )


# --- API 엔드포인트 ---
@app.post("/analyze")
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    웹사이트 분석을 백그라운드로 시작합니다.
    """
    advertiser = await database.fetch_one(
        """
        SELECT id, website_url
        FROM advertisers
        WHERE id = :advertiser_id
        """,
        {"advertiser_id": request.advertiser_id},
    )
    if not advertiser:
        raise HTTPException(status_code=404, detail="Advertiser not found")

    background_tasks.add_task(run_analysis_task, request.advertiser_id, request.url)
    return {
        "message": "Analysis started in the background.",
        "advertiser_id": request.advertiser_id,
        "url": request.url,
    }


@app.get("/health")
def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "ok", "service": "website-analysis-service"}


@app.get("/status/{advertiser_id}")
async def get_analysis_status(advertiser_id: int):
    """
    특정 광고주의 분석 상태를 조회합니다.
    임베딩 벡터 저장 현황도 포함됩니다.
    """
    advertiser = await database.fetch_one(
        """
        SELECT id, approval_status
        FROM advertisers
        WHERE id = :advertiser_id
        """,
        {"advertiser_id": advertiser_id},
    )
    if not advertiser:
        raise HTTPException(status_code=404, detail="Advertiser not found")

    review = await database.fetch_one(
        """
        SELECT review_status, website_analysis
        FROM advertiser_reviews
        WHERE advertiser_id = :advertiser_id
        """,
        {"advertiser_id": advertiser_id},
    )

    keywords_count = await database.fetch_val(
        """
        SELECT COUNT(*)
        FROM advertiser_keywords
        WHERE advertiser_id = :advertiser_id
          AND source = 'ai_suggested'
        """,
        {"advertiser_id": advertiser_id},
    )

    # 임베딩이 저장된 키워드 개수 조회
    keywords_with_embedding_count = await database.fetch_val(
        """
        SELECT COUNT(*)
        FROM advertiser_keywords
        WHERE advertiser_id = :advertiser_id
          AND source = 'ai_suggested'
          AND embedding IS NOT NULL
        """,
        {"advertiser_id": advertiser_id},
    )

    categories_count = await database.fetch_val(
        """
        SELECT COUNT(*)
        FROM advertiser_categories
        WHERE advertiser_id = :advertiser_id
          AND source = 'ai_suggested'
        """,
        {"advertiser_id": advertiser_id},
    )

    return {
        "advertiser_id": advertiser_id,
        "approval_status": advertiser["approval_status"],
        "review_status": review["review_status"] if review else None,
        "website_analysis": review["website_analysis"] if review else None,
        "ai_suggested_keywords": keywords_count or 0,
        "ai_suggested_keywords_with_embedding": keywords_with_embedding_count or 0,
        "ai_suggested_categories": categories_count or 0,
    }
