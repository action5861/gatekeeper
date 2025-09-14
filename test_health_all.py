import requests


def test_health_all():
    """모든 서비스의 헬스체크를 확인"""
    print("🏥 모든 서비스 헬스체크...")

    services = [
        ("API Gateway", "http://localhost:8000/health"),
        ("User Service", "http://localhost:8001/health"),
        ("Advertiser Service", "http://localhost:8002/health"),
        ("Auction Service", "http://localhost:8003/health"),
        ("Payment Service", "http://localhost:8004/health"),
        ("Port 8005", "http://localhost:8005/health"),
        ("Quality Service", "http://localhost:8006/health"),
        ("Port 8007", "http://localhost:8007/health"),
    ]

    for service_name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {service_name}: {data}")
            else:
                print(f"❌ {service_name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {service_name}: {e}")


if __name__ == "__main__":
    test_health_all()










