import re
import json
from datetime import datetime
from urllib.parse import urljoin

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy

from utils.helper import LOGGER

BASE_URL = "https://iereiestisnychtas.com/musicevents"
DOMAIN = "https://iereiestisnychtas.com"
CURRENT_YEAR = datetime.now().year


async def crawl_iereies():
    LOGGER.info("🌐 Crawling iereiestisnychtas.com")
    LOGGER.debug(f"URL: {BASE_URL}")

    schema = {
        "name": "Iereies",
        "baseSelector": "a.flex-events-a",
        "fields": [
            {"name": "title", "selector": "div.flex-eventsinfo-h h2", "type": "text"},
            {"name": "start_date", "selector": "div.flex-eventsinfo-p", "type": "text"},
            {"name": "end_date", "selector": "div.flex-eventsinfo-p", "type": "text"},
            {"name": "location", "selector": "div.flex-eventsinfo-more-details", "type": "text"},
            {"name": "imageUrl", "selector": "div.flex-eventsimg img", "type": "attribute", "attribute": "src"},
            {"name": "detailsUrl", "selector": "div.btn", "type": "attribute", "attribute": "href"},
        ],
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
    )

    events = []
    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=BASE_URL, config=config)

        if not result.success:
            LOGGER.error(f"❌ Crawl failed for {BASE_URL}: {result.error_message}")
            return []

        try:
            raw_data = json.loads(result.extracted_content)
        except json.JSONDecodeError as e:
            LOGGER.error(f"❌ Failed to parse extracted JSON: {e}")
            return []

        for event in raw_data:
            # Fix image URLs
            if event.get("imageUrl", "").startswith("/"):
                event["imageUrl"] = urljoin(DOMAIN, event["imageUrl"])

            # Extract time from location
            time = None
            match = re.match(r"(\d{1,2}:\d{2})(.+)", event.get("location", ""))
            if match:
                time = match.group(1)
                event["location"] = match.group(2).strip()
            else:
                time = event.get("location", "")
                event["location"] = ""

            # Clean weekday from date (e.g. "SUN 27/07" → "27/07")
            date_str = re.sub(r"^\w+\s+", "", event.get("start_date", "")).strip()
            datetime_str = f"{date_str} {time} {CURRENT_YEAR}" # e.g., "27/07 17:30 2025"

            try:
                parsed_date = datetime.strptime(datetime_str, "%d/%m %H:%M %Y")
                event["start_date"] = parsed_date
                event["end_date"] = parsed_date
            except ValueError:
                LOGGER.warning(f"⚠️ Could not parse date: {datetime_str}")
                continue

            # Fix details URL
            if event.get("detailsUrl", "").startswith("/"):
                event["detailsUrl"] = urljoin(DOMAIN, event["detailsUrl"])

            # Add metadata
            event["sourceName"] = "iereiestisnychtas.com"
            event["sourceUrl"] = BASE_URL

            events.append(event)

    LOGGER.info(f"✅ Completed crawling iereiestisnychtas.com — {len(events)} events found")
    return events
