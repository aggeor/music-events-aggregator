import asyncio
import sys
import os

from crawler.athinorama import crawl_athinorama
from crawler.iereies_tis_nychtas import crawl_iereies
from crawler.aptaliko import crawl_aptaliko
from crawler.clubber import crawl_clubber
from crawler.more_com import crawl_more_com
from crawler.ticketmaster import crawl_ticketmaster
from crawler.ticketservices import crawl_ticketservices
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
    crawl_ticketservices
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

async def run_with_timeout(timeout_minutes: int = 30):
    """Run main with a timeout; restart script if timeout is reached."""
    while True:
        try:
            await asyncio.wait_for(main(), timeout=timeout_minutes * 60)
            break  # finished successfully
        except asyncio.TimeoutError:
            LOGGER.warning(f"⚠️ Crawlers took more than {timeout_minutes} minutes. Restarting...")
            # Option 1: restart program in-place
            python = sys.executable
            LOGGER.info("Restarting script from scratch...")
            # Note: This replaces the current process with a new one
            os.execv(python, [python] + sys.argv)

if __name__ == "__main__":
    asyncio.run(run_with_timeout())
