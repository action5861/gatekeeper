import os
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    DECIMAL,
    Text,
    Boolean,
    ForeignKey,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
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


# Advertiser model
class Advertiser(Base):
    __tablename__ = "advertisers"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    company_name = Column(String(100), nullable=False)
    website_url = Column(String(255), nullable=True)
    daily_budget = Column(DECIMAL(10, 2), default=10000.00)
    created_at = Column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


# Auction model
class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(String(100), unique=True, nullable=False)
    query_text = Column(String(500), nullable=False)
    user_id = Column(Integer, nullable=True)
    status = Column(String(20), default="active")
    created_at = Column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
    selected_bid_id = Column(String(100), nullable=True)


# Bid model
class Bid(Base):
    __tablename__ = "bids"

    id = Column(String(100), primary_key=True)
    auction_id = Column(Integer, nullable=True)
    buyer_name = Column(String(100), nullable=False)
    price = Column(Integer, nullable=False)
    bonus_description = Column(Text, nullable=True)
    landing_url = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )


# AdvertiserKeyword model
class AdvertiserKeyword(Base):
    __tablename__ = "advertiser_keywords"

    id = Column(Integer, primary_key=True, index=True)
    advertiser_id = Column(
        Integer, ForeignKey("advertisers.id", ondelete="CASCADE"), nullable=False
    )
    keyword = Column(String(100), nullable=False)
    priority = Column(Integer, default=1)  # 1-5
    match_type = Column(String(20), default="broad")  # exact, phrase, broad
    created_at = Column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


# AdvertiserCategory model
class AdvertiserCategory(Base):
    __tablename__ = "advertiser_categories"

    id = Column(Integer, primary_key=True, index=True)
    advertiser_id = Column(
        Integer, ForeignKey("advertisers.id", ondelete="CASCADE"), nullable=False
    )
    category_path = Column(String(200), nullable=False)
    category_level = Column(Integer, nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )


# AdvertiserReview model
class AdvertiserReview(Base):
    __tablename__ = "advertiser_reviews"

    id = Column(Integer, primary_key=True, index=True)
    advertiser_id = Column(
        Integer, ForeignKey("advertisers.id", ondelete="CASCADE"), nullable=False
    )
    review_status = Column(
        String(20), default="pending"
    )  # pending, in_progress, approved, rejected
    reviewer_id = Column(Integer, nullable=True)
    review_notes = Column(Text, nullable=True)
    website_analysis = Column(Text, nullable=True)
    recommended_bid_min = Column(Integer, default=100)
    recommended_bid_max = Column(Integer, default=5000)
    created_at = Column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


# AutoBidSetting model
class AutoBidSetting(Base):
    __tablename__ = "auto_bid_settings"

    id = Column(Integer, primary_key=True, index=True)
    advertiser_id = Column(
        Integer, ForeignKey("advertisers.id", ondelete="CASCADE"), nullable=False
    )
    is_enabled = Column(Boolean, default=False)
    daily_budget = Column(DECIMAL(10, 2), default=10000.00)
    max_bid_per_keyword = Column(Integer, default=3000)
    min_quality_score = Column(Integer, default=50)
    preferred_categories = Column(JSON, nullable=True)
    excluded_keywords = Column(JSON, nullable=True)  # TEXT[] 대신 JSON으로 저장
    created_at = Column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


# BusinessCategory model
class BusinessCategory(Base):
    __tablename__ = "business_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    path = Column(String(200), nullable=False)
    level = Column(Integer, nullable=True)
    parent_id = Column(Integer, ForeignKey("business_categories.id"), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.current_timestamp()
    )
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, nullable=True)


# Database connection functions
async def connect_to_database():
    await database.connect()
    print("✅ Advertiser Service database connected successfully!")


async def disconnect_from_database():
    await database.disconnect()
    print("Advertiser Service database disconnected")
