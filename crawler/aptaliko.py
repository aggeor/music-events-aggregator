import re
import json
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy

from utils.helper import LOGGER

BASE_URL = "https://aptaliko.gr/search?contentType=EVENTS&groupPage=1&eventPage="
DOMAIN = "https://aptaliko.gr"


def parse_event_date(date_str: str) -> dict:
    """
    Parse a date string from aptaliko.gr and return a dict with 'start_date'/'end_date'.
    Supports:
      - ISO format
      - Date ranges (e.g., "Jun 25, 2025Jun 29, 2025")
      - Full date + time (e.g., "Jun 24, 2025, 7:30 PM")
      - Date only (e.g., "Jun 24, 2025")
    """
    date_str = date_str.strip()

    # ISO format
    try:
        dt = datetime.fromisoformat(date_str)
        return {"start_date": dt, "end_date": dt}
    except Exception:
        pass

    # Handle date range: "Jun 25, 2025Jun 29, 2025" or "Jul 14, 2025Jul 18, 2025"
    range_match = re.match(r"([A-Za-z]{3,}\s+\d{1,2},\s+\d{4})\s*([A-Za-z]{3,}\s+\d{1,2},\s+\d{4})", date_str)
    if range_match:
        try:
            start = datetime.strptime(range_match.group(1), "%b %d, %Y")
            end = datetime.strptime(range_match.group(2), "%b %d, %Y")
            return {"start_date": start, "end_date": end}
        except Exception as e:
            LOGGER.warning(f"⚠️ Could not parse date range '{date_str}': {e}")
            return {}

    # Date + time: "Jun 24, 2025, 7:30 PM"
    try:
        dt = datetime.strptime(date_str, "%b %d, %Y, %I:%M %p")
        return {"start_date": dt, "end_date": dt}
    except Exception:
        pass

    # Date only: "Jun 24, 2025" (no time)
    try:
        dt = datetime.strptime(date_str, "%b %d, %Y")
        return {"start_date": dt, "end_date": dt}
    except Exception:
        pass

    LOGGER.warning(f"⚠️ Could not parse date string: '{date_str}'")
    return {}


async def crawl_aptaliko():
    LOGGER.info("🌐 Crawling aptaliko.gr")

    page = 1
    all_events = []

    schema = {
        "name": "Aptaliko",
        "baseSelector": "a.mbz-card",
        "fields": [
            {"name": "title", "selector": "h2.text-2xl", "type": "text"},
            {"name": "date", "selector": "span.text-gray-700", "type": "text"},
            {"name": "location", "selector": "div.truncate", "type": "text"},
            {"name": "imageUrl", "selector": "img.transition-opacity", "type": "attribute", "attribute": "src"},
            {"name": "detailsUrl", "type": "attribute", "attribute": "href"},
        ],
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
        wait_for="css:a.mbz-card",
    )

    async with AsyncWebCrawler(verbose=True) as crawler:
        while True:
            url = f"{BASE_URL}{page}"
            LOGGER.debug(f"Fetching page {page}: {url}")

            # Fetch event data
            result = await crawler.arun(url=url, config=config)
            if not result.success:
                LOGGER.error(f"❌ Crawl failed on page {page}: {result.error_message}")
                break

            try:
                page_data = json.loads(result.extracted_content)
            except json.JSONDecodeError as e:
                LOGGER.error(f"❌ Failed to parse JSON on page {page}: {e}")
                break

            if not page_data or len(page_data) == 0:
                LOGGER.info(f"No more events found on page {page}, stopping.")
                break

            for event in page_data:
                # Fix relative URLs
                for key in ["imageUrl", "detailsUrl"]:
                    if event.get(key, "").startswith("/"):
                        event[key] = urljoin(DOMAIN, event[key])

                # Parse and normalize dates
                parsed = parse_event_date(event.get("date", ""))
                if parsed:
                    event["start_date"] = parsed["start_date"]
                    event["end_date"] = parsed["end_date"]
                else:
                    continue  # Skip invalid date
                if "date" in event:
                    event.pop("date", None)
                event["sourceName"] = "aptaliko.gr"
                event["sourceUrl"] = BASE_URL

            all_events.extend(page_data)

            # Check if there's a next page
            html_result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=None,
                    wait_for="css:button.o-pag__link.pagination-link.o-pag__next",
                ),
            )

            if not html_result.success:
                LOGGER.warning(f"⚠️ Failed to fetch pagination info on page {page}: {html_result.error_message}")
                break

            # raw_content is bytes, decode to str
            raw_html = html_result.fit_html
            soup = BeautifulSoup(raw_html, "html.parser")
            next_btn = soup.select_one("button.o-pag__link.pagination-link.o-pag__next")

            if not next_btn:
                LOGGER.info("No 'Next' button found, stopping crawl.")
                break

            classes = next_btn.get("class", [])
            if "o-pag__link--disabled" in classes or "pagination-link-disabled" in classes:
                LOGGER.info("Next button is disabled, stopping crawl.")
                break

            page += 1

    LOGGER.info(f"✅ Completed crawling aptaliko.gr — {len(all_events)} events found")
    return all_events
