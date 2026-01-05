import asyncio
import os
import sys
from pathlib import Path
from typing import List

# Ensure project root (/app) is on sys.path when running from /app/scripts
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from database import connect_to_database, disconnect_from_database, database
from main import get_text_embedding


async def backfill_embeddings(advertiser_id: int | None = None) -> None:
    """
    임베딩이 비어 있는 키워드에 대해 Gemini 임베딩을 생성하고 저장합니다.

    - DATABASE_URL 환경변수를 사용해 DB에 연결 (database 모듈 재사용)
    - keywords 테이블에서 embedding 이 NULL 인 레코드를 조회
    - main.get_text_embedding 을 사용해 임베딩 생성
    - 생성된 벡터를 embedding 컬럼에 업데이트
    """
    await connect_to_database()

    try:
        params: dict = {}
        # advertiser_keywords 테이블 기준으로 누락된 embedding을 복구한다.
        where_clause = "embedding IS NULL"
        if advertiser_id is not None:
            where_clause += " AND advertiser_id = :advertiser_id"
            params["advertiser_id"] = advertiser_id

        rows = await database.fetch_all(
            f"""
            SELECT id, advertiser_id, keyword
            FROM advertiser_keywords
            WHERE {where_clause}
            ORDER BY id
            """,
            params,
        )

        total = len(rows)
        target_desc = f" (advertiser_id={advertiser_id})" if advertiser_id else ""
        print(f"🚀 임베딩이 없는 키워드{target_desc}: {total}개")

        if total == 0:
            print("✅ 복구할 키워드가 없습니다.")
            return

        updated = 0
        for idx, row in enumerate(rows, start=1):
            kw_id = row["id"]
            adv_id = row["advertiser_id"]
            text: str = row["keyword"]

            print(f"[{idx}/{total}] 광고주#{adv_id} 키워드 '{text}' 임베딩 생성 중...")

            # main.py 의 비동기 임베딩 함수를 그대로 사용
            vector: List[float] = await get_text_embedding(text)
            if not vector:
                print("  ⚠️ 임베딩 생성 실패, 건너뜀")
                continue

            # pgvector(vector) 타입에 맞게 문자열 형태로 캐스팅해서 전달
            await database.execute(
                """
                UPDATE advertiser_keywords
                SET embedding = CAST(:embedding AS vector)
                WHERE id = :id
                """,
                {"id": kw_id, "embedding": str(vector)},
            )
            updated += 1
            print(f"  ✅ 임베딩 저장 완료 ({len(vector)}차원)")

        print(f"🎉 총 {updated}개의 키워드 임베딩 복구 완료 (전체 {total}개 중)")

    finally:
        await disconnect_from_database()


if __name__ == "__main__":
    # 기본값: 전체 광고주 대상으로 임베딩 복구
    # - BACKFILL_ADVERTISER_ID 가 설정되면 해당 ID만 대상으로 한정
    adv_id_env = os.getenv("BACKFILL_ADVERTISER_ID")
    target_adv_id: int | None
    if adv_id_env:
        try:
            target_adv_id = int(adv_id_env)
        except ValueError:
            target_adv_id = None
    else:
        target_adv_id = None

    asyncio.run(backfill_embeddings(target_adv_id))
