import re
from datetime import datetime
from urllib.parse import urljoin
import json

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy
from bs4 import BeautifulSoup

from utils.helper import LOGGER

CURRENT_YEAR = datetime.now().year

BASE_URL = "https://www.athinorama.gr/music/guide"

# Greek time mapping
def convert_greek_time_to_24h(time_str):
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

async def crawl_athinorama():
    LOGGER.info(f"Crawling athinorama.gr")
    LOGGER.info(f"URL: "+BASE_URL)
    schema = {
        "name": "Athinorama",
        "baseSelector": "div.guide-list div.item",
        "fields": [
            {"name": "title", "selector": "h2.item-title", "type": "text"},
            {"name": "summary_raw", "selector": "div.item-content", "type": "html"},
            {"name": "location", "selector": "div.item-description h4 a", "type": "text"},
            {"name": "detailsUrl", "selector": "h2.item-title a", "type": "attribute", "attribute": "href"},
        ]
    }

    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
    )

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=BASE_URL,
            config=config
        )

        if not result.success:
            print("Crawl failed:", result.error_message)
            return

        data = json.loads(result.extracted_content)
        cleaned_data = []

        for event in data:
            html_summary = event.get("summary_raw", "")
            location = event.get("location", "").strip()

            soup = BeautifulSoup(html_summary, "html.parser")
            summary_with_date = soup.find("p", class_="summary", style=lambda s: s and "display:block" in s)

            if not summary_with_date:
                print(f"Missing styled summary with date in: {html_summary}")
                continue

            strong_tag = summary_with_date.find("strong")
            date_str = strong_tag.text.strip() if strong_tag else None
            text_after_strong = strong_tag.next_sibling if strong_tag else ""

            if not date_str:
                print(f"Missing date in: {summary_with_date}")
                continue

            # Extract time from text after <strong>
            time_match = re.search(r"(\d{1,2}(?:[:.]\d{2})?\s*(?:π\.μ\.|μ\.μ\.))", text_after_strong or "")
            time_str = convert_greek_time_to_24h(time_match.group(1)) if time_match else "21:00"

            datetime_str = f"{date_str} {time_str} {CURRENT_YEAR}"
            try:
                dt = datetime.strptime(datetime_str, "%d/%m %H:%M %Y")
                event["start_date"] = dt
                event["end_date"] = dt
            except ValueError:
                print(f"Could not parse datetime: {datetime_str}")
                continue

            event["location"] = location
            event["imageUrl"] = None

            if event.get("detailsUrl", "").startswith("/"):
                event["detailsUrl"] = urljoin("https://www.athinorama.gr/", event["detailsUrl"])

            # Remove raw HTML content to keep output clean
            event.pop("summary_raw", None)

            cleaned_data.append(event)
        
        LOGGER.info(f"✅ Completed crawling athinorama.gr")
        return cleaned_data
