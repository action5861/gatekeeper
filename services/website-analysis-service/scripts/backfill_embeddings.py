"""
기존 광고주 키워드에 임베딩을 일괄 생성하는 스크립트

사용법:
    docker exec -it website-analysis-service python scripts/backfill_embeddings.py

또는 로컬에서:
    cd services/website-analysis-service
    python scripts/backfill_embeddings.py
"""

import asyncio
import os
import sys
from typing import Any, List, cast

# 상위 디렉토리 import를 위한 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import database, connect_to_database, disconnect_from_database

# Gemini SDK
try:
    from google import generativeai as genai
except ImportError:
    print("❌ google-generativeai 패키지가 설치되지 않았습니다.")
    print("   pip install google-generativeai")
    sys.exit(1)

# 환경 변수
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/text-embedding-004")
BATCH_SIZE = int(os.getenv("BACKFILL_BATCH_SIZE", "10"))  # 한 번에 처리할 키워드 수

if not API_KEY:
    print("❌ GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
    sys.exit(1)

genai.configure(api_key=API_KEY)


def get_embedding(text: str) -> List[float]:
    """텍스트에 대한 임베딩 벡터를 생성합니다."""
    clean = (text or "").strip()
    if not clean:
        return []

    try:
        res = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=clean,
            task_type="retrieval_document",  # DB 저장용
        )

        # 응답 파싱
        if isinstance(res, dict):
            emb = res.get("embedding")
            if isinstance(emb, list):
                return emb
            elif isinstance(emb, dict) and "values" in emb:
                return emb["values"]

        return []
    except Exception as e:
        print(f"  ⚠️ 임베딩 생성 실패: {e}")
        return []


async def backfill_embeddings():
    """임베딩이 없는 키워드에 일괄 임베딩을 생성합니다."""
    print("🚀 기존 키워드 임베딩 일괄 생성 시작")
    print(f"📊 설정: BATCH_SIZE={BATCH_SIZE}, MODEL={EMBEDDING_MODEL}")
    print("-" * 50)

    await connect_to_database()

    try:
        # 1) 임베딩이 없는 키워드 조회
        query = """
            SELECT id, advertiser_id, keyword
            FROM advertiser_keywords
            WHERE embedding IS NULL
            ORDER BY id
        """
        rows = await database.fetch_all(query)

        total = len(rows)
        print(f"📋 임베딩이 없는 키워드: {total}개")

        if total == 0:
            print("✅ 모든 키워드에 이미 임베딩이 있습니다.")
            return

        # 2) 배치 처리
        success_count = 0
        fail_count = 0

        for i, row in enumerate(rows):
            keyword_id = row["id"]
            advertiser_id = row["advertiser_id"]
            keyword = row["keyword"]

            print(f"[{i+1}/{total}] 광고주#{advertiser_id} '{keyword}' 처리 중...")

            # 임베딩 생성
            embedding = get_embedding(keyword)

            if embedding:
                # DB 업데이트 (CAST 문법 사용 - databases 라이브러리 호환)
                await database.execute(
                    """
                    UPDATE advertiser_keywords
                    SET embedding = CAST(:embedding AS vector)
                    WHERE id = :id
                    """,
                    {"id": keyword_id, "embedding": str(embedding)},
                )
                success_count += 1
                print(f"  ✅ 임베딩 저장 완료 ({len(embedding)}차원)")
            else:
                fail_count += 1
                print(f"  ❌ 임베딩 생성 실패")

            # API 레이트리밋 방지 (배치마다 잠시 대기)
            if (i + 1) % BATCH_SIZE == 0:
                print(f"  ⏳ 레이트리밋 방지 대기 (1초)...")
                await asyncio.sleep(1)

        # 3) 결과 요약
        print("-" * 50)
        print(f"🎉 일괄 임베딩 생성 완료!")
        print(f"   ✅ 성공: {success_count}개")
        print(f"   ❌ 실패: {fail_count}개")
        print(f"   📊 성공률: {success_count/total*100:.1f}%")

    finally:
        await disconnect_from_database()


async def check_status():
    """현재 임베딩 상태를 확인합니다."""
    await connect_to_database()

    try:
        # 전체 키워드 수
        total = await database.fetch_val("SELECT COUNT(*) FROM advertiser_keywords")

        # 임베딩이 있는 키워드 수
        with_embedding = await database.fetch_val(
            "SELECT COUNT(*) FROM advertiser_keywords WHERE embedding IS NOT NULL"
        )

        # 임베딩이 없는 키워드 수
        without_embedding = await database.fetch_val(
            "SELECT COUNT(*) FROM advertiser_keywords WHERE embedding IS NULL"
        )

        # 광고주별 현황
        advertiser_stats = await database.fetch_all(
            """
            SELECT 
                ak.advertiser_id,
                a.company_name,
                COUNT(*) as total_keywords,
                COUNT(ak.embedding) as with_embedding
            FROM advertiser_keywords ak
            JOIN advertisers a ON ak.advertiser_id = a.id
            GROUP BY ak.advertiser_id, a.company_name
            ORDER BY ak.advertiser_id
            """
        )

        print("=" * 60)
        print("📊 키워드 임베딩 현황")
        print("=" * 60)
        print(f"전체 키워드: {total}개")
        print(f"  ✅ 임베딩 있음: {with_embedding}개 ({with_embedding/total*100:.1f}%)")
        print(
            f"  ❌ 임베딩 없음: {without_embedding}개 ({without_embedding/total*100:.1f}%)"
        )
        print()
        print("📋 광고주별 현황:")
        print("-" * 60)
        for stat in advertiser_stats:
            name = stat["company_name"] or f"광고주#{stat['advertiser_id']}"
            total_kw = stat["total_keywords"]
            with_emb = stat["with_embedding"]
            pct = (with_emb / total_kw * 100) if total_kw > 0 else 0
            status = "✅" if pct == 100 else ("⚠️" if pct > 0 else "❌")
            print(f"  {status} {name}: {with_emb}/{total_kw}개 ({pct:.0f}%)")
        print("=" * 60)

    finally:
        await disconnect_from_database()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="기존 키워드 임베딩 일괄 생성")
    parser.add_argument("--check", action="store_true", help="현재 상태만 확인")
    args = parser.parse_args()

    if args.check:
        asyncio.run(check_status())
    else:
        asyncio.run(backfill_embeddings())
