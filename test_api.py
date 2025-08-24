#!/usr/bin/env python3
"""
API 테스트 스크립트
실제 API 호출을 통해 수정사항이 제대로 작동하는지 확인
"""

import requests
import json
import time

# API 엔드포인트
BASE_URL = "http://localhost:3000"
USER_SERVICE_URL = "http://localhost:8005"


def test_login():
    """로그인 테스트"""
    print("🔐 로그인 테스트...")

    # 여러 사용자로 시도
    test_users = [
        {"email": "won@won.com", "password": "ljh04021", "userType": "user"},
        {"email": "testuser2@example.com", "password": "test123", "userType": "user"},
        {"email": "test@example.com", "password": "password123", "userType": "user"},
        {"email": "sample@example.com", "password": "password123", "userType": "user"},
        {
            "email": "action5861@gmail.com",
            "password": "password123",
            "userType": "user",
        },
    ]

    for user_data in test_users:
        print(f"   시도 중: {user_data['email']}")
        try:
            response = requests.post(f"{BASE_URL}/api/auth/login", json=user_data)
            print(f"   응답 상태: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                print(f"✅ 로그인 성공! ({user_data['email']}) 토큰: {token[:20]}...")
                return token
            else:
                print(f"   실패: {response.text}")
        except Exception as e:
            print(f"   에러: {e}")

    print("❌ 모든 사용자 로그인 실패")
    return None


def test_search_with_auth(token):
    """인증된 검색 테스트"""
    print("\n🔍 인증된 검색 테스트...")

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    search_data = {"query": "테스트 검색어 - API 테스트"}

    try:
        response = requests.post(
            f"{BASE_URL}/api/search", json=search_data, headers=headers
        )
        print(f"검색 응답 상태: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ 검색 성공!")
            print(f"   - 품질 점수: {data['data']['qualityReport']['score']}")
            print(f"   - 경매 ID: {data['data']['auction']['searchId']}")
            return data["data"]["auction"]["searchId"]
        else:
            print(f"❌ 검색 실패: {response.text}")
            return None
    except Exception as e:
        print(f"❌ 검색 에러: {e}")
        return None


def test_dashboard_data(token):
    """대시보드 데이터 테스트"""
    print("\n📊 대시보드 데이터 테스트...")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{BASE_URL}/api/user/dashboard", headers=headers)
        print(f"대시보드 응답 상태: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ 대시보드 데이터 성공!")
            print(f"   - 총 수익: {data['earnings']['total']}원")
            print(f"   - 이번달 수익: {data['earnings']['thisMonth']['total']}원")
            print(f"   - 품질 이력 개수: {len(data['qualityHistory'])}")
            print(f"   - 일일 제출 한도: {data['submissionLimit']['dailyMax']}")
            print(f"   - 월간 검색 횟수: {data['stats']['monthlySearches']}")
            print(f"   - 성공률: {data['stats']['successRate']}%")
            print(f"   - 평균 품질 점수: {data['stats']['avgQualityScore']}")
            return True
        else:
            print(f"❌ 대시보드 실패: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 대시보드 에러: {e}")
        return False


def test_auction_selection(token, search_id):
    """경매 선택 테스트"""
    print(f"\n🏆 경매 선택 테스트 (Search ID: {search_id})...")

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    # 먼저 경매 정보를 가져와서 입찰 ID를 확인
    try:
        auction_response = requests.get(
            f"{BASE_URL}/api/auction/{search_id}", headers=headers
        )
        if auction_response.status_code == 200:
            auction_data = auction_response.json()
            if auction_data["data"]["bids"]:
                bid_id = auction_data["data"]["bids"][0]["id"]

                select_data = {"searchId": search_id, "selectedBidId": bid_id}

                response = requests.post(
                    f"{BASE_URL}/api/auction/select", json=select_data, headers=headers
                )
                print(f"경매 선택 응답 상태: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ 경매 선택 성공!")
                    print(f"   - 보상 금액: {data['data']['rewardAmount']}원")
                    return True
                else:
                    print(f"❌ 경매 선택 실패: {response.text}")
                    return False
            else:
                print("❌ 입찰이 없습니다.")
                return False
        else:
            print(f"❌ 경매 정보 조회 실패: {auction_response.text}")
            return False
    except Exception as e:
        print(f"❌ 경매 선택 에러: {e}")
        return False


def main():
    """메인 테스트 함수"""
    print("🚀 API 테스트 시작...\n")

    # 1. 로그인
    token = test_login()
    if not token:
        print("❌ 로그인 실패로 테스트 중단")
        return

    # 2. 검색 테스트
    search_id = test_search_with_auth(token)
    if not search_id:
        print("❌ 검색 실패로 테스트 중단")
        return

    # 3. 잠시 대기 (데이터 처리 시간)
    print("\n⏳ 데이터 처리 대기 중...")
    time.sleep(2)

    # 4. 대시보드 데이터 테스트
    dashboard_success = test_dashboard_data(token)

    # 5. 경매 선택 테스트
    if search_id:
        auction_success = test_auction_selection(token, search_id)

        if auction_success:
            # 6. 다시 대시보드 확인 (업데이트된 데이터)
            print("\n⏳ 경매 완료 후 데이터 처리 대기 중...")
            time.sleep(2)
            test_dashboard_data(token)

    print("\n🎉 API 테스트 완료!")


if __name__ == "__main__":
    main()
