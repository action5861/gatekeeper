#!/usr/bin/env python3
"""
최종 테스트 스크립트: 올바른 비밀번호로 등록 및 수익 테스트
"""
import requests
import json
import time

# API Gateway URL
BASE_URL = "http://localhost:8000"


def test_final():
    print("🧪 최종 테스트: 사용자 등록 및 /api/user/earnings 엔드포인트 테스트...")

    try:
        # 1. 새로운 사용자 등록 (올바른 비밀번호)
        print("\n1️⃣ 사용자 등록 중...")
        register_data = {
            "username": "testuser456",
            "email": "testuser456@example.com",
            "password": "TestPassword123!",
        }

        print(f"등록 요청: {register_data}")

        register_response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=register_data,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        print(f"등록 응답 상태: {register_response.status_code}")
        print(f"등록 응답 내용: {register_response.text}")

        if register_response.status_code not in [200, 201]:
            print("❌ 등록 실패")
            return False

        print("✅ 등록 성공!")

        # 2. 로그인
        print("\n2️⃣ 로그인 중...")
        login_data = {
            "email": "testuser456@example.com",
            "password": "TestPassword123!",
        }

        login_response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        print(f"로그인 응답 상태: {login_response.status_code}")
        print(f"로그인 응답 내용: {login_response.text}")

        if login_response.status_code != 200:
            print("❌ 로그인 실패")
            return False

        login_result = login_response.json()
        token = login_result.get("access_token")
        print(f"✅ 로그인 성공! 토큰: {token[:20]}...")

        # 3. /api/user/earnings 엔드포인트 테스트
        print("\n3️⃣ /api/user/earnings 엔드포인트 테스트...")
        earnings_data = {
            "amount": 1000,
            "query": "테스트 검색어",
            "adType": "bidded",
            "searchId": "test_search_001",
            "bidId": "test_bid_001",
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        }

        print(f"요청 데이터: {earnings_data}")

        earnings_response = requests.post(
            f"{BASE_URL}/api/user/earnings",
            json=earnings_data,
            headers=headers,
            timeout=10,
        )

        print(f"📊 응답 상태 코드: {earnings_response.status_code}")
        print(f"📊 응답 내용: {earnings_response.text}")

        if earnings_response.status_code == 201:
            print("✅ /api/user/earnings 엔드포인트 테스트 성공!")
            result = earnings_response.json()
            print(f"✅ 트랜잭션 ID: {result.get('transaction', {}).get('id', 'N/A')}")
            print(f"✅ 사용자 ID: {result.get('user_id', 'N/A')}")
            print(f"✅ 금액: {result.get('amount', 'N/A')}")
            return True
        else:
            print(f"❌ /api/user/earnings 엔드포인트 테스트 실패!")
            return False

    except requests.exceptions.ConnectionError:
        print("❌ 연결 오류: 서비스가 실행 중인지 확인하세요.")
        return False
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Gatekeeper API 최종 테스트 시작")
    print("=" * 50)

    success = test_final()

    print("\n" + "=" * 50)
    if success:
        print("🎉 모든 테스트 성공!")
    else:
        print("💥 테스트 실패!")




