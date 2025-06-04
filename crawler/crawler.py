
from urllib.parse import urljoin
import json

from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai import JsonCssExtractionStrategy


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
                "name": "image",
                "selector":"div.flex-eventsimg img",
                "type": "attribute",
                "attribute": "src"
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
            if "image" in event and event["image"].startswith("/"):
                event["image"] = urljoin("https://iereiestisnychtas.com", event["image"])
        # print(data)
        print(f"Extracted {len(data)} entries")
        print(json.dumps(data, indent=2) if data else "No data found")