import re
from datetime import datetime
from urllib.parse import urljoin
import json
from bs4 import BeautifulSoup

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy

from typing import Optional

def parse_event_date(date_str: str) -> dict:
    """
    Parse a date string from aptaliko.gr and return a dict with 'date' or 'start_date'/'end_date'.
    """
    date_str = date_str.strip()
    # Handle ISO format
    try:
        dt = datetime.fromisoformat(date_str)
        return {"date": dt}
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
            print(f"Could not parse date range: {date_str} - Error: {e}")
            return {}

    # Handle "Jun 24, 2025, 7:30 PM"
    try:
        dt = datetime.strptime(date_str, "%b %d, %Y, %I:%M %p")
        return {"date": dt}
    except Exception:
        pass

    # Handle "Jun 24, 2025" (no time)
    try:
        dt = datetime.strptime(date_str, "%b %d, %Y")
        return {"date": dt}
    except Exception:
        pass

    print(f"Could not parse date string: {date_str}")
    return {}


async def crawl_aptaliko():
    base_url = "https://aptaliko.gr/search?contentType=EVENTS&groupPage=1&eventPage="
    page = 1
    all_data = []

    # Schema to extract events data only (no rawHtml here)
    schema = {
        "name": "Aptaliko",
        "baseSelector": "a.mbz-card",
        "fields": [
            {"name": "title", "selector": "h2.text-2xl", "type": "text"},
            {"name": "date", "selector": "span.text-gray-700", "type": "text"},
            {"name": "location", "selector": "div.truncate", "type": "text"},
            {"name": "imageUrl", "selector": "img.transition-opacity", "type": "attribute", "attribute": "src"},
            {"name": "detailsUrl", "type": "attribute", "attribute": "href"},
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
        wait_for="css:a.mbz-card",
    )

    async with AsyncWebCrawler(verbose=True) as crawler:
        while True:
            url = f"{base_url}{page}"
            print(f"Fetching page {page}: {url}")

            # Fetch event data
            result = await crawler.arun(url=url, config=config)
            if not result.success:
                print(f"Crawl failed on page {page}: {result.error_message}")
                break

            page_data = json.loads(result.extracted_content)
            if not page_data or len(page_data) == 0:
                print(f"No more events found on page {page}. Stopping.")
                break

            # Fix URLs and parse dates
            for event in page_data:
                for key in ["imageUrl", "detailsUrl"]:
                    if event.get(key, "").startswith("/"):
                        event[key] = urljoin("https://aptaliko.gr", event[key])
                # Parse date(s)
                parsed = parse_event_date(event["date"])
                if "date" in parsed:
                    event["start_date"] = parsed["date"]
                    event["end_date"] = parsed["date"]
                elif "start_date" in parsed and "end_date" in parsed:
                    event["start_date"] = parsed["start_date"]
                    event["end_date"] = parsed["end_date"]
                else:
                    continue
                # Remove the original 'date' field
                if "date" in event:
                    del event["date"]

            all_data.extend(page_data)

            # Fetch raw page HTML separately to check "Next" button status
            html_result = await crawler.arun(
                url=url,
                config=CrawlerRunConfig(
                    cache_mode=CacheMode.BYPASS,
                    extraction_strategy=None,  # No extraction, raw HTML
                    wait_for="css:button.o-pag__link.pagination-link.o-pag__next",
                )
            )
            if not html_result.success:
                print(f"Failed to get page HTML on page {page}: {html_result.error_message}")
                break

            # raw_content is bytes, decode to str
            raw_html = html_result.fit_html
            soup = BeautifulSoup(raw_html, "html.parser")

            next_btn = soup.select_one("button.o-pag__link.pagination-link.o-pag__next")
            if next_btn is None:
                print("Next button not found, stopping crawl.")
                break

            classes = next_btn.get("class", [])
            if "o-pag__link--disabled" in classes or "pagination-link-disabled" in classes:
                print("Next button is disabled, stopping crawl.")
                break

            page += 1
    return all_data