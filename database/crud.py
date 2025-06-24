from sqlalchemy.future import select
from database.db import Event, AsyncSessionLocal, init_db

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)
async def save_events_to_db(events: list[dict]):
    LOGGER.info(f"Inserting events to database")
    await init_db()

    async with AsyncSessionLocal() as session:
        for e in events:
            query = select(Event).where(
                Event.title == e["title"],
                Event.start_date == e["start_date"],
                Event.end_date == e["end_date"]
            )
            result = await session.execute(query)
            existing = result.scalar_one_or_none()
            if existing:
                continue

            event = Event(
                title=e["title"],
                start_date=e["start_date"],
                end_date=e["end_date"],
                location=e["location"],
                imageUrl=e["imageUrl"],
                detailsUrl=e["detailsUrl"]
            )
            session.add(event)

        await session.commit()
        LOGGER.info(f"Completed inserting {len(events)} events")
