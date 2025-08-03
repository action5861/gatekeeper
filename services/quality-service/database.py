import os
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    DECIMAL,
    Text,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from databases import Database
import asyncpg

# 데이터베이스 URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:your_secure_password_123@postgres:5432/search_exchange_db",
)

# SQLAlchemy 설정
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Databases (비동기 설정)
database = Database(DATABASE_URL)

Base = declarative_base()


# 사용자 품질 이력 모델
class UserQualityHistory(Base):
    __tablename__ = "user_quality_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    quality_score = Column(Integer, nullable=False)
    week_label = Column(String(20), nullable=False)
    recorded_at = Column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )


# 데이터베이스 연결 함수
async def connect_to_database():
    await database.connect()
    print("✅ Quality Service database connected successfully!")


async def disconnect_from_database():
    await database.disconnect()
    print("Quality Service database disconnected")
