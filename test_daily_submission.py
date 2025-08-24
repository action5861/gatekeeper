import requests
import json
import time

# API Gateway URL
BASE_URL = "http://localhost:8000"


def test_quality_service():
    """품질 서비스의 동적 한도 계산 테스트"""
    print("🔍 품질 서비스 테스트 시작...")

    test_scores = [95, 90, 80, 70, 50, 30, 20]

    for score in test_scores:
        try:
            response = requests.post(
                f"{BASE_URL}/api/quality/calculate-limit",
                json={"qualityScore": score},
                headers={"Content-Type": "application/json"},
            )

            if response.status_code == 200:
                data = response.json()
                limit = data["data"]
                print(
                    f"✅ 품질점수 {score}점: {limit['level']} 등급, {limit['dailyMax']}개"
                )
            else:
                print(f"❌ 품질점수 {score}점 테스트 실패: {response.status_code}")

        except Exception as e:
            print(f"❌ 품질점수 {score}점 테스트 오류: {e}")


def test_user_login():
    """사용자 로그인 테스트"""
    print("\n🔐 사용자 로그인 테스트...")

    try:
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "test@example.com", "password": "testpass123"},
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ 로그인 성공, 토큰 획득")
            return token
        else:
            print(f"❌ 로그인 실패: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ 로그인 오류: {e}")
        return None


def test_dashboard_data(token):
    """대시보드 데이터 테스트"""
    print("\n📊 대시보드 데이터 테스트...")

    try:
        response = requests.get(
            f"{BASE_URL}/api/user/dashboard",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

        if response.status_code == 200:
            data = response.json()
            submission_limit = data.get("submissionLimit")
            daily_submission = data.get("dailySubmission")

            print(f"✅ 대시보드 데이터 성공")
            print(
                f"   - 제출 한도: {submission_limit['level']} ({submission_limit['dailyMax']}개)"
            )
            print(
                f"   - 오늘 사용량: {daily_submission['count']}/{daily_submission['limit']}"
            )
            print(f"   - 남은 횟수: {daily_submission['remaining']}")
            print(f"   - 평균 품질: {daily_submission['qualityScoreAvg']}점")

            return True
        else:
            print(f"❌ 대시보드 데이터 실패: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 대시보드 데이터 오류: {e}")
        return False


def test_daily_submission_update(token, quality_score):
    """일일 제출 카운트 업데이트 테스트"""
    print(f"\n📝 일일 제출 업데이트 테스트 (품질점수: {quality_score})...")

    try:
        response = requests.post(
            f"{BASE_URL}/api/user/update-daily-submission",
            json={"quality_score": quality_score},
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

        if response.status_code == 200:
            data = response.json()
            daily_submission = data.get("dailySubmission")
            submission_limit = data.get("submissionLimit")

            print(f"✅ 업데이트 성공")
            print(
                f"   - 새로운 한도: {submission_limit['level']} ({submission_limit['dailyMax']}개)"
            )
            print(
                f"   - 현재 사용량: {daily_submission['count']}/{daily_submission['limit']}"
            )
            print(f"   - 남은 횟수: {daily_submission['remaining']}")
            print(f"   - 평균 품질: {daily_submission['qualityScoreAvg']}점")

            return True
        else:
            print(f"❌ 업데이트 실패: {response.status_code}")
            print(f"   응답: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 업데이트 오류: {e}")
        return False


def main():
    print("🚀 일일 제출 한도 시스템 테스트 시작")
    print("=" * 50)

    # 1. 품질 서비스 테스트
    test_quality_service()

    # 2. 사용자 로그인
    token = test_user_login()
    if not token:
        print("❌ 로그인 실패로 인해 테스트 중단")
        return

    # 3. 초기 대시보드 데이터 확인
    if not test_dashboard_data(token):
        print("❌ 대시보드 데이터 조회 실패")
        return

    # 4. 일일 제출 카운트 업데이트 테스트 (여러 번)
    test_scores = [85, 92, 78, 95, 88]

    for i, score in enumerate(test_scores, 1):
        print(f"\n--- {i}번째 제출 테스트 ---")
        if test_daily_submission_update(token, score):
            time.sleep(1)  # 1초 대기
        else:
            print("❌ 업데이트 실패로 테스트 중단")
            break

    # 5. 최종 대시보드 데이터 확인
    print("\n📊 최종 대시보드 데이터 확인...")
    test_dashboard_data(token)

    print("\n✅ 테스트 완료!")


if __name__ == "__main__":
    main()
