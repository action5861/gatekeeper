#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json


def test_user_login():
    """사용자 로그인 테스트"""

    print("🔍 사용자 로그인 테스트")
    print("=" * 50)

    # 사용자 로그인 데이터
    login_data = {"email": "user@example.com", "password": "password123"}

    try:
        print("1️⃣ 사용자 로그인 시도...")
        login_response = requests.post(
            "http://localhost:8005/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
        )

        print(f"응답 상태 코드: {login_response.status_code}")
        print(f"응답 내용: {login_response.text}")

        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get("access_token")
            print(f"✅ 로그인 성공! 토큰: {token[:20]}...")

            # 대시보드 데이터 요청
            print("\n2️⃣ 사용자 대시보드 데이터 요청...")
            dashboard_response = requests.get(
                "http://localhost:8005/dashboard",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )

            if dashboard_response.status_code == 200:
                dashboard_data = dashboard_response.json()
                print("✅ 대시보드 데이터 조회 성공!")
                print(
                    f"대시보드 데이터: {json.dumps(dashboard_data, indent=2, ensure_ascii=False)}"
                )
            else:
                print(f"❌ 대시보드 API 오류: {dashboard_response.status_code}")
                print(f"응답: {dashboard_response.text}")

        else:
            print(f"❌ 로그인 실패: {login_response.status_code}")
            print(f"응답: {login_response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ user-service에 연결할 수 없습니다.")
        print("Docker 서비스가 실행 중인지 확인해주세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    test_user_login()
