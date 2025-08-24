#!/usr/bin/env python3
"""
대시보드 데이터 테스트 스크립트
사용자 검색, 품질 점수, 제출 현황 등이 제대로 저장되고 조회되는지 확인
"""

import asyncio
import asyncpg
import os
from datetime import datetime, timedelta

# 데이터베이스 연결 설정
DATABASE_URL = (
    "postgresql://admin:your_secure_password_123@localhost:5433/search_exchange_db"
)


async def test_dashboard_data():
    """대시보드 데이터 테스트"""
    try:
        # 데이터베이스 연결
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ 데이터베이스 연결 성공")

        # 1. 사용자 데이터 확인
        print("\n🔍 1. 사용자 데이터 확인")
        users = await conn.fetch(
            "SELECT id, username, email, total_earnings, quality_score, submission_count FROM users"
        )
        for user in users:
            print(f"   사용자 {user['id']}: {user['username']} ({user['email']})")
            print(f"   - 총 수익: {user['total_earnings']}원")
            print(f"   - 품질 점수: {user['quality_score']}")
            print(f"   - 제출 횟수: {user['submission_count']}")

        # 2. 검색 쿼리 데이터 확인
        print("\n🔍 2. 검색 쿼리 데이터 확인")
        search_queries = await conn.fetch(
            """
            SELECT user_id, query_text, quality_score, commercial_value, created_at 
            FROM search_queries 
            ORDER BY created_at DESC 
            LIMIT 10
        """
        )
        print(f"   총 검색 쿼리 수: {len(search_queries)}")
        for query in search_queries:
            print(
                f"   - 사용자 {query['user_id']}: '{query['query_text']}' (품질: {query['quality_score']})"
            )

        # 3. 품질 이력 데이터 확인
        print("\n🔍 3. 품질 이력 데이터 확인")
        quality_history = await conn.fetch(
            """
            SELECT user_id, week_label, quality_score, recorded_at 
            FROM user_quality_history 
            ORDER BY user_id, recorded_at DESC
        """
        )
        print(f"   총 품질 이력 수: {len(quality_history)}")
        for history in quality_history:
            print(
                f"   - 사용자 {history['user_id']}: {history['week_label']} (품질: {history['quality_score']})"
            )

        # 4. 일일 제출 현황 확인
        print("\n🔍 4. 일일 제출 현황 확인")
        daily_submissions = await conn.fetch(
            """
            SELECT user_id, submission_date, submission_count, quality_score_avg 
            FROM daily_submissions 
            ORDER BY submission_date DESC, user_id
        """
        )
        print(f"   총 일일 제출 기록 수: {len(daily_submissions)}")
        for submission in daily_submissions:
            print(
                f"   - 사용자 {submission['user_id']}: {submission['submission_date']} (제출: {submission['submission_count']}, 평균 품질: {submission['quality_score_avg']})"
            )

        # 5. 경매 상태 확인
        print("\n🔍 5. 경매 상태 확인")
        auctions = await conn.fetch(
            """
            SELECT user_id, search_id, query_text, status, created_at 
            FROM auctions 
            ORDER BY created_at DESC
        """
        )
        print(f"   총 경매 수: {len(auctions)}")
        completed_count = sum(
            1 for auction in auctions if auction["status"] == "completed"
        )
        print(f"   - 완료된 경매: {completed_count}개")
        for auction in auctions:
            print(
                f"   - 사용자 {auction['user_id']}: '{auction['query_text']}' (상태: {auction['status']})"
            )

        # 6. 거래 내역 확인
        print("\n🔍 6. 거래 내역 확인")
        transactions = await conn.fetch(
            """
            SELECT user_id, query_text, buyer_name, primary_reward, secondary_reward, status 
            FROM transactions 
            ORDER BY created_at DESC
        """
        )
        print(f"   총 거래 수: {len(transactions)}")
        total_earnings = sum(t["primary_reward"] or 0 for t in transactions)
        print(f"   - 총 1차 보상: {total_earnings}원")
        for transaction in transactions:
            print(
                f"   - 사용자 {transaction['user_id']}: '{transaction['query_text']}' -> {transaction['buyer_name']} ({transaction['primary_reward']}원)"
            )

        # 7. 대시보드 통계 계산 테스트
        print("\n🔍 7. 대시보드 통계 계산 테스트")
        for user_id in [1, 2]:  # 테스트 사용자들
            print(f"\n   사용자 {user_id} 통계:")

            # 월간 검색 횟수
            monthly_searches = await conn.fetchval(
                """
                SELECT COUNT(*) 
                FROM search_queries 
                WHERE user_id = $1 
                AND created_at >= date_trunc('month', CURRENT_DATE)
            """,
                user_id,
            )
            print(f"   - 이번달 검색 횟수: {monthly_searches}")

            # 성공률
            auction_stats = await conn.fetchrow(
                """
                SELECT 
                    COUNT(*) as total_auctions,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_auctions
                FROM auctions 
                WHERE user_id = $1
            """,
                user_id,
            )
            if auction_stats and auction_stats["total_auctions"] > 0:
                success_rate = (
                    auction_stats["completed_auctions"]
                    / auction_stats["total_auctions"]
                ) * 100
                print(f"   - 경매 성공률: {success_rate:.1f}%")
            else:
                print(f"   - 경매 성공률: 0%")

            # 평균 품질 점수
            avg_quality = await conn.fetchval(
                """
                SELECT AVG(quality_score) 
                FROM search_queries 
                WHERE user_id = $1
            """,
                user_id,
            )
            print(
                f"   - 평균 품질 점수: {avg_quality:.1f}"
                if avg_quality
                else "   - 평균 품질 점수: 0"
            )

        await conn.close()
        print("\n✅ 테스트 완료")

    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_dashboard_data())
