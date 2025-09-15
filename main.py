import asyncio

from crawler.athinorama import crawl_athinorama
from crawler.iereies_tis_nychtas import crawl_iereies
from crawler.aptaliko import crawl_aptaliko
from crawler.clubber import crawl_clubber
from crawler.more_com import crawl_more_com
from crawler.ticketmaster import crawl_ticketmaster
from database.crud import save_events_to_db
from utils.helper import print_serialized, LOGGER

# Registry of all crawlers
CRAWLERS = [
    crawl_iereies,
    crawl_aptaliko,
    crawl_athinorama,
    crawl_clubber,
    crawl_more_com,
    crawl_ticketmaster,
]

async def run_crawler(crawler_func):
    """Run a single crawler, print and save results."""
    try:
        events = await crawler_func()
        if not events:
            LOGGER.warning(f"No events returned from {crawler_func.__name__}")
            return
        print_serialized(events)
        await save_events_to_db(events)
        LOGGER.info(f"Saved {len(events)} events from {crawler_func.__name__}")
    except Exception as e:
        LOGGER.error(f"❌ Error running {crawler_func.__name__}: {e}")

async def main():
    for crawler in CRAWLERS:
        await run_crawler(crawler)

if __name__ == "__main__":
    asyncio.run(main())