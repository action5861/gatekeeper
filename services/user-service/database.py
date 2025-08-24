import os
from sqlalchemy import create_engine, Column, Integer, String, DateTime, DECIMAL, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from databases import Database
import asyncpg

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://admin:your_secure_password_123@postgres:5432/search_exchange_db",
)

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Databases (async setup)
database = Database(DATABASE_URL)

Base = declarative_base()


# User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
    total_earnings = Column(DECIMAL(10, 2), default=0.00)
    quality_score = Column(Integer, default=50)
    submission_count = Column(Integer, default=0)


# Transaction model
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(100), primary_key=True)
    user_id = Column(Integer, nullable=True)
    query_text = Column(String(500), nullable=False)
    buyer_name = Column(String(100), nullable=False)
    primary_reward = Column(DECIMAL(10, 2), nullable=False)
    secondary_reward = Column(DECIMAL(10, 2), nullable=True)
    status = Column(String(20), default="1차 완료")
    created_at = Column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


# Quality history model
class UserQualityHistory(Base):
    __tablename__ = "user_quality_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    quality_score = Column(Integer, nullable=False)
    week_label = Column(String(20), nullable=False)
    recorded_at = Column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )


# Database connection functions
async def connect_to_database():
    try:
        print("🔌 Attempting to connect to database...")
        print(f"🔌 Database URL: {DATABASE_URL}")
        await database.connect()
        print("✅ User Service database connected successfully!")
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print(f"❌ Error type: {type(e)}")
        import traceback

        print(f"❌ Traceback: {traceback.format_exc()}")
        raise e


async def disconnect_from_database():
    try:
        await database.disconnect()
        print("User Service database disconnected")
    except Exception as e:
        print(f"❌ Database disconnection error: {str(e)}")
