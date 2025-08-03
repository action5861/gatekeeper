#!/usr/bin/env python3
"""
기존 사용자들의 비밀번호를 bcrypt로 업데이트하는 스크립트
"""

import asyncio
from passlib.context import CryptContext
from database import connect_to_database, disconnect_from_database, database

# bcrypt 컨텍스트 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def update_user_passwords():
    """기존 사용자들의 비밀번호를 bcrypt로 업데이트"""
    try:
        await connect_to_database()
        print("✅ 데이터베이스에 연결되었습니다.")

        # 모든 사용자 조회
        users = await database.fetch_all("SELECT id, email, username FROM users")
        print(f"📋 총 {len(users)}명의 사용자를 찾았습니다.")

        # 기본 비밀번호 (모든 사용자를 'password123'으로 설정)
        new_password = "password123"
        hashed_password = pwd_context.hash(new_password)

        updated_count = 0
        for user in users:
            try:
                # 사용자 비밀번호 업데이트
                await database.execute(
                    "UPDATE users SET hashed_password = :hashed_password WHERE id = :user_id",
                    {"hashed_password": hashed_password, "user_id": user["id"]},
                )
                print(f"✅ {user['email']} ({user['username']}) 비밀번호 업데이트 완료")
                updated_count += 1
            except Exception as e:
                print(f"❌ {user['email']} 업데이트 실패: {e}")

        print(f"\n🎉 총 {updated_count}명의 사용자 비밀번호가 업데이트되었습니다.")
        print("📝 모든 사용자의 비밀번호는 'password123'으로 설정되었습니다.")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        await disconnect_from_database()
        print("🔌 데이터베이스 연결이 종료되었습니다.")


if __name__ == "__main__":
    asyncio.run(update_user_passwords())
