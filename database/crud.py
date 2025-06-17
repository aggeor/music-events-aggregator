from sqlalchemy.future import select
from database.db import Event, AsyncSessionLocal, init_db

async def save_events_to_db(events: list[dict]):
    await init_db()

    async with AsyncSessionLocal() as session:
        for e in events:
            query = select(Event).where(Event.title == e["title"], Event.date == e["date"])
            result = await session.execute(query)
            existing = result.scalar_one_or_none()
            if existing:
                continue

            event = Event(
                title=e["title"],
                date=e["date"],
                location=e["location"],
                imageUrl=e["imageUrl"],
                detailsUrl=e["detailsUrl"]
            )
            session.add(event)

        await session.commit()
