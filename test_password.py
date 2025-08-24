#!/usr/bin/env python3
"""
비밀번호 해시 테스트
데이터베이스의 해시된 비밀번호가 올바른지 확인
"""

import bcrypt


def test_password_hash():
    """비밀번호 해시 테스트"""
    print("🔐 비밀번호 해시 테스트...")

    # 데이터베이스에 있는 해시들
    stored_hashes = [
        "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj0kEa8E0zdy",  # testuser
        "$2b$12$nx10nz1xEJ3WKO75WmeD4e2JMSH9JZJmVcTqK1/1K10D98lJdkqLq",  # won@won.com
    ]

    # 테스트할 비밀번호들
    test_passwords = [
        "password123",
        "password",
        "123456",
        "admin",
        "test",
        "user",
        "sample",
        "won",
        "won123",
        "1234",
        "0000",
        "1111",
        "2222",
        "3333",
        "4444",
        "5555",
        "6666",
        "7777",
        "8888",
        "9999",
        "123123",
        "abc123",
        "qwerty",
        "asdf",
        "zxcv",
        "password1",
        "password2",
        "test123",
        "user123",
        "admin123",
    ]

    for i, stored_hash in enumerate(stored_hashes):
        print(f"\n해시 {i+1}: {stored_hash[:20]}...")
        for password in test_passwords:
            try:
                # 비밀번호를 바이트로 변환
                password_bytes = password.encode("utf-8")

                # 해시 검증
                is_valid = bcrypt.checkpw(password_bytes, stored_hash.encode("utf-8"))

                if is_valid:
                    print(f"✅ 비밀번호 일치: '{password}'")
                    return password, stored_hash
                else:
                    print(f"❌ 비밀번호 불일치: '{password}'")
            except Exception as e:
                print(f"❌ 에러 ({password}): {e}")

    print("❌ 일치하는 비밀번호를 찾을 수 없습니다.")
    return None, None


def create_test_user():
    """테스트용 사용자 생성"""
    print("\n👤 테스트용 사용자 생성...")

    password = "test123"
    password_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

    print(f"비밀번호: {password}")
    print(f"해시: {hashed.decode('utf-8')}")

    return password, hashed.decode("utf-8")


if __name__ == "__main__":
    # 기존 해시 테스트
    correct_password, correct_hash = test_password_hash()

    if not correct_password:
        # 새로운 테스트 사용자 생성
        password, hashed = create_test_user()
        print(f"\n새로운 테스트 사용자 정보:")
        print(f"이메일: testuser2@example.com")
        print(f"비밀번호: {password}")
        print(f"해시: {hashed}")
