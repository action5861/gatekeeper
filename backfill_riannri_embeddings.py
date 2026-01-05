"""
리앤리성형외과 키워드 임베딩 일괄 생성 스크립트

사용법:
    docker exec -it website-analysis-service python /app/backfill_riannri_embeddings.py

또는 로컬에서:
    cd services/website-analysis-service
    python ../../backfill_riannri_embeddings.py
"""

import asyncio
import os
import sys
from typing import List, Optional

# 상위 디렉토리 import를 위한 경로 추가
script_path = os.path.abspath(__file__)
script_dir = os.path.dirname(script_path)

# 여러 경로 시도
possible_paths = [
    "/app",  # Docker 환경
    os.path.join(
        script_dir, "services", "website-analysis-service"
    ),  # 프로젝트 루트에서 실행
    os.path.dirname(
        os.path.dirname(script_dir)
    ),  # services/website-analysis-service 안에서 실행
    script_dir,  # 현재 디렉토리
]

for path in possible_paths:
    if os.path.exists(path) and os.path.exists(os.path.join(path, "database.py")):
        if path not in sys.path:
            sys.path.insert(0, path)
        break

try:
    from database import database, connect_to_database, disconnect_from_database
except ImportError as e:
    print(f"❌ database 모듈을 찾을 수 없습니다.")
    print(f"   시도한 경로: {possible_paths}")
    print(f"   현재 작업 디렉토리: {os.getcwd()}")
    print(f"   스크립트 경로: {script_path}")
    sys.exit(1)

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
BATCH_SIZE = int(os.getenv("BACKFILL_BATCH_SIZE", "10"))

if not API_KEY:
    print("❌ GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
    sys.exit(1)

genai.configure(api_key=API_KEY)


def get_embedding(text: str, retry_count: int = 3) -> Optional[List[float]]:
    """텍스트에 대한 임베딩 벡터를 생성합니다. 재시도 로직 포함."""
    clean = (text or "").strip()
    if not clean:
        return None

    for attempt in range(retry_count):
        try:
            res = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=clean,
                task_type="retrieval_document",
            )

            # 응답 파싱 - 다양한 응답 형식 처리
            embedding: Optional[List[float]] = None

            # dict 형태 응답
            if isinstance(res, dict):
                emb = res.get("embedding")
                if isinstance(emb, list) and len(emb) > 0:
                    embedding = emb
                elif isinstance(emb, dict):
                    # dict 안에 "values" 키가 있는 경우
                    if "values" in emb:
                        vals = emb.get("values")
                        if isinstance(vals, list) and len(vals) > 0:
                            embedding = vals
                # res 자체에 "values" 키가 있는 경우
                if embedding is None and "values" in res:
                    vals = res.get("values")
                    if isinstance(vals, list) and len(vals) > 0:
                        embedding = vals

            # 객체 형태 응답 (TypedDict 또는 객체)
            if embedding is None:
                # getattr로 안전하게 접근
                emb_obj = getattr(res, "embedding", None)
                if emb_obj is not None:
                    if isinstance(emb_obj, list) and len(emb_obj) > 0:
                        embedding = emb_obj
                    elif isinstance(emb_obj, dict):
                        # dict인 경우 "values" 키 확인
                        if "values" in emb_obj:
                            vals = emb_obj.get("values")
                            if isinstance(vals, list) and len(vals) > 0:
                                embedding = vals
                    else:
                        # 객체에 values 속성이 있는 경우
                        vals = getattr(emb_obj, "values", None)
                        if isinstance(vals, list) and len(vals) > 0:
                            embedding = vals

            # 최종 검증
            if embedding and isinstance(embedding, list) and len(embedding) > 0:
                # 768차원인지 확인 (text-embedding-004는 768차원)
                if len(embedding) == 768:
                    return embedding
                else:
                    print(f"  ⚠️ 예상치 못한 임베딩 차원: {len(embedding)} (예상: 768)")
                    return embedding  # 차원이 다르더라도 반환

            return None

        except Exception as e:
            if attempt < retry_count - 1:
                wait_time = (attempt + 1) * 2  # 2초, 4초, 6초
                print(f"  ⚠️ 임베딩 생성 실패 (시도 {attempt + 1}/{retry_count}): {e}")
                print(f"  ⏳ {wait_time}초 후 재시도...")
                import time

                time.sleep(wait_time)
            else:
                print(f"  ❌ 임베딩 생성 최종 실패: {e}")
                return None

    return None


async def backfill_riannri_embeddings():
    """리앤리성형외과의 임베딩이 없는 키워드에 임베딩을 생성합니다."""
    print("🚀 리앤리성형외과 키워드 임베딩 일괄 생성 시작")
    print(f"📊 설정: BATCH_SIZE={BATCH_SIZE}, MODEL={EMBEDDING_MODEL}")
    print(f"📊 API_KEY 설정: {'✅' if API_KEY else '❌'}")
    print("-" * 50)

    # 데이터베이스 연결
    try:
        await connect_to_database()
        print("✅ 데이터베이스 연결 성공")
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        sys.exit(1)

    try:
        # 1) 리앤리성형외과 광고주 찾기
        advertiser_query = """
            SELECT id, company_name, username
            FROM advertisers
            WHERE company_name LIKE '%리앤리%' 
               OR company_name LIKE '%성형외과%'
               OR username LIKE '%리앤리%'
            ORDER BY id
        """
        advertisers = await database.fetch_all(advertiser_query)

        if not advertisers:
            print("❌ 리앤리성형외과 광고주를 찾을 수 없습니다.")
            return

        print(f"📋 찾은 광고주: {len(advertisers)}개")
        for adv in advertisers:
            print(
                f"   - ID: {adv['id']}, 회사명: {adv['company_name']}, 사용자명: {adv['username']}"
            )

        # 2) 각 광고주의 임베딩이 없는 키워드 조회
        all_keywords = []
        for adv in advertisers:
            keywords_query = """
                SELECT id, advertiser_id, keyword
                FROM advertiser_keywords
                WHERE advertiser_id = :advertiser_id
                  AND embedding IS NULL
                ORDER BY id
            """
            keywords = await database.fetch_all(
                keywords_query, {"advertiser_id": adv["id"]}
            )
            all_keywords.extend(keywords)
            print(f"   광고주#{adv['id']}: 임베딩 없는 키워드 {len(keywords)}개")

        total = len(all_keywords)
        print(f"\n📋 총 임베딩이 없는 키워드: {total}개")

        if total == 0:
            print("✅ 모든 키워드에 이미 임베딩이 있습니다.")
            return

        # 3) 배치 처리
        success_count = 0
        fail_count = 0

        for i, row in enumerate(all_keywords):
            keyword_id = row["id"]
            advertiser_id = row["advertiser_id"]
            keyword = row["keyword"]

            print(f"[{i+1}/{total}] 광고주#{advertiser_id} '{keyword}' 처리 중...")

            # 임베딩 생성
            embedding = get_embedding(keyword)

            if embedding and len(embedding) > 0:
                try:
                    # DB 업데이트
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
                except Exception as db_error:
                    fail_count += 1
                    print(f"  ❌ DB 저장 실패: {db_error}")
            else:
                fail_count += 1
                print(f"  ❌ 임베딩 생성 실패 (결과 없음)")

            # API 레이트리밋 방지 (배치마다 잠시 대기)
            if (i + 1) % BATCH_SIZE == 0:
                print(f"  ⏳ 레이트리밋 방지 대기 (1초)...")
                await asyncio.sleep(1)

        # 4) 결과 요약
        print("-" * 50)
        print(f"🎉 일괄 임베딩 생성 완료!")
        print(f"   ✅ 성공: {success_count}개")
        print(f"   ❌ 실패: {fail_count}개")
        if total > 0:
            print(f"   📊 성공률: {success_count/total*100:.1f}%")

        # 5) 최종 상태 확인
        print("\n📊 최종 상태:")
        for adv in advertisers:
            final_query = """
                SELECT 
                    COUNT(*) as total,
                    COUNT(embedding) as with_embedding
                FROM advertiser_keywords
                WHERE advertiser_id = :advertiser_id
            """
            stats = await database.fetch_one(final_query, {"advertiser_id": adv["id"]})
            if stats:
                total_kw = stats["total"]
                with_emb = stats["with_embedding"]
                pct = (with_emb / total_kw * 100) if total_kw > 0 else 0
                print(
                    f"   광고주#{adv['id']} ({adv['company_name']}): {with_emb}/{total_kw}개 ({pct:.1f}%)"
                )

    finally:
        await disconnect_from_database()


if __name__ == "__main__":
    asyncio.run(backfill_riannri_embeddings())
