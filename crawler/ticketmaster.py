import json
from datetime import datetime
from urllib.parse import urljoin

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy

from utils.helper import LOGGER

CURRENT_YEAR = datetime.now().year
BASE_URL = "https://www.ticketmaster.gr/_sce_category_s_Music.html"

async def crawl_ticketmaster():
    LOGGER.info(f"Crawling ticketmaster.gr")
    LOGGER.info(f"URL: {BASE_URL}")

    # Schema: keep only top-level properties
    schema = {
        "name": "TicketmasterGR",
        "baseSelector": "div.event",
        "fields": [
            {"name": "title", "selector": "h3.evTitle", "type": "text"},
            {"name": "detailsUrl", "selector": "a", "type": "attribute", "attribute": "href"},
            {"name": "location","type": "attribute", "attribute": "data-venue"},
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
            event_title = event.get('title', f'Unknown Event {i+1}')

            # Parse dates
            start_date = None
            end_date = None

            try:
                start_date_str = event.get("start_date", "").strip()
                end_date_str = event.get("end_date", "").strip()

                if start_date_str:
                    start_date = datetime.strptime(start_date_str.split('.')[0], "%Y-%m-%d %H:%M:%S")
                if end_date_str:
                    end_date = datetime.strptime(end_date_str.split('.')[0], "%Y-%m-%d %H:%M:%S")

            except Exception as e:
                LOGGER.warning(f"Could not parse dates for event {event_title}: {e}")

            # Skip events without start date
            if not start_date:
                LOGGER.warning(f"❌ Skipping event {event_title}: no valid start date found")
                continue

            # Clean up top-level event data
            cleaned_event = {
                "title": event.get("title", "").strip(),
                "location": event.get("location", "").strip(),
                "start_date": start_date,
                "end_date": end_date
            }

            # Fix relative URLs
            details_url = event.get("detailsUrl", "").strip()
            if details_url:
                cleaned_event["detailsUrl"] = urljoin("https://www.ticketmaster.gr/", details_url)

            image_url = event.get("imageUrl", "").strip()
            if image_url:
                cleaned_event["imageUrl"] = urljoin("https://www.ticketmaster.gr/", image_url)
            
            cleaned_event["sourceName"] = "ticketmaster.gr"
            cleaned_event["sourceUrl"] = BASE_URL

            cleaned_data.append(cleaned_event)
        return cleaned_data
