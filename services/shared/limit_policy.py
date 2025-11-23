"""
일일 제출 한도 정책의 단일 소스 (Single Source of Truth)

이 모듈은 User Service와 Quality Service에서 공통으로 사용하는
한도 계산 로직을 제공합니다.

기존 비즈니스 규칙 유지:
- 70점 미만: 기본 한도 (5회)
- 70점 이상: 기본 한도 + 10회 (15회)

추후 확장 가능한 구조로 설계:
- settled_today 파라미터는 정산 완료 건수 기반 보너스 한도에 활용 가능
- 품질 점수 등급별 세분화 가능
"""
import os
from dataclasses import dataclass
from typing import Literal

# 품질 레벨 타입 정의
QualityLevel = Literal[
    "Excellent",
    "Very Good",
    "Good",
    "Average",
    "Below Average",
    "Poor",
    "Very Poor",
    "Standard",
]


@dataclass
class LimitInfo:
    """일일 제출 한도 정보"""
    daily_max: int  # 오늘 최종 허용 제출 횟수 (하드 캡)
    level: QualityLevel  # 품질 레벨명


def calculate_dynamic_limit(
    quality_score: int, 
    settled_today: int = 0
) -> LimitInfo:
    """
    일일 제출 한도를 품질 점수에 따라 동적으로 계산합니다.
    
    Args:
        quality_score: 사용자의 품질 점수 (0-100)
        settled_today: 오늘 정산 완료된 트랜잭션 수 (확장용, 현재는 미사용)
    
    Returns:
        LimitInfo: 일일 제출 한도 정보
    
    현재 규칙:
        - 70점 미만: 기본 한도 (환경 변수 DEFAULT_DAILY_LIMIT, 기본값 5)
        - 70점 이상: 기본 한도 + 10회 (총 15회)
    
    추후 확장 가능:
        - settled_today를 활용한 정산 완료 건수 기반 보너스
        - 품질 점수 등급별 세분화 (80점, 90점 등)
    """
    # 환경 변수에서 기본 한도 가져오기 (기본값: 5)
    base_limit = int(os.getenv("DEFAULT_DAILY_LIMIT", "5"))
    
    # 현재 비즈니스 규칙: 70점 기준
    # 기존 동작을 유지하면서 확장 가능한 구조로 작성
    if quality_score >= 70:
        daily_max = base_limit + 10  # 기본 5회 + 추가 10회 = 15회
        level = "Good"
    else:
        daily_max = base_limit  # 기본 5회
        level = "Average"
    
    # 추후 확장 예시 (주석 처리):
    # if quality_score >= 90 and settled_today >= 5:
    #     daily_max = base_limit + 15  # 20회
    #     level = "Excellent"
    # elif quality_score >= 80 and settled_today >= 3:
    #     daily_max = base_limit + 10  # 15회
    #     level = "Very Good"
    # elif quality_score >= 70:
    #     daily_max = base_limit + 5   # 10회
    #     level = "Good"
    # else:
    #     daily_max = base_limit       # 5회
    #     level = "Average"
    
    return LimitInfo(daily_max=daily_max, level=level)

