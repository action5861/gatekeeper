import requests
import json

# 품질 서비스 직접 테스트
QUALITY_SERVICE_URL = "http://localhost:8006"


def test_base_limit():
    """base_limit 값을 확인하는 테스트"""
    print("🔍 base_limit 값 확인 테스트...")

    # 100점 테스트 (Excellent 등급)
    try:
        response = requests.post(
            f"{QUALITY_SERVICE_URL}/calculate-limit",
            json={"qualityScore": 100},
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            data = response.json()
            limit = data["data"]
            print(f"✅ 100점: {limit['level']} 등급, {limit['dailyMax']}개")

            # base_limit 계산
            if limit["level"] == "Excellent":
                base_limit = limit["dailyMax"] / 3
                print(f"🔍 계산된 base_limit: {base_limit}")
            else:
                print(f"❌ 예상과 다른 등급: {limit['level']}")
        else:
            print(f"❌ 테스트 실패: {response.status_code}")

    except Exception as e:
        print(f"❌ 테스트 오류: {e}")


if __name__ == "__main__":
    test_base_limit()
