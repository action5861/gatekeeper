import os
import asyncio
from databases import Database

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:your_secure_password_123@postgres:5432/search_exchange_db",
)

# Databases (async setup)
database = Database(DATABASE_URL)


# Database connection functions with retry logic
async def connect_to_database():
    """데이터베이스 연결 (재시도 로직 포함)"""
    max_retries = 10
    retry_delay = 2  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            await database.connect()
            print(
                f"✅ Website Analysis Service database connected successfully! (attempt {attempt})"
            )
            return
        except Exception as e:
            if attempt < max_retries:
                print(
                    f"⚠️ Database connection failed (attempt {attempt}/{max_retries}): {e}"
                )
                print(f"🔄 Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
            else:
                print(f"❌ Failed to connect to database after {max_retries} attempts")
                raise


async def disconnect_from_database():
    """데이터베이스 연결 해제"""
    try:
        await database.disconnect()
        print("🔌 Website Analysis Service database disconnected")
    except Exception as e:
        print(f"⚠️ Error disconnecting database: {e}")
