import re
import json
from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode, JsonCssExtractionStrategy

from utils.helper import LOGGER

CURRENT_YEAR = datetime.now().year
BASE_URL = "https://www.athinorama.gr/music/guide"


def convert_greek_time_to_24h(time_str: str) -> str:
    """Convert Greek AM/PM times into 24h format."""
    match = re.search(r"(\d{1,2})(?:[:\.](\d{2}))?\s*(π\.μ\.|μ\.μ\.)", time_str)
    if not match:
        return "21:00"  # default fallback

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = match.group(3)

    if meridiem == "μ.μ." and hour != 12:
        hour += 12
    elif meridiem == "π.μ." and hour == 12:
        hour = 0

    return f"{hour:02}:{minute:02}"


def parse_event_datetime(summary_html: str) -> tuple[datetime | None, datetime | None]:
    """Extract datetime from Athinorama summary HTML."""
    soup = BeautifulSoup(summary_html, "html.parser")
    summary_with_date = soup.find("p", class_="summary", style=lambda s: s and "display:block" in s)

    if not summary_with_date:
        LOGGER.warning(f"Missing styled summary with date in HTML: {summary_html[:80]}...")
        return None, None

    strong_tag = summary_with_date.find("strong")
    date_str = strong_tag.get_text(strip=True) if strong_tag else None
    text_after_strong = strong_tag.next_sibling if strong_tag else ""

    if not date_str:
        LOGGER.warning(f"Missing date in summary: {summary_with_date}")
        return None, None

    time_match = re.search(r"(\d{1,2}(?::\d{2}|.\d{2})?\s*(?:π\.μ\.|μ\.μ\.))", text_after_strong or "")
    time_str = convert_greek_time_to_24h(time_match.group(1)) if time_match else "21:00"

    datetime_str = f"{date_str} {time_str} {CURRENT_YEAR}"
    try:
        dt = datetime.strptime(datetime_str, "%d/%m %H:%M %Y")
        return dt, dt
    except ValueError:
        LOGGER.warning(f"Could not parse datetime: {datetime_str}")
        return None, None


async def crawl_athinorama():
    LOGGER.info(f"Crawling athinorama.gr")
    LOGGER.info(f"URL: {BASE_URL}")

    schema = {
        "name": "Athinorama",
        "baseSelector": "div.guide-list div.item",
        "fields": [
            {"name": "title", "selector": "h2.item-title", "type": "text"},
            {"name": "summary_raw", "selector": "div.item-content", "type": "html"},
            {"name": "location", "selector": "div.item-description h4 a", "type": "text"},
            {"name": "detailsUrl", "selector": "h2.item-title a", "type": "attribute", "attribute": "href"},
        ],
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)
    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
    )

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(url=BASE_URL, config=config)
        if not result.success:
            LOGGER.error(f"Crawl failed: {result.error_message}")
            return []

        data = json.loads(result.extracted_content)
        cleaned_data = []

        for event in data:
            start_date, end_date = parse_event_datetime(event.get("summary_raw", ""))

            if not start_date:
                continue

            details_url = event.get("detailsUrl", "")
            if details_url.startswith("/"):
                details_url = urljoin("https://www.athinorama.gr/", details_url)

            cleaned_data.append({
                "title": event.get("title", "").strip(),
                "location": event.get("location", "").strip(),
                "start_date": start_date,
                "end_date": end_date,
                "imageUrl": None,  # not provided
                "detailsUrl": details_url,
                "sourceName": "athinorama.gr",
                "sourceUrl": BASE_URL,
            })

        LOGGER.info(f"✅ Completed crawling athinorama.gr ({len(cleaned_data)} events)")
        return cleaned_data
