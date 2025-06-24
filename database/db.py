from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, DateTime, Integer, String
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
    detailsUrl = Column(String)

# Create async engine and session factory
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Function to create tables
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
