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


# Database connection functions
async def connect_to_database():
    await database.connect()
    print("✅ Advertiser Service database connected successfully!")


async def disconnect_from_database():
    await database.disconnect()
    print("Advertiser Service database disconnected")
