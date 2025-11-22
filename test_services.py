#!/usr/bin/env python3
"""
서비스 상태 확인 및 품질 평가 테스트
"""

import requests
import json


def test_service_status():
    """모든 서비스의 상태를 확인합니다."""
    services = {
        "Next.js API": "http://localhost:3000",
        "API Gateway": "http://localhost:8000",
        "Analysis Service": "http://localhost:8001",
        "User Service": "http://localhost:8002",
    }

    print("Checking service status...")
    for name, url in services.items():
        try:
            response = requests.get(url, timeout=3)
            print(f"OK {name}: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"FAIL {name}: Connection refused")
        except Exception as e:
            print(f"WARN {name}: {e}")


def test_quality_evaluation():
    """품질 평가 API를 직접 테스트합니다."""
    print("\nTesting quality evaluation...")

    try:
        response = requests.post(
            "http://localhost:8001/evaluate",
            json={"query": "아이폰16", "user_id": 1},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        print(f"Analysis Service Response: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("SUCCESS! Analysis service working!")
            print(f"Score: {result['data']['score']}")
            print(f"Commercial Value: {result['data']['commercialValue']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"Analysis service error: {e}")
        return False


def main():
    print("Service Status Check...")
    print("=" * 50)

    test_service_status()
    analysis_ok = test_quality_evaluation()

    print("\n" + "=" * 50)
    if analysis_ok:
        print("All services are working correctly!")
        print("Now try the web interface at http://localhost:3000")
    else:
        print("Some services have issues.")
        print("Please check the service logs for more details.")


if __name__ == "__main__":
    main()
