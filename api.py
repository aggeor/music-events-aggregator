from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from datetime import datetime

from database.db import AsyncSessionLocal, Event as EventDB 

app = FastAPI()

# Get DB session
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Pydantic schema
class EventSchema(BaseModel):
    id: int
    title: str
    start_date: datetime
    end_date: datetime
    location: str
    imageUrl: str | None
    detailsUrl: str | None
    sourceName: str
    sourceUrl: str

    class Config:
        orm_mode = True  # allows Pydantic to work directly with ORM objects

@app.get("/events", response_model=list[EventSchema])
async def get_events(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EventDB))
    events = result.scalars().all()
    return events
