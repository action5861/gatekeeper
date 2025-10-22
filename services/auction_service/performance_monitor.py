"""
Auction Service 성능 모니터링 도구
- 쿼리 성능 측정
- N+1 쿼리 문제 감지
- 성능 메트릭 수집
"""

import time
import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import json


@dataclass
class QueryMetrics:
    """쿼리 성능 메트릭"""

    query: str
    execution_time: float
    result_count: int
    timestamp: datetime = field(default_factory=datetime.now)
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """전체 성능 메트릭"""

    total_queries: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    slow_queries: List[QueryMetrics] = field(default_factory=list)
    n_plus_1_detected: bool = False
    cache_hit_rate: float = 0.0
    matching_accuracy: float = 0.0


class PerformanceMonitor:
    """성능 모니터링 클래스"""

    def __init__(self, database):
        self.database = database
        self.metrics = PerformanceMetrics()
        self.query_history: List[QueryMetrics] = []
        self.query_counts = defaultdict(int)
        self.logger = logging.getLogger(__name__)

        # 성능 임계값 설정
        self.slow_query_threshold = 1.0  # 1초 이상
        self.n_plus_1_threshold = 10  # 10개 이상의 연속 쿼리

    async def monitor_query(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> Any:
        """쿼리 실행 모니터링"""
        start_time = time.time()

        try:
            if "SELECT" in query.upper():
                result = await self.database.fetch_all(query, parameters or {})
            else:
                result = await self.database.execute(query, parameters or {})

            execution_time = time.time() - start_time

            # 메트릭 수집
            query_metric = QueryMetrics(
                query=query,
                execution_time=execution_time,
                result_count=len(result) if isinstance(result, list) else 1,
                parameters=parameters if parameters is not None else {},
            )

            self._update_metrics(query_metric)
            self._detect_n_plus_1(query_metric)

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"쿼리 실행 오류: {query[:100]}... - {str(e)}")
            raise

    def _update_metrics(self, query_metric: QueryMetrics):
        """메트릭 업데이트"""
        self.query_history.append(query_metric)
        self.metrics.total_queries += 1
        self.metrics.total_execution_time += query_metric.execution_time
        self.metrics.average_execution_time = (
            self.metrics.total_execution_time / self.metrics.total_queries
        )

        # 느린 쿼리 감지
        if query_metric.execution_time > self.slow_query_threshold:
            self.metrics.slow_queries.append(query_metric)

    def _detect_n_plus_1(self, query_metric: QueryMetrics):
        """N+1 쿼리 문제 감지"""
        # 최근 10개 쿼리 중 유사한 패턴 감지
        recent_queries = self.query_history[-10:]

        if len(recent_queries) >= self.n_plus_1_threshold:
            # 같은 쿼리 패턴이 반복되는지 확인
            query_patterns = defaultdict(int)
            for qm in recent_queries:
                # 쿼리에서 테이블명과 기본 구조만 추출
                pattern = self._extract_query_pattern(qm.query)
                query_patterns[pattern] += 1

            # 한 패턴이 3번 이상 반복되면 N+1 문제 의심
            max_repetition = max(query_patterns.values()) if query_patterns else 0
            if max_repetition >= 3:
                self.metrics.n_plus_1_detected = True
                self.logger.warning(f"N+1 쿼리 문제 감지: {max_repetition}번 반복")

    def _extract_query_pattern(self, query: str) -> str:
        """쿼리에서 패턴 추출"""
        # SELECT, FROM, WHERE 키워드만 추출
        import re

        pattern = re.sub(r"\s+", " ", query.upper())
        pattern = re.sub(r":\w+", ":param", pattern)  # 파라미터를 :param으로 치환
        return pattern

    def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_queries": self.metrics.total_queries,
            "total_execution_time": round(self.metrics.total_execution_time, 3),
            "average_execution_time": round(self.metrics.average_execution_time, 3),
            "slow_queries_count": len(self.metrics.slow_queries),
            "n_plus_1_detected": self.metrics.n_plus_1_detected,
            "cache_hit_rate": round(self.metrics.cache_hit_rate, 3),
            "matching_accuracy": round(self.metrics.matching_accuracy, 3),
        }

        # 느린 쿼리 상세 정보
        if self.metrics.slow_queries:
            report["slow_queries"] = [
                {
                    "query": (
                        qm.query[:100] + "..." if len(qm.query) > 100 else qm.query
                    ),
                    "execution_time": round(qm.execution_time, 3),
                    "result_count": qm.result_count,
                    "timestamp": qm.timestamp.isoformat(),
                }
                for qm in self.metrics.slow_queries[-5:]  # 최근 5개만
            ]

        return report

    def reset_metrics(self):
        """메트릭 초기화"""
        self.metrics = PerformanceMetrics()
        self.query_history.clear()
        self.query_counts.clear()

    async def save_metrics_to_db(self):
        """메트릭을 데이터베이스에 저장"""
        try:
            report = self.get_performance_report()

            await self.database.execute(
                """
                INSERT INTO auction_performance_metrics 
                (metric_name, metric_value, measurement_time, additional_data)
                VALUES (:metric_name, :metric_value, :measurement_time, :additional_data)
                """,
                {
                    "metric_name": "performance_report",
                    "metric_value": report["average_execution_time"],
                    "measurement_time": datetime.now(),
                    "additional_data": json.dumps(report),
                },
            )

            self.logger.info("성능 메트릭이 데이터베이스에 저장되었습니다.")

        except Exception as e:
            self.logger.error(f"메트릭 저장 오류: {str(e)}")


class OptimizedDatabaseWrapper:
    """최적화된 데이터베이스 래퍼"""

    def __init__(self, database):
        self.database = database
        self.monitor = PerformanceMonitor(database)

    async def fetch_all(self, query: str, values: Optional[Dict[str, Any]] = None):
        """모니터링이 포함된 fetch_all"""
        return await self.monitor.monitor_query(query, values)

    async def fetch_one(self, query: str, values: Optional[Dict[str, Any]] = None):
        """모니터링이 포함된 fetch_one"""
        result = await self.monitor.monitor_query(query, values)
        return result[0] if result else None

    async def execute(self, query: str, values: Optional[Dict[str, Any]] = None):
        """모니터링이 포함된 execute"""
        return await self.monitor.monitor_query(query, values)

    def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 조회"""
        return self.monitor.get_performance_report()

    async def save_metrics(self):
        """메트릭 저장"""
        await self.monitor.save_metrics_to_db()


# 성능 테스트 함수들
async def run_performance_tests(database):
    """성능 테스트 실행"""
    print("🚀 Auction Service 성능 테스트 시작")

    wrapper = OptimizedDatabaseWrapper(database)

    # 테스트 쿼리들
    test_queries = [
        "SELECT COUNT(*) FROM advertisers",
        "SELECT * FROM advertiser_keywords LIMIT 10",
        "SELECT * FROM auto_bid_settings WHERE is_enabled = true",
        "SELECT * FROM advertiser_categories LIMIT 5",
        "SELECT * FROM business_categories WHERE is_active = true",
    ]

    # 쿼리 실행
    for query in test_queries:
        try:
            await wrapper.fetch_all(query)
            print(f"✅ 쿼리 실행 완료: {query[:50]}...")
        except Exception as e:
            print(f"❌ 쿼리 실행 실패: {str(e)}")

    # 성능 리포트 생성
    report = wrapper.get_performance_report()
    print("\n📊 성능 리포트:")
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # 메트릭 저장
    await wrapper.save_metrics()

    return report


if __name__ == "__main__":
    # 성능 테스트 실행
    import asyncio
    from database import database

    async def main():
        await run_performance_tests(database)

    asyncio.run(main())
