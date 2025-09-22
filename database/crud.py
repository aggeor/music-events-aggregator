from sqlalchemy.future import select
from database.db import Event, AsyncSessionLocal, init_db
from utils.helper import LOGGER

async def save_events_to_db(events: list[dict]):
    LOGGER.info("Inserting/updating events in database")
    await init_db()

    async with AsyncSessionLocal() as session:
        for e in events:
            # Use detailsUrl if available, otherwise fallback to title + location
            if e.get("detailsUrl"):
                query = select(Event).where(Event.detailsUrl == e["detailsUrl"])
            else:
                query = select(Event).where(
                    Event.title == e["title"],
                    Event.location == e["location"]
                )

            result = await session.execute(query)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing event
                existing.title = e["title"]
                existing.start_date = e["start_date"]
                existing.end_date = e["end_date"]
                existing.location = e["location"]
                existing.imageUrl = e["imageUrl"]
                existing.detailsUrl = e["detailsUrl"]
                existing.sourceName = e["sourceName"]
                existing.sourceUrl = e["sourceUrl"]
            else:
                # Insert new event
                event = Event(**e)
                session.add(event)

        await session.commit()
        LOGGER.info(f"Completed inserting/updating {len(events)} events")
