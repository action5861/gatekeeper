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

# ?�이?�베?�스 URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:your_secure_password_123@postgres:5432/search_exchange_db",
)

# SQLAlchemy ?�정
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Databases (비동�? ?�정
database = Database(DATABASE_URL)

Base = declarative_base()


# ?�� 검??쿼리 모델
class SearchQuery(Base):
    __tablename__ = "search_queries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    query_text = Column(String(500), nullable=False)
    quality_score = Column(Integer, nullable=False)
    commercial_value = Column(String(20), nullable=False)
    keywords = Column(JSON, nullable=True)
    suggestions = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())


# ?���??�용??모델
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )
    total_earnings = Column(DECIMAL(10, 2), default=0.00)
    quality_score = Column(Integer, default=50)
    submission_count = Column(Integer, default=0)


# ?�� ?�용???�질 ?�력 모델
class UserQualityHistory(Base):
    __tablename__ = "user_quality_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    quality_score = Column(Integer, nullable=False)
    week_label = Column(String(20), nullable=False)
    recorded_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())


# ?�이?�베?�스 ?�결 ?�수
async def connect_to_database():
    await database.connect()
    print("✅ Analysis Service database connected successfully!")


async def disconnect_from_database():
    await database.disconnect()
    print("Analysis Service database disconnected")
