# pyright: reportAttributeAccessIssue=false
"""
표준 카테고리 마이그레이션 스크립트 (async + databases + Gemini 분류)

실행 (컨테이너 내부):
    docker-compose exec advertiser-service python scripts/migrate_categories_to_standard.py

기능:
- advertisers 테이블의 모든 광고주를 조회
- 각 광고주에 대해 Gemini API를 호출하여 표준 14개 카테고리 중 가장 적합한 하나를 선택
- advertisers.category 컬럼을 해당 표준 카테고리로 UPDATE
"""

import sys
import os
import asyncio
import logging
from typing import List, Optional


def _register_database_path() -> None:
    """database.py 파일이 있는 디렉토리를 찾아 sys.path에 추가한다.

    1) 현재 파일 기준 상위 디렉토리를 최대 3단계까지 탐색
    2) 실패 시 /app, /app/services/advertiser-service, 현재 작업 디렉터리에서 탐색
    """

    # 1. 현재 파일 기준 상위 디렉토리 탐색
    current_path = os.path.abspath(__file__)
    for _ in range(3):
        current_path = os.path.dirname(current_path)
        candidate = os.path.join(current_path, "database.py")
        if os.path.exists(candidate):
            if current_path not in sys.path:
                sys.path.insert(0, current_path)
            print(f"✅ Found database.py at: {current_path}")
            return

    # 2. 일반적인 루트 경로들 탐색
    search_roots = ["/app", "/app/services/advertiser-service", os.getcwd()]
    for root in search_roots:
        candidate = os.path.join(root, "database.py")
        if os.path.exists(root) and os.path.exists(candidate):
            if root not in sys.path:
                sys.path.insert(0, root)
            print(f"✅ Found database.py at search root: {root}")
            return

    print("⚠️ Warning: database.py not found in common paths.")


# 경로 등록 실행 (database 모듈 import 전에 반드시 호출)
_register_database_path()

# 이제 database 모듈 import (동기/비동기 모두 사용 가능)
from database import (  # type: ignore
    database,
    connect_to_database,
    disconnect_from_database,
)

try:
    from google import generativeai as genai  # type: ignore
except ImportError:
    genai = None  # type: ignore[assignment]


logger = logging.getLogger("category-migration")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


# 표준 카테고리 목록 (14개)
STANDARD_CATEGORIES: List[str] = [
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


def _configure_gemini() -> None:
    """GEMINI_API_KEY 또는 GOOGLE_API_KEY를 사용해 Gemini SDK를 설정합니다."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Gemini API 키(GEMINI_API_KEY/GOOGLE_API_KEY)가 설정되지 않았습니다."
        )

    if not genai:
        raise RuntimeError("google-generativeai 패키지가 설치되어 있지 않습니다.")

    try:
        genai.configure(api_key=api_key)  # type: ignore[attr-defined]
        logger.info("✅ Gemini API configured for category migration.")
    except Exception as exc:  # pragma: no cover - 방어적 로깅
        logger.error("Gemini 설정 실패: %s", exc, exc_info=True)
        raise


def _build_prompt(company_name: str, existing_category: str) -> str:
    """광고주 정보를 기반으로 표준 카테고리 분류를 요청하는 프롬프트를 생성합니다."""
    existing_txt = existing_category if existing_category else "없음"
    std_list = ", ".join(STANDARD_CATEGORIES)

    return f"""
You are a strict business category classifier for search ads.

Your task:
- Read the advertiser info (company name and existing category).
- THEN choose exactly ONE best-matching category from the following STANDARD_CATEGORIES (in Korean):
  [{std_list}]

Rules:
- You MUST answer with EXACTLY ONE of the STANDARD_CATEGORIES.
- Do NOT invent new category names.
- If the advertiser is a charity, NGO, donation, international aid, or similar non-profit organization,
  choose "비영리/공공".
- If the advertiser is an eyewear shop, optician, eye clinic, or sells glasses/contact lenses,
  choose between "의료/건강" and "패션/뷰티" and pick the more appropriate one.
- If the advertiser is clearly an online supplement/health store like vitamins, health foods, etc.,
  choose "생활/건강".

Advertiser Info (Korean):
- 회사명(company_name): "{company_name}"
- 기존 카테고리(existing_category): "{existing_txt}"

Output format:
- Respond with ONLY ONE WORD, EXACTLY one of:
  {std_list}
- No explanations. No extra words. Just the category.
"""


def _classify_category_sync(company_name: str, existing_category: str) -> Optional[str]:
    """동기 Gemini 호출을 통해 표준 카테고리 하나를 결정합니다.

    - 예외 발생 시 None 반환 (상위 async 코드에서 안전하게 건너뜀)
    """
    if not genai:
        return None

    prompt = _build_prompt(company_name, existing_category)

    try:
        model_name = os.getenv("GEMINI_MODEL", "models/gemini-flash-latest")
        model = genai.GenerativeModel(model_name)  # type: ignore[attr-defined]
        res = model.generate_content(prompt)
        text = (getattr(res, "text", "") or "").strip()
        if not text:
            return None

        # 첫 줄만 사용, 양쪽 공백/따옴표 제거
        first = text.splitlines()[0].strip().strip('"').strip("'")

        # 표준 카테고리와 정확히 일치하는지 확인
        for cat in STANDARD_CATEGORIES:
            if first == cat:
                return cat

        # 혹시 모델이 "카테고리: XXX" 형태로 답한 경우를 방어적으로 처리
        cleaned = first.replace("카테고리", "").replace(":", "").strip()
        for cat in STANDARD_CATEGORIES:
            if cleaned == cat:
                return cat

        logger.warning(
            "⚠️ Gemini가 표준 카테고리에 맞지 않는 값을 반환했습니다: '%s' (company='%s')",
            first,
            company_name,
        )
        return None
    except Exception as exc:  # pragma: no cover - 외부 API 예외 방어
        logger.error("❌ Gemini 카테고리 분류 중 오류: %s", exc, exc_info=True)
        return None


async def migrate_categories() -> None:
    """advertisers.category를 표준 14개 카테고리로 정규화하는 일회성 마이그레이션."""
    await connect_to_database()

    try:
        _configure_gemini()
    except RuntimeError as exc:
        logger.error("Gemini 설정 오류로 인해 마이그레이션을 종료합니다: %s", exc)
        await disconnect_from_database()
        return

    try:
        # advertisers 테이블에 category 컬럼이 없을 수 있으므로, 없으면 생성
        try:
            await database.execute(
                """
                ALTER TABLE advertisers
                ADD COLUMN IF NOT EXISTS category TEXT
                """
            )
            logger.info("✅ advertisers 테이블에 category 컬럼을 확인/생성했습니다.")
        except Exception as exc:
            logger.error(
                "❌ advertisers.category 컬럼 생성/확인 중 오류: %s", exc, exc_info=True
            )
            # 컬럼이 없으면 이후 UPDATE 에서 다시 오류가 날 것이므로 조기에 종료
            raise

        # 모든 광고주 조회 (기존 category 컬럼은 사용하지 않고 회사명 기준으로 분류)
        rows = await database.fetch_all(
            """
            SELECT id, company_name
            FROM advertisers
            ORDER BY id
            """
        )

        logger.info(
            "총 %d명의 광고주에 대해 카테고리 마이그레이션을 시작합니다.", len(rows)
        )

        updated = 0
        for idx, row in enumerate(rows, start=1):
            adv_id = int(row["id"])  # type: ignore[index]
            company_name = str(row["company_name"])  # type: ignore[index]
            existing_category = ""  # 기존 category 텍스트는 사용하지 않음

            logger.info(
                "[%d/%d] 광고주#%d '%s' 분류 시작",
                idx,
                len(rows),
                adv_id,
                company_name,
            )

            # 동기 Gemini 호출을 별도 스레드에서 실행
            std_cat = await asyncio.to_thread(
                _classify_category_sync, company_name, existing_category
            )

            if not std_cat:
                logger.warning(
                    "⚠️ 광고주#%d '%s'에 대해 카테고리 분류 실패, 건너뜀",
                    adv_id,
                    company_name,
                )
                continue

            logger.info(
                "✅ 광고주#%d '%s' → 표준 카테고리: '%s'",
                adv_id,
                company_name,
                std_cat,
            )

            # advertisers.category 컬럼을 표준 카테고리로 업데이트
            try:
                await database.execute(
                    """
                    UPDATE advertisers
                    SET category = :category
                    WHERE id = :id
                    """,
                    {"category": std_cat, "id": adv_id},
                )
                updated += 1
            except Exception as exc:  # 개별 광고주 업데이트 실패 시 계속 진행
                logger.error(
                    "❌ 광고주#%d '%s' 카테고리 업데이트 중 오류: %s",
                    adv_id,
                    company_name,
                    exc,
                    exc_info=True,
                )
                continue

        logger.info(
            "🎉 표준 카테고리로 마이그레이션 완료: %d명의 광고주 category 컬럼 업데이트",
            updated,
        )

    finally:
        await disconnect_from_database()


if __name__ == "__main__":
    asyncio.run(migrate_categories())
