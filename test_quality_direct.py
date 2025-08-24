import requests
import json

# 품질 서비스 직접 테스트
QUALITY_SERVICE_URL = "http://localhost:8006"


def test_quality_service_direct():
    """품질 서비스를 직접 테스트"""
    print("🔍 품질 서비스 직접 테스트 시작...")

    test_scores = [95, 90, 80, 70, 50, 30, 20]

    for score in test_scores:
        try:
            response = requests.post(
                f"{QUALITY_SERVICE_URL}/calculate-limit",
                json={"qualityScore": score},
                headers={"Content-Type": "application/json"},
            )

            print(f"품질점수 {score}점 - 상태코드: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                limit = data["data"]
                print(
                    f"✅ 품질점수 {score}점: {limit['level']} 등급, {limit['dailyMax']}개"
                )
            else:
                print(f"❌ 응답: {response.text}")

        except Exception as e:
            print(f"❌ 품질점수 {score}점 테스트 오류: {e}")

    # 헬스체크
    try:
        response = requests.get(f"{QUALITY_SERVICE_URL}/health")
        print(f"\n🏥 헬스체크 - 상태코드: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ 헬스체크 성공: {response.json()}")
        else:
            print(f"❌ 헬스체크 실패: {response.text}")
    except Exception as e:
        print(f"❌ 헬스체크 오류: {e}")


if __name__ == "__main__":
    test_quality_service_direct()
