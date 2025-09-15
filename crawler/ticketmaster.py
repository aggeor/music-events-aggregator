import json
from datetime import datetime
from urllib.parse import urljoin

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy

from utils.helper import LOGGER

CURRENT_YEAR = datetime.now().year
BASE_URL = "https://www.ticketmaster.gr/_sce_category_s_Music.html"


def parse_ticketmaster_date(date_str: str):
    """Parse Ticketmaster date string into datetime object."""
    if not date_str:
        return None
    try:
        # Remove fractional seconds if present
        return datetime.strptime(date_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def fix_url(url: str, base: str = "https://www.ticketmaster.gr/"):
    """Convert relative URL to absolute."""
    return urljoin(base, url) if url else None


async def crawl_ticketmaster():
    LOGGER.info(f"Crawling ticketmaster.gr")
    LOGGER.info(f"URL: {BASE_URL}")

    # Extraction schema
    schema = {
        "name": "TicketmasterGR",
        "baseSelector": "div.event",
        "fields": [
            {"name": "title", "selector": "h3.evTitle", "type": "text"},
            {"name": "detailsUrl", "selector": "a", "type": "attribute", "attribute": "href"},
            {"name": "location", "type": "attribute", "attribute": "data-venue"},
            {"name": "start_date", "type": "attribute", "attribute": "data-start-date"},
            {"name": "end_date", "type": "attribute", "attribute": "data-end-date"},
            {"name": "imageUrl", "type": "attribute", "attribute": "data-image"},
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)
    config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS, extraction_strategy=extraction_strategy)

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=BASE_URL, config=config)

        if not result.success:
            LOGGER.error(f"Crawl failed: {result.error_message}")
            return []

        try:
            data = json.loads(result.extracted_content)
        except json.JSONDecodeError as e:
            LOGGER.error(f"JSON decode error: {e}")
            LOGGER.info(f"Raw extracted content: {result.extracted_content[:1000]}...")
            return []

        LOGGER.info(f"Found {len(data)} events")
        cleaned_data = []

        for i, event in enumerate(data):
            title = event.get('title', f'Unknown Event {i+1}').strip()
            location = event.get('location', 'Unknown').strip()

            start_date = parse_ticketmaster_date(event.get("start_date", ""))
            end_date = parse_ticketmaster_date(event.get("end_date", ""))

            if not start_date:
                LOGGER.warning(f"❌ Skipping event {title}: no valid start date")
                continue

            cleaned_event = {
                "title": title,
                "location": location,
                "start_date": start_date,
                "end_date": end_date,
                "detailsUrl": fix_url(event.get("detailsUrl", "").strip()),
                "imageUrl": fix_url(event.get("imageUrl", "").strip()),
                "sourceName": "ticketmaster.gr",
                "sourceUrl": BASE_URL
            }

            cleaned_data.append(cleaned_event)

        LOGGER.info(f"✅ Completed crawling ticketmaster.gr ({len(cleaned_data)} events parsed)")
        return cleaned_data
