from fastapi import FastAPI, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from datetime import datetime

from database.db import AsyncSessionLocal, Event as EventDB 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allowed origins for dynamic CORS
ALLOWED_ORIGINS = {
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://events.maenox.com",
    "http://events.maenox.com",
    "https://music-events-frontend-rose.vercel.app"
    "http://music-events-frontend-rose.vercel.app",
}

# CORSMiddleware for methods, headers, credentials
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # let custom middleware control the origin dynamically
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware to dynamically set Access-Control-Allow-Origin
@app.middleware("http")
async def dynamic_cors(request: Request, call_next):
    response = await call_next(request)
    origin = request.headers.get("origin")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
    return response

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
