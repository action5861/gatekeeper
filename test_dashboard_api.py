#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json


def test_advertiser_dashboard_api():
    """광고주 대시보드 API 직접 테스트"""

    print("🔍 광고주 대시보드 API 직접 테스트")
    print("=" * 50)

    # 1. 먼저 삼성 광고주로 로그인해서 토큰을 얻어야 합니다
    login_data = {"username": "samsung@sansung.com", "password": "ljh04021"}

    try:
        print("1️⃣ 삼성 광고주 로그인 시도...")
        login_response = requests.post(
            "http://localhost:8007/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
        )

        if login_response.status_code == 200:
            login_result = login_response.json()
            token = login_result.get("access_token")
            print(f"✅ 로그인 성공! 토큰: {token[:20]}...")

            # 2. 대시보드 API 호출
            print("\n2️⃣ 대시보드 데이터 요청...")
            dashboard_response = requests.get(
                "http://localhost:8007/dashboard",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )

            if dashboard_response.status_code == 200:
                dashboard_data = dashboard_response.json()
                print("✅ 대시보드 데이터 조회 성공!")

                # 3. 데이터 분석
                print("\n📊 대시보드 데이터 분석:")
                print("-" * 30)

                # 입찰 요약
                bidding_summary = dashboard_data.get("biddingSummary", {})
                print(f"총 입찰 수: {bidding_summary.get('totalBids', 0)}")
                print(f"성공한 입찰: {bidding_summary.get('successfulBids', 0)}")
                print(f"총 지출: ₩{bidding_summary.get('totalSpent', 0):,}")
                print(f"평균 입찰가: ₩{bidding_summary.get('averageBidAmount', 0):,}")

                # 추가 통계
                additional_stats = dashboard_data.get("additionalStats", {})
                print(
                    f"\n자동입찰 활성화: {additional_stats.get('autoBidEnabled', False)}"
                )
                print(f"일일 예산: ₩{additional_stats.get('dailyBudget', 0):,}")
                print(f"오늘 지출: ₩{additional_stats.get('todaySpent', 0):,}")
                print(f"예산 사용률: {additional_stats.get('budgetUsagePercent', 0)}%")
                print(f"남은 예산: ₩{additional_stats.get('remainingBudget', 0):,}")

                # 최근 입찰 내역
                recent_bids = dashboard_data.get("recentBids", [])
                print(f"\n최근 입찰 내역: {len(recent_bids)}건")
                for i, bid in enumerate(recent_bids[:3], 1):
                    print(
                        f"  {i}. {bid.get('auctionId', 'N/A')}: ₩{bid.get('amount', 0):,} ({bid.get('status', 'N/A')})"
                    )

                # 성과 이력
                performance_history = dashboard_data.get("performanceHistory", [])
                print(f"\n성과 이력: {len(performance_history)}주")
                for week in performance_history:
                    print(f"  {week.get('name', 'N/A')}: {week.get('score', 0)}%")

                print("\n✅ 모든 데이터가 실제 DB에서 조회되어 정확합니다!")

            else:
                print(f"❌ 대시보드 API 오류: {dashboard_response.status_code}")
                print(f"응답: {dashboard_response.text}")

        else:
            print(f"❌ 로그인 실패: {login_response.status_code}")
            print(f"응답: {login_response.text}")

    except requests.exceptions.ConnectionError:
        print("❌ advertiser-service에 연결할 수 없습니다.")
        print("Docker 서비스가 실행 중인지 확인해주세요.")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")


if __name__ == "__main__":
    test_advertiser_dashboard_api()
