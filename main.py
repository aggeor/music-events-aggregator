import asyncio

from crawler.crawler import iereies
from database.crud import save_events_to_db

async def main():
    data = await iereies()
    if data:
        await save_events_to_db(data)

if __name__ == "__main__":
    asyncio.run(main())