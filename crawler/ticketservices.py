import json
from datetime import datetime
from urllib.parse import urljoin
import re
from bs4 import BeautifulSoup

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from utils.helper import LOGGER

BASE_URL = "https://www.ticketservices.gr/en/LiveConcerts/"


def parse_ticketservices_dates(data_dates: str):
    """Parse TicketServices data-dates attribute into start and end datetime."""
    if not data_dates:
        return None, None

    # Split by | for multi-day events
    date_parts = data_dates.split("|")
    parsed_dates = []
    for part in date_parts:
        try:
            parsed_dates.append(datetime.strptime(part.strip(), "%Y-%m-%d").replace(hour=21))
        except Exception:
            continue

    if not parsed_dates:
        return None, None

    return parsed_dates[0], parsed_dates[-1]  # start_date, end_date



async def crawl_ticketservices():
    LOGGER.info(f"Crawling ticketservices.gr")
    LOGGER.info(f"URL: {BASE_URL}")

    schema = {
        "name": "TicketServicesGR",
        "baseSelector": "li.event",
        "fields": [
            {"name": "title", "type": "attribute", "attribute": "data-title"},
            {"name": "detailsUrl", "selector": "a", "type": "attribute", "attribute": "href"},
            {"name": "location", "type": "attribute", "attribute": "data-venues"},
            {"name": "dates", "type": "attribute", "attribute": "data-dates"},
            {"name": "imageUrl", "selector": "img", "type": "attribute", "attribute": "src"},
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

        cleaned_data = []
        for i, event in enumerate(data):
            # Clean title (remove HTML / <br>)
            title_html = event.get("title", f"Unknown Event {i+1}")
            title = BeautifulSoup(title_html, "html.parser").get_text(separator=" ").strip()

            # Clean location
            location = event.get("location", "").strip()

            # Parse dates
            data_dates = event.get("dates", "")  # 'dates' comes from data-dates attribute
            start_date, end_date = parse_ticketservices_dates(data_dates)

            cleaned_event = {
                "title": title,
                "location": location,
                "start_date": start_date,
                "end_date": end_date,
                "detailsUrl": urljoin(BASE_URL, event.get("detailsUrl", "").strip()),
                "imageUrl": urljoin(BASE_URL, event.get("imageUrl", "").strip()),
                "sourceName": "ticketservices.gr",
                "sourceUrl": BASE_URL,
            }
            cleaned_data.append(cleaned_event)

        LOGGER.info(f"✅ Completed crawling ticketservices.gr ({len(cleaned_data)} events parsed)")
        return cleaned_data
