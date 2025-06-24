import asyncio

from crawler.iereies_tis_nychtas import crawl_iereies
from crawler.aptaliko import crawl_aptaliko
from database.crud import save_events_to_db

async def main():
    iereies_data = await crawl_iereies()
    if iereies_data:
        await save_events_to_db(iereies_data)
    
    aptaliko_data = await crawl_aptaliko()
    if aptaliko_data:
        await save_events_to_db(aptaliko_data)

if __name__ == "__main__":
    asyncio.run(main())