from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from datetime import datetime

from database.db import AsyncSessionLocal, Event as EventDB 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow requests from your frontend (Next.js runs on port 3000)
origins = [
    "http://localhost:3000",   # Next.js dev server
    "http://127.0.0.1:3000",
    # add production domain later, e.g. "https://myfrontend.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Which origins can talk to API
    allow_credentials=True,
    allow_methods=["*"],         # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],         # Allow all headers
)

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
