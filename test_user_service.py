#!/usr/bin/env python3
"""
User Service 직접 테스트
"""

import requests
import json

# User Service URL
USER_SERVICE_URL = "http://localhost:8005"


def test_search_completed():
    """search-completed API 직접 테스트"""
    print("🔍 User Service search-completed API 직접 테스트...")

    # 먼저 로그인해서 토큰 얻기
    login_data = {"email": "won@won.com", "password": "ljh04021"}

    try:
        login_response = requests.post(f"{USER_SERVICE_URL}/login", json=login_data)
        print(f"로그인 응답: {login_response.status_code}")

        if login_response.status_code == 200:
            token_data = login_response.json()
            token = token_data.get("access_token")
            print(f"토큰 획득: {token[:20]}...")

            # search-completed API 테스트
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }

            test_data = {
                "query": "테스트 검색어",
                "quality_score": 75,
                "commercial_value": "high",
                "keywords": {"keyword1": "value1"},
                "suggestions": {"suggestion1": "value1"},
                "auction_id": "test_auction_123",
            }

            print(f"전송할 데이터: {json.dumps(test_data, indent=2)}")

            response = requests.post(
                f"{USER_SERVICE_URL}/search-completed", json=test_data, headers=headers
            )

            print(f"응답 상태: {response.status_code}")
            print(f"응답 내용: {response.text}")

            if response.status_code == 200:
                print("✅ search-completed API 성공!")
            else:
                print("❌ search-completed API 실패!")

        else:
            print(f"❌ 로그인 실패: {login_response.text}")

    except Exception as e:
        print(f"❌ 에러: {e}")


if __name__ == "__main__":
    test_search_completed()
