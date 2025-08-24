import requests
import json

# 품질 서비스 직접 테스트
QUALITY_SERVICE_URL = "http://localhost:8006"


def test_all_scores():
    """모든 점수 범위를 테스트하여 base_limit 계산"""
    print("🔍 모든 점수 범위 테스트...")

    test_cases = [
        (100, "Excellent", 3),  # 100점: Excellent, 300%
        (95, "Excellent", 3),  # 95점: Excellent, 300%
        (90, "Very Good", 2),  # 90점: Very Good, 200%
        (80, "Good", 1.6),  # 80점: Good, 160%
        (70, "Average", 1.2),  # 70점: Average, 120%
        (50, "Below Average", 1),  # 50점: Below Average, 100%
        (30, "Poor", 0.6),  # 30점: Poor, 60%
        (20, "Very Poor", 0.4),  # 20점: Very Poor, 40%
    ]

    for score, expected_level, multiplier in test_cases:
        try:
            response = requests.post(
                f"{QUALITY_SERVICE_URL}/calculate-limit",
                json={"qualityScore": score},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                data = response.json()
                limit = data["data"]
                print(f"✅ {score}점: {limit['level']} 등급, {limit['dailyMax']}개")

                # base_limit 계산
                calculated_base_limit = limit["dailyMax"] / multiplier
                print(f"   계산된 base_limit: {calculated_base_limit:.2f}")

                if limit["level"] != expected_level:
                    print(
                        f"   ⚠️ 예상 등급과 다름: 예상={expected_level}, 실제={limit['level']}"
                    )
            else:
                print(f"❌ {score}점 테스트 실패: {response.status_code}")

        except Exception as e:
            print(f"❌ {score}점 테스트 오류: {e}")


if __name__ == "__main__":
    test_all_scores()
