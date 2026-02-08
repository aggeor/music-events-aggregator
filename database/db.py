from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, DateTime, Integer, String, Index
import os
DATABASE_URL = os.getenv("DATABASE_URL")

Base = declarative_base()

class Event(Base):
    __tablename__ = "music_events"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    location = Column(String)
    imageUrl = Column(String)
    detailsUrl = Column(String, unique=True, nullable=True)  # Unique when present, but optional
    sourceName = Column(String)
    sourceUrl = Column(String)
    
    # Add indexes for common queries
    __table_args__ = (
        Index('idx_start_date', 'start_date'),
        Index('idx_source_name', 'sourceName'),
    )

# Create async engine and session factory
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Function to create tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
