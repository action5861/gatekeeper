"""
최적화된 광고 매칭 로직
- N+1 쿼리 문제 해결
- 배치 쿼리로 성능 최적화
- 캐싱 메커니즘 추가
- 정확도 개선 알고리즘
"""

import hashlib
import json
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import asyncio
from dataclasses import dataclass


@dataclass
class MatchingResult:
    """매칭 결과 데이터 클래스"""

    advertiser_id: int
    company_name: str
    match_score: float
    match_reasons: List[str]
    keyword_matches: List[Dict[str, Any]]
    category_matches: List[Dict[str, Any]]
    auto_bid_settings: Optional[Dict[str, Any]] = None
    review_status: Optional[str] = None


class OptimizedAdvertiserMatcher:
    """최적화된 광고주 매칭 클래스"""

    def __init__(self, database):
        self.database = database
        self.cache = {}  # 간단한 메모리 캐시
        self.cache_ttl = 300  # 5분 캐시 TTL

    async def find_matching_advertisers_optimized(
        self, search_query: str, quality_score: int
    ) -> List[MatchingResult]:
        """
        최적화된 광고주 매칭 로직
        - N+1 쿼리 문제 해결
        - 배치 쿼리 사용
        - 캐싱 메커니즘 적용
        """
        print(f"최적화된 매칭 시작: '{search_query}' (품질점수: {quality_score})")

        # 1. 캐시 확인
        cache_key = self._generate_cache_key(search_query, quality_score)
        cached_result = await self._get_from_cache(cache_key)
        if cached_result:
            print("캐시에서 결과 반환")
            return cached_result

        # 2. 검색 토큰 생성
        search_tokens = self._generate_search_tokens(search_query)
        print(f"검색 토큰: {search_tokens}")

        # 3. 배치 쿼리로 모든 데이터 한 번에 조회
        advertisers_data = await self._fetch_advertisers_batch(
            search_tokens, quality_score
        )

        # 4. 매칭 점수 계산
        matching_results = await self._calculate_matching_scores(
            search_tokens, advertisers_data, quality_score
        )

        # 5. 결과 정렬 및 필터링
        final_results = self._filter_and_sort_results(matching_results)

        # 6. 캐시 저장
        await self._save_to_cache(cache_key, final_results)

        print(f"최적화된 매칭 완료: {len(final_results)}개 결과")
        return final_results

    def _generate_search_tokens(self, search_query: str) -> set:
        """검색 쿼리에서 토큰 생성 (한글 최적화)"""
        tokens = set()

        # 1. 전체 검색어
        tokens.add(search_query.lower())

        # 2. 공백으로 분리된 토큰들
        tokens.update(search_query.lower().split())

        # 3. 한글 부분 문자열 (2글자 이상)
        if any(ord(char) > 127 for char in search_query):
            for i in range(len(search_query) - 1):
                for j in range(i + 2, len(search_query) + 1):
                    token = search_query[i:j].lower()
                    if len(token) >= 2:
                        tokens.add(token)

        return tokens

    async def _fetch_advertisers_batch(
        self, search_tokens: set, quality_score: int
    ) -> Dict[str, Any]:
        """배치 쿼리로 모든 필요한 데이터를 한 번에 조회"""

        # 1. 활성화된 광고주와 자동 입찰 설정을 한 번에 조회
        advertisers_query = """
            SELECT 
                a.id as advertiser_id,
                a.company_name,
                a.website_url,
                abs.is_enabled,
                abs.daily_budget,
                abs.max_bid_per_keyword,
                abs.min_quality_score,
                ar.review_status,
                ar.recommended_bid_min,
                ar.recommended_bid_max
            FROM advertisers a
            LEFT JOIN auto_bid_settings abs ON a.id = abs.advertiser_id
            LEFT JOIN advertiser_reviews ar ON a.id = ar.advertiser_id
            WHERE abs.is_enabled = true
        """

        advertisers = await self.database.fetch_all(advertisers_query)

        # 2. 모든 키워드를 한 번에 조회
        keyword_query = """
            SELECT 
                ak.advertiser_id,
                ak.keyword,
                ak.priority,
                ak.match_type
            FROM advertiser_keywords ak
            WHERE ak.keyword = ANY(:tokens)
               OR ak.keyword LIKE ANY(SELECT '%' || token || '%' FROM unnest(:tokens) AS token)
        """

        keywords = await self.database.fetch_all(
            keyword_query, {"tokens": list(search_tokens)}
        )

        # 3. 모든 카테고리를 한 번에 조회
        category_query = """
            SELECT 
                ac.advertiser_id,
                ac.category_path,
                ac.is_primary,
                bc.name as category_name
            FROM advertiser_categories ac
            JOIN business_categories bc ON ac.category_path = bc.path
            WHERE bc.is_active = true
        """

        categories = await self.database.fetch_all(category_query)

        # 4. 비즈니스 카테고리 정보 조회
        business_categories_query = """
            SELECT id, name, path, level
            FROM business_categories
            WHERE is_active = true
        """

        business_categories = await self.database.fetch_all(business_categories_query)

        return {
            "advertisers": advertisers,
            "keywords": keywords,
            "categories": categories,
            "business_categories": business_categories,
        }

    async def _calculate_matching_scores(
        self, search_tokens: set, data: Dict[str, Any], quality_score: int
    ) -> List[MatchingResult]:
        """매칭 점수 계산 (최적화된 알고리즘)"""

        results = []
        advertiser_map = {adv["advertiser_id"]: adv for adv in data["advertisers"]}

        # 키워드 매칭 점수 계산
        keyword_scores = self._calculate_keyword_scores(search_tokens, data["keywords"])

        # 카테고리 매칭 점수 계산
        category_scores = self._calculate_category_scores(
            search_tokens, data["categories"], data["business_categories"]
        )

        # 각 광고주별 최종 점수 계산
        for advertiser in data["advertisers"]:
            advertiser_id = advertiser["advertiser_id"]

            # 키워드 매칭 점수
            keyword_score = keyword_scores.get(advertiser_id, 0)
            keyword_matches = [
                kw for kw in data["keywords"] if kw["advertiser_id"] == advertiser_id
            ]

            # 카테고리 매칭 점수
            category_score = category_scores.get(advertiser_id, 0)
            category_matches = [
                cat
                for cat in data["categories"]
                if cat["advertiser_id"] == advertiser_id
            ]

            # 최종 매칭 점수
            total_score = keyword_score + (category_score * 0.6)

            # 매칭 이유 생성
            reasons = []
            if keyword_score > 0:
                reasons.append(f"키워드 매칭: {keyword_score:.2f}점")
            if category_score > 0:
                reasons.append(f"카테고리 매칭: {category_score:.2f}점")

            # 품질 점수 기준 확인
            if total_score == 0 and quality_score >= advertiser.get(
                "min_quality_score", 0
            ):
                total_score = 0.1
                reasons.append("품질 점수 기준 충족")

            if total_score > 0:
                results.append(
                    MatchingResult(
                        advertiser_id=advertiser_id,
                        company_name=advertiser["company_name"],
                        match_score=total_score,
                        match_reasons=reasons,
                        keyword_matches=keyword_matches,
                        category_matches=category_matches,
                        auto_bid_settings={
                            "daily_budget": advertiser["daily_budget"],
                            "max_bid_per_keyword": advertiser["max_bid_per_keyword"],
                            "min_quality_score": advertiser["min_quality_score"],
                        },
                        review_status=advertiser["review_status"],
                    )
                )

        return results

    def _calculate_keyword_scores(
        self, search_tokens: set, keywords: List[Dict[str, Any]]
    ) -> Dict[int, float]:
        """키워드 매칭 점수 계산"""
        scores = {}

        for keyword in keywords:
            advertiser_id = keyword["advertiser_id"]
            if advertiser_id not in scores:
                scores[advertiser_id] = 0

            # 매치 타입별 점수 차등
            if keyword["match_type"] == "exact":
                score_boost = 1.0
            elif keyword["match_type"] == "phrase":
                score_boost = 0.85
            elif keyword["match_type"] == "broad":
                score_boost = 0.7
            else:
                score_boost = 0.5

            # 우선순위 가중치
            priority_weight = 1 + (keyword["priority"] / 10.0)

            scores[advertiser_id] += score_boost * priority_weight

        return scores

    def _calculate_category_scores(
        self,
        search_tokens: set,
        categories: List[Dict[str, Any]],
        business_categories: List[Dict[str, Any]],
    ) -> Dict[int, float]:
        """카테고리 매칭 점수 계산"""
        scores = {}

        # 카테고리명 매칭
        matched_categories = set()
        for token in search_tokens:
            for bc in business_categories:
                if token in bc["name"].lower():
                    matched_categories.add(bc["path"])

        # 매칭된 카테고리의 광고주들에 점수 부여
        for category in categories:
            if category["category_path"] in matched_categories:
                advertiser_id = category["advertiser_id"]
                if advertiser_id not in scores:
                    scores[advertiser_id] = 0

                # 기본 점수 + primary 가중치
                base_score = 0.6
                if category["is_primary"]:
                    base_score *= 1.2

                scores[advertiser_id] += base_score

        return scores

    def _filter_and_sort_results(
        self, results: List[MatchingResult]
    ) -> List[MatchingResult]:
        """결과 필터링 및 정렬"""
        # 매칭 점수가 0보다 큰 것만 필터링
        filtered_results = [r for r in results if r.match_score > 0]

        # 매칭 점수 내림차순 정렬
        return sorted(filtered_results, key=lambda x: x.match_score, reverse=True)

    def _generate_cache_key(self, search_query: str, quality_score: int) -> str:
        """캐시 키 생성"""
        content = f"{search_query}_{quality_score}"
        return hashlib.md5(content.encode()).hexdigest()

    async def _get_from_cache(self, cache_key: str) -> Optional[List[MatchingResult]]:
        """캐시에서 데이터 조회"""
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if datetime.now().timestamp() - timestamp < self.cache_ttl:
                return cached_data
            else:
                del self.cache[cache_key]
        return None

    async def _save_to_cache(self, cache_key: str, data: List[MatchingResult]):
        """캐시에 데이터 저장"""
        self.cache[cache_key] = (data, datetime.now().timestamp())

    async def calculate_optimized_bid_price(
        self,
        advertiser_id: int,
        match_score: float,
        auto_bid_settings: Dict[str, Any],
        review_data: Optional[Dict[str, Any]],
    ) -> int:
        """최적화된 입찰가 계산"""

        # 기본 입찰가 = 최대 입찰가의 (매칭 점수)%
        base_bid = int(auto_bid_settings["max_bid_per_keyword"] * min(match_score, 1.0))

        # 심사 결과에 따른 조정
        if review_data and review_data.get("review_status") == "approved":
            recommended_min = review_data.get("recommended_bid_min", 0)
            recommended_max = review_data.get("recommended_bid_max", base_bid)

            base_bid = max(recommended_min, min(base_bid, recommended_max))

        return max(base_bid, 0)

    async def check_budget_availability_optimized(
        self, advertiser_id: int, bid_amount: int, daily_budget: float
    ) -> bool:
        """최적화된 예산 확인"""

        # 오늘 지출액 조회
        spend_query = """
            SELECT COALESCE(SUM(price), 0) as total_spent
            FROM bids b
            JOIN auctions a ON b.auction_id = a.id
            WHERE b.advertiser_id = :advertiser_id
              AND DATE(a.created_at) = CURRENT_DATE
        """

        result = await self.database.fetch_one(
            spend_query, {"advertiser_id": advertiser_id}
        )

        total_spent = result["total_spent"] if result else 0

        # 예산 확인
        return (total_spent + bid_amount) <= daily_budget


class OptimizedBidGenerator:
    """최적화된 입찰 생성기"""

    def __init__(self, database):
        self.database = database
        self.matcher = OptimizedAdvertiserMatcher(database)

    async def generate_optimized_bids(
        self, search_query: str, quality_score: int
    ) -> List[Dict[str, Any]]:
        """최적화된 입찰 생성"""

        print(f"최적화된 입찰 생성 시작: '{search_query}'")

        # 1. 매칭된 광고주 조회
        matching_results = await self.matcher.find_matching_advertisers_optimized(
            search_query, quality_score
        )

        if not matching_results:
            print("매칭된 광고주 없음")
            return []

        # 2. 각 광고주별 입찰 생성
        bids = []
        for result in matching_results:
            try:
                # 입찰가 계산
                if result.auto_bid_settings:
                    bid_price = await self.matcher.calculate_optimized_bid_price(
                        result.advertiser_id,
                        result.match_score,
                        result.auto_bid_settings,
                        (
                            {"review_status": result.review_status}
                            if result.review_status
                            else None
                        ),
                    )
                else:
                    continue

                if bid_price <= 0:
                    continue

                # 예산 확인
                if (
                    result.auto_bid_settings
                    and "daily_budget" in result.auto_bid_settings
                ):
                    budget_available = (
                        await self.matcher.check_budget_availability_optimized(
                            result.advertiser_id,
                            bid_price,
                            result.auto_bid_settings["daily_budget"],
                        )
                    )
                else:
                    continue

                if not budget_available:
                    print(f"예산 부족: 광고주 {result.advertiser_id}")
                    continue

                # 입찰 정보 생성
                bid_data = {
                    "advertiser_id": result.advertiser_id,
                    "company_name": result.company_name,
                    "bid_price": bid_price,
                    "match_score": result.match_score,
                    "match_reasons": result.match_reasons,
                    "website_url": (
                        result.auto_bid_settings.get("website_url", "")
                        if result.auto_bid_settings
                        else ""
                    ),
                    "keyword_matches": result.keyword_matches,
                    "category_matches": result.category_matches,
                }

                bids.append(bid_data)
                print(f"입찰 생성: {result.company_name} - {bid_price}원")

            except Exception as e:
                print(f"입찰 생성 오류 (광고주 {result.advertiser_id}): {e}")
                continue

        # 3. 입찰가 내림차순 정렬
        bids.sort(key=lambda x: x["bid_price"], reverse=True)

        print(f"최종 입찰 생성 완료: {len(bids)}개")
        return bids
