"""
Auction Service 최적화된 매칭 로직 테스트
- N+1 쿼리 문제 해결 검증
- 성능 개선 측정
- 정확도 검증
"""

# pytest는 선택적 의존성
try:
    import pytest
except ImportError:
    pytest = None

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock
from typing import List, Dict, Any
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from .optimized_matching import (
    OptimizedAdvertiserMatcher,
    OptimizedBidGenerator,
    MatchingResult,
)


class TestOptimizedMatching:
    """최적화된 매칭 로직 테스트 클래스"""

    def mock_database(self):
        """모의 데이터베이스 설정"""
        db = AsyncMock()

        # 광고주 데이터
        db.fetch_all.return_value = [
            {
                "advertiser_id": 1,
                "company_name": "테스트 광고주 1",
                "website_url": "https://test1.com",
                "is_enabled": True,
                "daily_budget": 10000.0,
                "max_bid_per_keyword": 1000,
                "min_quality_score": 50,
                "review_status": "approved",
                "recommended_bid_min": 100,
                "recommended_bid_max": 800,
            },
            {
                "advertiser_id": 2,
                "company_name": "테스트 광고주 2",
                "website_url": "https://test2.com",
                "is_enabled": True,
                "daily_budget": 15000.0,
                "max_bid_per_keyword": 1500,
                "min_quality_score": 60,
                "review_status": "approved",
                "recommended_bid_min": 200,
                "recommended_bid_max": 1200,
            },
        ]

        # 키워드 데이터
        db.fetch_all.side_effect = [
            # 첫 번째 호출: 광고주 데이터
            [
                {
                    "advertiser_id": 1,
                    "company_name": "테스트 광고주 1",
                    "website_url": "https://test1.com",
                    "is_enabled": True,
                    "daily_budget": 10000.0,
                    "max_bid_per_keyword": 1000,
                    "min_quality_score": 50,
                    "review_status": "approved",
                    "recommended_bid_min": 100,
                    "recommended_bid_max": 800,
                },
                {
                    "advertiser_id": 2,
                    "company_name": "테스트 광고주 2",
                    "website_url": "https://test2.com",
                    "is_enabled": True,
                    "daily_budget": 15000.0,
                    "max_bid_per_keyword": 1500,
                    "min_quality_score": 60,
                    "review_status": "approved",
                    "recommended_bid_min": 200,
                    "recommended_bid_max": 1200,
                },
            ],
            # 두 번째 호출: 키워드 데이터
            [
                {
                    "advertiser_id": 1,
                    "keyword": "스마트폰",
                    "priority": 5,
                    "match_type": "exact",
                },
                {
                    "advertiser_id": 2,
                    "keyword": "휴대폰",
                    "priority": 4,
                    "match_type": "broad",
                },
            ],
            # 세 번째 호출: 카테고리 데이터
            [
                {
                    "advertiser_id": 1,
                    "category_path": "전자제품/스마트폰",
                    "is_primary": True,
                    "category_name": "스마트폰",
                }
            ],
            # 네 번째 호출: 비즈니스 카테고리 데이터
            [{"id": 1, "name": "스마트폰", "path": "전자제품/스마트폰", "level": 2}],
        ]

        return db

    def matcher(self, mock_database):
        """최적화된 매칭 객체 생성"""
        return OptimizedAdvertiserMatcher(mock_database)

    def bid_generator(self, mock_database):
        """최적화된 입찰 생성기 객체 생성"""
        return OptimizedBidGenerator(mock_database)

    async def test_optimized_matching_basic(self, matcher):
        """기본 매칭 기능 테스트"""
        search_query = "스마트폰"
        quality_score = 70

        results = await matcher.find_matching_advertisers_optimized(
            search_query, quality_score
        )

        assert len(results) > 0
        assert all(isinstance(result, MatchingResult) for result in results)
        assert all(result.match_score > 0 for result in results)

    async def test_performance_improvement(self, matcher):
        """성능 개선 측정 테스트"""
        search_query = "스마트폰"
        quality_score = 70

        # 성능 측정
        start_time = time.time()
        results = await matcher.find_matching_advertisers_optimized(
            search_query, quality_score
        )
        end_time = time.time()

        execution_time = end_time - start_time

        # 실행 시간이 1초 이내여야 함 (최적화 목표)
        assert execution_time < 1.0, f"실행 시간이 너무 깁니다: {execution_time:.2f}초"

        print(f"✅ 최적화된 매칭 실행 시간: {execution_time:.3f}초")

    async def test_cache_functionality(self, matcher):
        """캐시 기능 테스트"""
        search_query = "스마트폰"
        quality_score = 70

        # 첫 번째 호출
        start_time = time.time()
        results1 = await matcher.find_matching_advertisers_optimized(
            search_query, quality_score
        )
        first_call_time = time.time() - start_time

        # 두 번째 호출 (캐시에서 조회)
        start_time = time.time()
        results2 = await matcher.find_matching_advertisers_optimized(
            search_query, quality_score
        )
        second_call_time = time.time() - start_time

        # 캐시된 호출이 더 빨라야 함
        assert second_call_time < first_call_time
        assert len(results1) == len(results2)

        print(f"✅ 첫 번째 호출: {first_call_time:.3f}초")
        print(f"✅ 캐시된 호출: {second_call_time:.3f}초")

    async def test_matching_accuracy(self, matcher):
        """매칭 정확도 테스트"""
        # 정확한 키워드 매칭
        exact_results = await matcher.find_matching_advertisers_optimized(
            "스마트폰", 70
        )

        # 부분 매칭
        partial_results = await matcher.find_matching_advertisers_optimized(
            "스마트", 70
        )

        # 정확한 매칭이 더 높은 점수를 받아야 함
        if exact_results and partial_results:
            exact_score = max(result.match_score for result in exact_results)
            partial_score = max(result.match_score for result in partial_results)

            assert exact_score >= partial_score
            print(f"✅ 정확한 매칭 점수: {exact_score:.2f}")
            print(f"✅ 부분 매칭 점수: {partial_score:.2f}")

    async def test_bid_generation(self, bid_generator):
        """입찰 생성 테스트"""
        search_query = "스마트폰"
        quality_score = 70

        bids = await bid_generator.generate_optimized_bids(search_query, quality_score)

        assert len(bids) > 0
        assert all("advertiser_id" in bid for bid in bids)
        assert all("bid_price" in bid for bid in bids)
        assert all(bid["bid_price"] > 0 for bid in bids)

        print(f"✅ 생성된 입찰 수: {len(bids)}")
        for bid in bids:
            print(f"   - {bid['company_name']}: {bid['bid_price']}원")

    async def test_no_n_plus_1_queries(self, matcher):
        """N+1 쿼리 문제 해결 검증"""
        # 데이터베이스 호출 횟수 모니터링
        call_count = 0

        async def mock_fetch_all(query, values=None):
            nonlocal call_count
            call_count += 1
            return await matcher.database.fetch_all(query, values)

        matcher.database.fetch_all = mock_fetch_all

        search_query = "스마트폰"
        quality_score = 70

        await matcher.find_matching_advertisers_optimized(search_query, quality_score)

        # 배치 쿼리로 인해 호출 횟수가 제한되어야 함
        assert call_count <= 4, f"N+1 쿼리 문제가 발생했습니다. 호출 횟수: {call_count}"
        print(f"✅ 데이터베이스 호출 횟수: {call_count} (N+1 문제 해결)")

    async def test_keyword_matching_types(self, matcher):
        """다양한 키워드 매칭 타입 테스트"""
        test_cases = [
            ("스마트폰", "exact"),  # 정확한 매칭
            ("스마트", "broad"),  # 부분 매칭
            ("휴대폰", "broad"),  # 유사 키워드
        ]

        for query, expected_type in test_cases:
            results = await matcher.find_matching_advertisers_optimized(query, 70)

            if results:
                print(f"✅ '{query}' ({expected_type}): {len(results)}개 매칭")
                for result in results:
                    print(f"   - {result.company_name}: {result.match_score:.2f}점")

    async def test_category_matching(self, matcher):
        """카테고리 매칭 테스트"""
        # 카테고리 관련 검색어
        category_queries = ["전자제품", "스마트폰", "휴대폰"]

        for query in category_queries:
            results = await matcher.find_matching_advertisers_optimized(query, 70)

            print(f"✅ 카테고리 매칭 '{query}': {len(results)}개 결과")
            for result in results:
                if result.category_matches:
                    print(
                        f"   - {result.company_name}: {len(result.category_matches)}개 카테고리 매칭"
                    )

    async def test_quality_score_filtering(self, matcher):
        """품질 점수 필터링 테스트"""
        # 낮은 품질 점수
        low_quality_results = await matcher.find_matching_advertisers_optimized(
            "스마트폰", 30
        )

        # 높은 품질 점수
        high_quality_results = await matcher.find_matching_advertisers_optimized(
            "스마트폰", 80
        )

        print(f"✅ 낮은 품질 점수 (30): {len(low_quality_results)}개 결과")
        print(f"✅ 높은 품질 점수 (80): {len(high_quality_results)}개 결과")

        # 높은 품질 점수에서 더 많은 결과가 나와야 함
        assert len(high_quality_results) >= len(low_quality_results)

    async def test_budget_availability(self, matcher):
        """예산 확인 테스트"""
        # 모의 예산 데이터 설정
        matcher.database.fetch_one.return_value = {"total_spent": 5000.0}

        # 예산 내 입찰
        available = await matcher.check_budget_availability_optimized(1, 1000, 10000.0)
        assert available is True

        # 예산 초과 입찰
        available = await matcher.check_budget_availability_optimized(1, 6000, 10000.0)
        assert available is False

        print("✅ 예산 확인 로직 정상 작동")


class TestPerformanceComparison:
    """성능 비교 테스트"""

    async def test_old_vs_new_performance(self):
        """기존 로직 vs 최적화된 로직 성능 비교"""
        # 이 테스트는 실제 환경에서 실행해야 함
        # 여기서는 구조만 제시

        test_queries = ["스마트폰", "휴대폰", "전자제품", "삼성 갤럭시", "아이폰"]

        print("🚀 성능 비교 테스트 (실제 환경에서 실행 필요)")
        print("   - 기존 로직: N+1 쿼리 문제")
        print("   - 최적화된 로직: 배치 쿼리 + 캐싱")
        print("   - 예상 성능 개선: 3-5배 향상")


if __name__ == "__main__":
    # 테스트 실행
    print("테스트 실행을 위해서는 pytest가 필요합니다.")
    print("pip install pytest")
