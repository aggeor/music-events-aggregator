
import re
from datetime import datetime
from urllib.parse import urljoin
import json

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy


CURRENT_YEAR = datetime.now().year

async def iereies():
    # 1. Define a simple extraction schema
    schema = {
        "name": "Iereies",
        "baseSelector": "a.flex-events-a",    # Repeated elements
        "fields": [
            {
                "name": "title",  # The output key
                "selector": "div.flex-eventsinfo-h h2",
                "type": "text"
            },
            {
                "name": "date",
                "selector": "div.flex-eventsinfo-p",
                "type": "text"
            },
            {
                "name": "location",
                "selector": "div.flex-eventsinfo-more-details",
                "type": "text"
            },
            {
                "name": "imageUrl",
                "selector":"div.flex-eventsimg img",
                "type": "attribute",
                "attribute": "src"
            },
            {
                "name": "detailsUrl",
                "selector":"div.btn",
                "type":"attribute",
                "attribute": "href"
            }
        ]
    }

    # 2. Create the extraction strategy
    extraction_strategy = JsonCssExtractionStrategy(schema, verbose=True)

    # 3. Set up your crawler config (if needed)
    config = CrawlerRunConfig(
        # e.g., pass js_code or wait_for if the page is dynamic
        # wait_for="css:.crypto-row:nth-child(20)"
        cache_mode = CacheMode.BYPASS,
        extraction_strategy=extraction_strategy,
    )

    async with AsyncWebCrawler(verbose=True) as crawler:
        # 4. Run the crawl and extraction
        result = await crawler.arun(
            url="https://iereiestisnychtas.com/musicevents",
            config=config
        )

        if not result.success:
            print("Crawl failed:", result.error_message)
            return

        # 5. Parse the extracted JSON
        data = json.loads(result.extracted_content)
        for event in data:
            # Ensure full image URL
            if event.get("imageUrl", "").startswith("/"):
                event["imageUrl"] = urljoin("https://iereiestisnychtas.com", event["imageUrl"])

            # Extract time from location
            match = re.match(r"(\d{1,2}:\d{2})(.+)", event["location"])
            if match:
                time = match.group(1)  # e.g., "17:30"
                location = match.group(2).strip()
                event["location"] = location
            else:
                time = event["location"]  # Default fallback time if location not found
                event["location"] = "" # Add empty location

            # Clean weekday (e.g., "SUN 27/07" → "27/07")
            date_str = re.sub(r"^\w+\s+", "", event["date"]).strip()

            # Combine with time
            datetime_str = f"{date_str} {time} {CURRENT_YEAR}"  # e.g., "27/07 17:30 2025"
            
            try:
                parsed_date = datetime.strptime(datetime_str, "%d/%m %H:%M %Y")
                event["date"] = parsed_date
            except ValueError:
                print(f"Could not parse date: {datetime_str}")
                continue  # Skip if invalid
            # Add detailsUrl
            if event.get("detailsUrl", "").startswith("/"):
                event["detailsUrl"] = urljoin("https://iereiestisnychtas.com", event["detailsUrl"])
        print(f"Extracted {len(data)} entries")
        print(json.dumps(data, indent=2, default=serialize) if data else "No data found")
        return data


def serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")