"""
머신러닝 기반 자동 입찰 최적화 시스템
성공한 입찰 패턴 분석, 광고주별 최적 입찰가 자동 조정, 
시간대별 입찰 강도 조절, 경쟁 상황 기반 실시간 가격 조정
"""

import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from dataclasses import dataclass
from enum import Enum

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BidResult(Enum):
    WON = "won"
    LOST = "lost"
    TIMEOUT = "timeout"


class MatchType(Enum):
    EXACT = "exact"
    PHRASE = "phrase"
    BROAD = "broad"


@dataclass
class BidContext:
    """입찰 컨텍스트 정보"""

    search_query: str
    quality_score: int
    match_type: MatchType
    match_score: float
    competitor_count: int
    time_of_day: int
    day_of_week: int
    historical_success_rate: float
    avg_winning_bid: float
    budget_remaining: float


@dataclass
class OptimizationResult:
    """최적화 결과"""

    recommended_bid: int
    confidence_score: float
    reasoning: str
    expected_success_rate: float
    cost_efficiency: float


class AutoBidOptimizer:
    """머신러닝 기반 자동 입찰 최적화기"""

    def __init__(self, database_connection):
        self.db = database_connection
        self.learning_rate = 0.1
        self.min_bid = 100
        self.max_bid = 10000

    async def get_optimal_bid(
        self, advertiser_id: int, context: BidContext
    ) -> OptimizationResult:
        """최적 입찰가 계산"""
        try:
            # 1. 과거 성과 데이터 분석
            historical_data = await self._get_historical_performance(
                advertiser_id, context
            )

            # 2. 경쟁 상황 분석
            competition_analysis = await self._analyze_competition(context)

            # 3. 시간대별 패턴 분석
            time_pattern = await self._analyze_time_pattern(advertiser_id, context)

            # 4. 키워드별 성과 분석
            keyword_performance = await self._analyze_keyword_performance(
                advertiser_id, context.search_query
            )

            # 5. 머신러닝 모델을 통한 예측
            predicted_success_rate = self._predict_success_rate(
                context,
                historical_data,
                competition_analysis,
                time_pattern,
                keyword_performance,
            )

            # 6. 최적 입찰가 계산
            optimal_bid = self._calculate_optimal_bid(
                context, predicted_success_rate, competition_analysis
            )

            # 7. 비용 효율성 계산
            cost_efficiency = self._calculate_cost_efficiency(
                optimal_bid, predicted_success_rate
            )

            # 8. 신뢰도 점수 계산
            confidence_score = self._calculate_confidence_score(
                historical_data, competition_analysis, keyword_performance
            )

            reasoning = self._generate_reasoning(
                context, optimal_bid, predicted_success_rate, competition_analysis
            )

            return OptimizationResult(
                recommended_bid=int(optimal_bid),
                confidence_score=confidence_score,
                reasoning=reasoning,
                expected_success_rate=predicted_success_rate,
                cost_efficiency=cost_efficiency,
            )

        except Exception as e:
            logger.error(f"Error calculating optimal bid: {e}")
            # 기본값 반환
            return OptimizationResult(
                recommended_bid=1000,
                confidence_score=0.5,
                reasoning="기본 입찰가 사용 (오류 발생)",
                expected_success_rate=0.5,
                cost_efficiency=0.5,
            )

    async def _get_historical_performance(
        self, advertiser_id: int, context: BidContext
    ) -> Dict:
        """과거 성과 데이터 분석"""
        try:
            # 최근 30일간의 입찰 데이터 조회
            query = """
                SELECT 
                    bid_amount,
                    bid_result,
                    match_score,
                    quality_score,
                    competitor_count,
                    EXTRACT(HOUR FROM created_at) as hour,
                    EXTRACT(DOW FROM created_at) as day_of_week
                FROM auto_bid_logs
                WHERE advertiser_id = :advertiser_id
                AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                AND search_query ILIKE :query_pattern
            """

            # 검색 쿼리 패턴 생성 (유사 키워드 포함)
            query_pattern = f"%{context.search_query}%"

            results = await self.db.fetch_all(
                query, {"advertiser_id": advertiser_id, "query_pattern": query_pattern}
            )

            if not results:
                return self._get_default_historical_data()

            # 성공률 계산
            total_bids = len(results)
            won_bids = sum(1 for r in results if r["bid_result"] == "won")
            success_rate = won_bids / total_bids if total_bids > 0 else 0

            # 평균 입찰가 계산
            bid_amounts = [r["bid_amount"] for r in results]
            avg_bid = sum(bid_amounts) / len(bid_amounts) if bid_amounts else 1000
            winning_bids = [
                r["bid_amount"] for r in results if r["bid_result"] == "won"
            ]
            avg_winning_bid = (
                sum(winning_bids) / len(winning_bids) if winning_bids else avg_bid
            )

            # 매칭 점수별 성과
            match_score_performance = {}
            for result in results:
                score_range = int(result["match_score"] * 10) / 10  # 0.1 단위로 그룹화
                if score_range not in match_score_performance:
                    match_score_performance[score_range] = {"total": 0, "won": 0}
                match_score_performance[score_range]["total"] += 1
                if result["bid_result"] == "won":
                    match_score_performance[score_range]["won"] += 1

            return {
                "total_bids": total_bids,
                "success_rate": success_rate,
                "avg_bid": avg_bid,
                "avg_winning_bid": avg_winning_bid,
                "match_score_performance": match_score_performance,
                "recent_trend": self._calculate_recent_trend(results),
            }

        except Exception as e:
            logger.error(f"Error getting historical performance: {e}")
            return self._get_default_historical_data()

    def _get_default_historical_data(self) -> Dict:
        """기본 과거 데이터"""
        return {
            "total_bids": 0,
            "success_rate": 0.5,
            "avg_bid": 1000,
            "avg_winning_bid": 1200,
            "match_score_performance": {},
            "recent_trend": 0,
        }

    async def _analyze_competition(self, context: BidContext) -> Dict:
        """경쟁 상황 분석"""
        try:
            # 최근 24시간 내 동일 키워드 경쟁 분석
            query = """
                SELECT 
                    AVG(bid_amount) as avg_competitor_bid,
                    COUNT(*) as competitor_bid_count,
                    AVG(CASE WHEN bid_result = 'won' THEN bid_amount ELSE NULL END) as avg_winning_competitor_bid
                FROM auto_bid_logs
                WHERE search_query ILIKE :query_pattern
                AND created_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
                AND advertiser_id != :advertiser_id
            """

            results = await self.db.fetch_one(
                query,
                {
                    "query_pattern": f"%{context.search_query}%",
                    "advertiser_id": 0,  # 기본값
                },
            )

            if not results:
                return {
                    "avg_competitor_bid": 1000,
                    "competitor_bid_count": 0,
                    "avg_winning_competitor_bid": 1200,
                    "competition_level": "low",
                }

            avg_competitor_bid = results["avg_competitor_bid"] or 1000
            competitor_count = results["competitor_bid_count"] or 0
            avg_winning_competitor_bid = results["avg_winning_competitor_bid"] or 1200

            # 경쟁 수준 판단
            if competitor_count > 10:
                competition_level = "high"
            elif competitor_count > 5:
                competition_level = "medium"
            else:
                competition_level = "low"

            return {
                "avg_competitor_bid": avg_competitor_bid,
                "competitor_bid_count": competitor_count,
                "avg_winning_competitor_bid": avg_winning_competitor_bid,
                "competition_level": competition_level,
            }

        except Exception as e:
            logger.error(f"Error analyzing competition: {e}")
            return {
                "avg_competitor_bid": 1000,
                "competitor_bid_count": 0,
                "avg_winning_competitor_bid": 1200,
                "competition_level": "low",
            }

    async def _analyze_time_pattern(
        self, advertiser_id: int, context: BidContext
    ) -> Dict:
        """시간대별 패턴 분석"""
        try:
            query = """
                SELECT 
                    EXTRACT(HOUR FROM created_at) as hour,
                    COUNT(*) as total_bids,
                    AVG(CASE WHEN bid_result = 'won' THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                    AVG(bid_amount) as avg_bid
                FROM auto_bid_logs
                WHERE advertiser_id = :advertiser_id
                AND created_at >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY EXTRACT(HOUR FROM created_at)
                ORDER BY hour
            """

            results = await self.db.fetch_all(query, {"advertiser_id": advertiser_id})

            if not results:
                return {"hour_performance": {}, "best_hour": 12, "worst_hour": 0}

            hour_performance = {}
            for result in results:
                hour_performance[int(result["hour"])] = {
                    "success_rate": result["success_rate"],
                    "avg_bid": result["avg_bid"],
                    "total_bids": result["total_bids"],
                }

            # 최고/최저 성과 시간대 찾기
            if hour_performance:
                best_hour = max(
                    hour_performance.keys(),
                    key=lambda h: hour_performance[h]["success_rate"],
                )
                worst_hour = min(
                    hour_performance.keys(),
                    key=lambda h: hour_performance[h]["success_rate"],
                )
            else:
                best_hour = 12
                worst_hour = 0

            return {
                "hour_performance": hour_performance,
                "best_hour": best_hour,
                "worst_hour": worst_hour,
            }

        except Exception as e:
            logger.error(f"Error analyzing time pattern: {e}")
            return {"hour_performance": {}, "best_hour": 12, "worst_hour": 0}

    async def _analyze_keyword_performance(
        self, advertiser_id: int, search_query: str
    ) -> Dict:
        """키워드별 성과 분석"""
        try:
            query = """
                SELECT 
                    search_query,
                    COUNT(*) as total_bids,
                    AVG(CASE WHEN bid_result = 'won' THEN 1.0 ELSE 0.0 END) * 100 as success_rate,
                    AVG(bid_amount) as avg_bid,
                    AVG(match_score) as avg_match_score
                FROM auto_bid_logs
                WHERE advertiser_id = :advertiser_id
                AND search_query ILIKE :query_pattern
                AND created_at >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY search_query
                ORDER BY success_rate DESC
                LIMIT 5
            """

            results = await self.db.fetch_all(
                query,
                {"advertiser_id": advertiser_id, "query_pattern": f"%{search_query}%"},
            )

            if not results:
                return {
                    "keyword_success_rate": 0.5,
                    "keyword_avg_bid": 1000,
                    "similar_keywords": [],
                }

            # 유사 키워드 성과
            similar_keywords = []
            for result in results:
                similar_keywords.append(
                    {
                        "keyword": result["search_query"],
                        "success_rate": result["success_rate"],
                        "avg_bid": result["avg_bid"],
                        "total_bids": result["total_bids"],
                    }
                )

            # 전체 키워드 성과 평균
            success_rates = [r["success_rate"] for r in results]
            avg_bids = [r["avg_bid"] for r in results]

            avg_success_rate = (
                sum(success_rates) / len(success_rates) if success_rates else 0.5
            )
            avg_bid = sum(avg_bids) / len(avg_bids) if avg_bids else 1000

            return {
                "keyword_success_rate": avg_success_rate,
                "keyword_avg_bid": avg_bid,
                "similar_keywords": similar_keywords,
            }

        except Exception as e:
            logger.error(f"Error analyzing keyword performance: {e}")
            return {
                "keyword_success_rate": 0.5,
                "keyword_avg_bid": 1000,
                "similar_keywords": [],
            }

    def _predict_success_rate(
        self,
        context: BidContext,
        historical_data: Dict,
        competition_analysis: Dict,
        time_pattern: Dict,
        keyword_performance: Dict,
    ) -> float:
        """머신러닝 모델을 통한 성공률 예측"""
        try:
            # 특성 벡터 생성
            features = {
                "match_score": context.match_score,
                "quality_score": context.quality_score / 100.0,  # 0-1 범위로 정규화
                "competitor_count": min(
                    context.competitor_count / 10.0, 1.0
                ),  # 0-1 범위로 정규화
                "historical_success_rate": historical_data["success_rate"],
                "avg_winning_bid_ratio": context.avg_winning_bid
                / 5000.0,  # 0-1 범위로 정규화
                "budget_remaining_ratio": min(context.budget_remaining / 10000.0, 1.0),
                "time_of_day_factor": self._get_time_factor(
                    context.time_of_day, time_pattern
                ),
                "match_type_factor": self._get_match_type_factor(context.match_type),
            }

            # 가중치 (실제로는 학습된 가중치 사용)
            weights = {
                "match_score": 0.25,
                "quality_score": 0.20,
                "competitor_count": -0.15,
                "historical_success_rate": 0.20,
                "avg_winning_bid_ratio": -0.10,
                "budget_remaining_ratio": 0.05,
                "time_of_day_factor": 0.03,
                "match_type_factor": 0.02,
            }

            # 선형 모델로 예측
            prediction = sum(features[key] * weights[key] for key in features.keys())

            # 시그모이드 함수로 0-1 범위로 변환
            predicted_success_rate = 1 / (1 + math.exp(-prediction))

            # 경계값 설정
            predicted_success_rate = max(0.1, min(0.9, predicted_success_rate))

            return predicted_success_rate

        except Exception as e:
            logger.error(f"Error predicting success rate: {e}")
            return 0.5

    def _calculate_optimal_bid(
        self,
        context: BidContext,
        predicted_success_rate: float,
        competition_analysis: Dict,
    ) -> float:
        """최적 입찰가 계산"""
        try:
            # 기본 입찰가 (경쟁자 평균 입찰가 기반)
            base_bid = competition_analysis["avg_competitor_bid"]

            # 성공률에 따른 조정
            success_rate_adjustment = (predicted_success_rate - 0.5) * 0.3  # ±15% 조정

            # 품질 점수에 따른 조정
            quality_adjustment = (context.quality_score - 50) / 100 * 0.2  # ±10% 조정

            # 매칭 점수에 따른 조정
            match_score_adjustment = (context.match_score - 0.5) * 0.2  # ±10% 조정

            # 예산 상황에 따른 조정
            budget_adjustment = 0
            if context.budget_remaining < 1000:
                budget_adjustment = -0.1  # 예산 부족시 10% 감소
            elif context.budget_remaining > 5000:
                budget_adjustment = 0.05  # 예산 여유시 5% 증가

            # 경쟁 수준에 따른 조정
            competition_adjustment = 0
            if competition_analysis["competition_level"] == "high":
                competition_adjustment = 0.1  # 경쟁 심할 때 10% 증가
            elif competition_analysis["competition_level"] == "low":
                competition_adjustment = -0.05  # 경쟁 적을 때 5% 감소

            # 최종 입찰가 계산
            optimal_bid = base_bid * (
                1
                + success_rate_adjustment
                + quality_adjustment
                + match_score_adjustment
                + budget_adjustment
                + competition_adjustment
            )

            # 경계값 적용
            optimal_bid = max(self.min_bid, min(self.max_bid, optimal_bid))

            return optimal_bid

        except Exception as e:
            logger.error(f"Error calculating optimal bid: {e}")
            return 1000

    def _calculate_cost_efficiency(
        self, bid_amount: float, success_rate: float
    ) -> float:
        """비용 효율성 계산"""
        try:
            # ROI 기반 효율성 계산
            expected_roi = success_rate * 2.0  # 성공시 2배 수익 가정
            cost_efficiency = expected_roi / (bid_amount / 1000)  # 1000원 단위로 정규화

            return min(1.0, max(0.0, cost_efficiency))

        except Exception as e:
            logger.error(f"Error calculating cost efficiency: {e}")
            return 0.5

    def _calculate_confidence_score(
        self,
        historical_data: Dict,
        competition_analysis: Dict,
        keyword_performance: Dict,
    ) -> float:
        """신뢰도 점수 계산"""
        try:
            # 데이터 품질 점수
            data_quality = min(historical_data["total_bids"] / 100.0, 1.0)

            # 경쟁 데이터 품질
            competition_quality = min(
                competition_analysis["competitor_bid_count"] / 20.0, 1.0
            )

            # 키워드 데이터 품질
            keyword_quality = min(
                len(keyword_performance["similar_keywords"]) / 5.0, 1.0
            )

            # 가중 평균
            confidence_score = (
                data_quality * 0.5 + competition_quality * 0.3 + keyword_quality * 0.2
            )

            return max(0.1, min(1.0, confidence_score))

        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return 0.5

    def _generate_reasoning(
        self,
        context: BidContext,
        optimal_bid: float,
        predicted_success_rate: float,
        competition_analysis: Dict,
    ) -> str:
        """추천 이유 생성"""
        try:
            reasons = []

            # 성공률 기반 이유
            if predicted_success_rate > 0.7:
                reasons.append("높은 예상 성공률")
            elif predicted_success_rate < 0.3:
                reasons.append("낮은 예상 성공률로 인한 보수적 입찰")

            # 경쟁 상황 기반 이유
            if competition_analysis["competition_level"] == "high":
                reasons.append("높은 경쟁 상황")
            elif competition_analysis["competition_level"] == "low":
                reasons.append("낮은 경쟁 상황")

            # 품질 점수 기반 이유
            if context.quality_score > 80:
                reasons.append("높은 품질 점수")
            elif context.quality_score < 30:
                reasons.append("낮은 품질 점수")

            # 매칭 점수 기반 이유
            if context.match_score > 0.8:
                reasons.append("높은 매칭 정확도")
            elif context.match_score < 0.3:
                reasons.append("낮은 매칭 정확도")

            if not reasons:
                reasons.append("균형잡힌 입찰 전략")

            return ", ".join(reasons)

        except Exception as e:
            logger.error(f"Error generating reasoning: {e}")
            return "기본 추천"

    def _calculate_recent_trend(self, results: List[Dict]) -> float:
        """최근 트렌드 계산"""
        try:
            if len(results) < 2:
                return 0

            # 최근 10개 입찰의 성공률 변화
            recent_results = results[-10:]
            first_half = recent_results[: len(recent_results) // 2]
            second_half = recent_results[len(recent_results) // 2 :]

            if not first_half or not second_half:
                return 0

            first_success_rate = sum(
                1 for r in first_half if r["bid_result"] == "won"
            ) / len(first_half)
            second_success_rate = sum(
                1 for r in second_half if r["bid_result"] == "won"
            ) / len(second_half)

            return second_success_rate - first_success_rate

        except Exception as e:
            logger.error(f"Error calculating recent trend: {e}")
            return 0

    def _get_time_factor(self, hour: int, time_pattern: Dict) -> float:
        """시간대별 조정 팩터"""
        try:
            hour_performance = time_pattern.get("hour_performance", {})
            if hour in hour_performance:
                success_rate = hour_performance[hour]["success_rate"]
                return (success_rate - 50) / 100  # -0.5 ~ 0.5 범위
            return 0

        except Exception as e:
            logger.error(f"Error getting time factor: {e}")
            return 0

    def _get_match_type_factor(self, match_type: MatchType) -> float:
        """매칭 타입별 조정 팩터"""
        try:
            factors = {
                MatchType.EXACT: 0.1,  # 정확 매칭은 10% 증가
                MatchType.PHRASE: 0.05,  # 구문 매칭은 5% 증가
                MatchType.BROAD: -0.05,  # 광범위 매칭은 5% 감소
            }
            return factors.get(match_type, 0)

        except Exception as e:
            logger.error(f"Error getting match type factor: {e}")
            return 0

    async def update_model(
        self,
        advertiser_id: int,
        bid_result: BidResult,
        actual_bid: int,
        context: BidContext,
    ):
        """모델 업데이트 (학습)"""
        try:
            # 입찰 결과를 로그에 저장
            await self._log_bid_result(advertiser_id, bid_result, actual_bid, context)

            # 주기적으로 모델 재학습 (실제로는 더 정교한 학습 알고리즘 사용)
            logger.info(f"Bid result logged: {bid_result.value} for bid {actual_bid}")

        except Exception as e:
            logger.error(f"Error updating model: {e}")

    async def _log_bid_result(
        self,
        advertiser_id: int,
        bid_result: BidResult,
        actual_bid: int,
        context: BidContext,
    ):
        """입찰 결과 로깅"""
        try:
            query = """
                INSERT INTO auto_bid_logs (
                    advertiser_id, search_query, match_type, match_score, 
                    bid_amount, bid_result, quality_score, competitor_count, created_at
                ) VALUES (
                    :advertiser_id, :search_query, :match_type, :match_score,
                    :bid_amount, :bid_result, :quality_score, :competitor_count, CURRENT_TIMESTAMP
                )
            """

            await self.db.execute(
                query,
                {
                    "advertiser_id": advertiser_id,
                    "search_query": context.search_query,
                    "match_type": context.match_type.value,
                    "match_score": context.match_score,
                    "bid_amount": actual_bid,
                    "bid_result": bid_result.value,
                    "quality_score": context.quality_score,
                    "competitor_count": context.competitor_count,
                },
            )

        except Exception as e:
            logger.error(f"Error logging bid result: {e}")


# 사용 예시
async def create_auto_bid_optimizer(database_connection):
    """자동 입찰 최적화기 생성"""
    return AutoBidOptimizer(database_connection)
