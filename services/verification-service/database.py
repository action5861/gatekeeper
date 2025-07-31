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


# ?�� 검�??�청 모델
class VerificationRequest(Base):
    __tablename__ = "verification_requests"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(100), nullable=True)
    proof_file_path = Column(String(500), nullable=True)
    verification_status = Column(String(20), default="pending")
    verification_result = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    processed_at = Column(DateTime(timezone=True), nullable=True)


# ?�� 거래 ?�역 모델
class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(100), primary_key=True)
    user_id = Column(Integer, nullable=True)
    auction_id = Column(Integer, nullable=True)
    query_text = Column(String(500), nullable=False)
    buyer_name = Column(String(100), nullable=False)
    primary_reward = Column(DECIMAL(10, 2), nullable=False)
    secondary_reward = Column(DECIMAL(10, 2), nullable=True)
    status = Column(String(20), default="1�??�료")
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )


# ?�이?�베?�스 ?�결 ?�수
async def connect_to_database():
    await database.connect()
    print("✅ Verification Service database connected successfully!")


async def disconnect_from_database():
    await database.disconnect()
    print("Verification Service database disconnected")
