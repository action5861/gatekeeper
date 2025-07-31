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


# ?�� 경매 모델
class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(String(100), unique=True, nullable=False)
    query_text = Column(String(500), nullable=False)
    user_id = Column(Integer, nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    selected_bid_id = Column(String(100), nullable=True)


# ?�� ?�찰 모델
class Bid(Base):
    __tablename__ = "bids"

    id = Column(String(100), primary_key=True)
    auction_id = Column(Integer, nullable=True)
    buyer_name = Column(String(100), nullable=False)
    price = Column(Integer, nullable=False)
    bonus_description = Column(Text, nullable=True)
    landing_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.current_timestamp())


# ?�이?�베?�스 ?�결 ?�수
async def connect_to_database():
    await database.connect()
    print("✅ Auction Service database connected successfully!")


async def disconnect_from_database():
    await database.disconnect()
    print("Auction Service database disconnected")
