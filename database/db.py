from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, DateTime, Integer, String

# SQLite file-based DB for dev
DATABASE_URL = "sqlite+aiosqlite:///database/music_events.db"

Base = declarative_base()

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    date = Column(DateTime)
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
