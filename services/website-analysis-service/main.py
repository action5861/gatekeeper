# services/website-analysis-service/main.py
import os
import json
import logging
from typing import Any, cast

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
MODEL_NAME = os.getenv("GEMINI_MODEL", "models/gemini-flash-latest")

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


@app.on_event("shutdown")
async def shutdown():
    await disconnect_from_database()


# --- 핵심 로직 ---
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
                logger.warning(f"⚠️ networkidle 타임아웃, domcontentloaded로 재시도: {url} - {str(e)}")
                # 2차 시도: domcontentloaded (최대 30초)
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    logger.info(f"✅ domcontentloaded로 페이지 로드 완료: {url}")
                    # 추가 대기: JavaScript 실행을 위해 3초 대기
                    await page.wait_for_timeout(3000)
                except Exception as e2:
                    logger.warning(f"⚠️ domcontentloaded도 실패, load로 재시도: {url} - {str(e2)}")
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


async def analyze_with_gemini(text_content: str) -> dict:
    """
    Gemini AI를 사용하여 웹사이트 텍스트를 분석합니다.
    """
    prompt = f"""
당신은 최고의 디지털 마케팅 전략가입니다. 아래는 한 기업의 웹사이트에서 추출한 텍스트 데이터입니다.
이 데이터를 기반으로 다음 형식의 JSON 객체를 반드시 생성해주세요:

{{
    "business_summary": "100자 이내로 비즈니스를 요약한 텍스트",
    "recommended_keywords": ["키워드1", "키워드2", "키워드3", ...],
    "recommended_categories": ["카테고리1", "카테고리2", ...]
}}

**중요 지시사항:**
1. business_summary는 반드시 100자 이내로 작성하세요.
2. recommended_keywords는 최소 10개 이상, 최대 20개까지 반드시 포함하세요. 비즈니스와 관련된 검색 키워드를 제시하세요.
3. recommended_categories는 최소 3개 이상, 최대 5개까지 반드시 포함하세요. 비즈니스 카테고리 경로를 제시하세요.
4. JSON 형식만 반환하세요. 코드블록(```), 설명, 추가 텍스트는 포함하지 마세요.
5. 키워드와 카테고리는 비어있는 배열이면 안 됩니다. 반드시 값이 있어야 합니다.

---
웹사이트 텍스트:
{text_content[:5000]}
---
"""

    # safety_settings: 버전 호환을 위해 list[dict] 형태 권장
    safety_settings = None
    if HarmCategory and HarmBlockThreshold:
        safety_settings = [
            {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_NONE},  # type: ignore[attr-defined]
            {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},  # type: ignore[attr-defined]
            {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, "threshold": HarmBlockThreshold.BLOCK_NONE},  # type: ignore[attr-defined]
            {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, "threshold": HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE},  # type: ignore[attr-defined]
        ]

    try:
        responder = getattr(model, "generate_content_async", None)
        if callable(responder):
            response = await model.generate_content_async(prompt, safety_settings=safety_settings)  # type: ignore[attr-defined]
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
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            start, end = raw.find("{"), raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                result = json.loads(raw[start : end + 1])
            else:
                raise

        # 유효성 보정 + 개수 제한
        result.setdefault("business_summary", "AI 분석 요약 없음")
        result.setdefault("recommended_keywords", [])
        result.setdefault("recommended_categories", [])
        result["recommended_keywords"] = result["recommended_keywords"][:20]
        result["recommended_categories"] = result["recommended_categories"][:5]
        
        # 로깅: Gemini 응답 확인
        logger.info(f"🤖 Gemini 분석 결과: summary={len(result.get('business_summary', ''))}자, keywords={len(result.get('recommended_keywords', []))}개, categories={len(result.get('recommended_categories', []))}개")
        logger.info(f"🤖 키워드 샘플: {result.get('recommended_keywords', [])[:5]}")
        logger.info(f"🤖 카테고리 샘플: {result.get('recommended_categories', [])[:3]}")
        
        return result

    except Exception as e:
        logger.error(f"❌ Error calling/parsing Gemini API: {e}", exc_info=True)
        return {}


async def save_analysis_results(advertiser_id: int, results: dict):
    """
    분석 결과를 데이터베이스에 저장합니다.
    """
    logger.info(f"💾 [{advertiser_id}] 분석 결과 저장 시작")
    logger.info(f"💾 [{advertiser_id}] results keys: {list(results.keys())}")
    
    summary = results.get("business_summary", "AI 분석 요약 없음")
    logger.info(f"💾 [{advertiser_id}] summary: {summary[:100]}...")
    
    await database.execute(
        "UPDATE advertiser_reviews SET website_analysis = :summary, review_status = 'pending' WHERE advertiser_id = :advertiser_id",
        {"summary": summary, "advertiser_id": advertiser_id},
    )

    keywords = results.get("recommended_keywords", [])
    logger.info(f"💾 [{advertiser_id}] 키워드 개수: {len(keywords)}, 키워드: {keywords}")
    
    keyword_count = 0
    for keyword in keywords:
        if keyword and isinstance(keyword, str) and keyword.strip():
            await database.execute(
                """
                INSERT INTO advertiser_keywords (advertiser_id, keyword, source, match_type, priority)
                VALUES (:advertiser_id, :keyword, 'ai_suggested', 'broad', 1)
                """,
                {"advertiser_id": advertiser_id, "keyword": keyword.strip()},
            )
            keyword_count += 1
    
    logger.info(f"💾 [{advertiser_id}] 저장된 키워드 개수: {keyword_count}")

    categories = results.get("recommended_categories", [])
    logger.info(f"💾 [{advertiser_id}] 카테고리 개수: {len(categories)}, 카테고리: {categories}")
    
    category_count = 0
    for category in categories:
        if category and isinstance(category, str) and category.strip():
            await database.execute(
                """
                INSERT INTO advertiser_categories (advertiser_id, category_path, source, category_level, is_primary)
                VALUES (:advertiser_id, :category_path, 'ai_suggested', 1, false)
                """,
                {"advertiser_id": advertiser_id, "category_path": category.strip()},
            )
            category_count += 1
    
    logger.info(f"💾 [{advertiser_id}] 저장된 카테고리 개수: {category_count}")

    await database.execute(
        "UPDATE advertisers SET approval_status = 'pending' WHERE id = :advertiser_id",
        {"advertiser_id": advertiser_id},
    )
    
    logger.info(f"💾 [{advertiser_id}] 분석 결과 저장 완료: 키워드 {keyword_count}개, 카테고리 {category_count}개")


async def run_analysis_task(advertiser_id: int, url: str):
    """
    백그라운드에서 실행되는 웹사이트 분석 태스크입니다.
    """
    try:
        logger.info(f"🔍 [{advertiser_id}] 웹사이트 분석 시작: {url}")

        # 1) 상태 변경
        await database.execute(
            "UPDATE advertisers SET approval_status = 'pending_analysis' WHERE id = :advertiser_id",
            {"advertiser_id": advertiser_id},
        )

        # 2) 스크래핑
        scraped_text = await scrape_website_text(url)
        if not scraped_text:
            await database.execute(
                "UPDATE advertisers SET approval_status = 'pending' WHERE id = :advertiser_id",
                {"advertiser_id": advertiser_id},
            )
            await database.execute(
                "UPDATE advertiser_reviews SET website_analysis = '웹사이트 분석 실패: 사이트 접근 불가', review_status = 'pending' WHERE advertiser_id = :advertiser_id",
                {"advertiser_id": advertiser_id},
            )
            return

        # 3) Gemini 분석
        logger.info(f"🔍 [{advertiser_id}] Gemini AI 분석 시작...")
        analysis_results = await analyze_with_gemini(scraped_text)
        logger.info(f"🔍 [{advertiser_id}] Gemini AI 분석 완료. 결과 키: {list(analysis_results.keys()) if analysis_results else 'None'}")
        if not analysis_results:
            await database.execute(
                "UPDATE advertisers SET approval_status = 'pending' WHERE id = :advertiser_id",
                {"advertiser_id": advertiser_id},
            )
            await database.execute(
                "UPDATE advertiser_reviews SET website_analysis = '웹사이트 분석 실패: AI 분석 오류', review_status = 'pending' WHERE advertiser_id = :advertiser_id",
                {"advertiser_id": advertiser_id},
            )
            return

        # 4) 결과 저장
        await save_analysis_results(advertiser_id, analysis_results)
        logger.info(f"✨ [{advertiser_id}] 전체 분석 프로세스 완료")

    except Exception as e:
        logger.error(f"💥 [{advertiser_id}] 분석 중 예외 발생: {e}", exc_info=True)
        try:
            await database.execute(
                "UPDATE advertisers SET approval_status = 'pending' WHERE id = :advertiser_id",
                {"advertiser_id": advertiser_id},
            )
            await database.execute(
                "UPDATE advertiser_reviews SET website_analysis = :analysis, review_status = 'pending' WHERE advertiser_id = :advertiser_id",
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
        "SELECT id, website_url FROM advertisers WHERE id = :advertiser_id",
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
    """
    advertiser = await database.fetch_one(
        "SELECT id, approval_status FROM advertisers WHERE id = :advertiser_id",
        {"advertiser_id": advertiser_id},
    )
    if not advertiser:
        raise HTTPException(status_code=404, detail="Advertiser not found")

    review = await database.fetch_one(
        "SELECT review_status, website_analysis FROM advertiser_reviews WHERE advertiser_id = :advertiser_id",
        {"advertiser_id": advertiser_id},
    )

    keywords_count = await database.fetch_val(
        "SELECT COUNT(*) FROM advertiser_keywords WHERE advertiser_id = :advertiser_id AND source = 'ai_suggested'",
        {"advertiser_id": advertiser_id},
    )

    categories_count = await database.fetch_val(
        "SELECT COUNT(*) FROM advertiser_categories WHERE advertiser_id = :advertiser_id AND source = 'ai_suggested'",
        {"advertiser_id": advertiser_id},
    )

    return {
        "advertiser_id": advertiser_id,
        "approval_status": advertiser["approval_status"],
        "review_status": review["review_status"] if review else None,
        "website_analysis": review["website_analysis"] if review else None,
        "ai_suggested_keywords": keywords_count or 0,
        "ai_suggested_categories": categories_count or 0,
    }
