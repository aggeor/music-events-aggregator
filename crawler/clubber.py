import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from utils.helper import LOGGER

BASE_URL = "https://www.clubber.gr/events"


def parse_event_time(date_str: str, time_str: str) -> datetime | None:
    """Combine date string and time string into a datetime object."""
    if not (date_str and time_str):
        return None
    try:
        # Example: 'Thu, 28 August'
        date_obj = datetime.strptime(date_str, "%a, %d %B").replace(year=datetime.now().year)
        hour, minute = map(int, time_str.split(":"))
        return date_obj.replace(hour=hour, minute=minute)
    except (ValueError, AttributeError):
        return None


def adjust_end_date(start_dt: datetime | None, end_dt: datetime | None) -> datetime | None:
    """If end time is before start time, assume it's the next day."""
    if start_dt and end_dt and end_dt <= start_dt:
        return end_dt + timedelta(days=1)
    return end_dt


async def crawl_clubber():
    LOGGER.info(f"Crawling clubber.gr")
    LOGGER.info(f"URL: {BASE_URL}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/137.0.0.0 Safari/537.36"
        )
    }

    try:
        res = requests.get(BASE_URL, headers=headers, timeout=15)
        res.raise_for_status()
    except requests.RequestException as e:
        LOGGER.error(f"❌ Failed to fetch {BASE_URL}: {e}")
        return []

    soup = BeautifulSoup(res.text, "html.parser")
    events = []
    current_date = None

    for element in soup.select(".em-events-list-grouped > *"):
        # Update current date when an <h2> is found
        if element.name == "h2":
            current_date = element.get_text(strip=True)
            continue

        # Each event block is a styled <div>
        if element.name == "div" and "display: flex" in element.get("style", ""):
            img = element.select_one("img")
            title_tag = element.select_one("b")
            title = title_tag.get_text(strip=True) if title_tag else ""

            # Clean up inline <b> tags so they don’t leak into location
            for b in element.select("b"):
                b.decompose()

            # Extract location (remove any time ranges)
            location_text = element.get_text(separator=" ", strip=True)
            location = re.sub(r"\d{1,2}:\d{2}\s*–\s*\d{1,2}:\d{2}", "", location_text).strip()

            # Extract time range
            time_match = re.search(r"(\d{1,2}:\d{2})\s*–\s*(\d{1,2}:\d{2})", element.get_text())
            start_str, end_str = time_match.groups() if time_match else (None, None)

            start_dt = parse_event_time(current_date, start_str)
            end_dt = parse_event_time(current_date, end_str)
            end_dt = adjust_end_date(start_dt, end_dt)

            events.append({
                "title": title,
                "start_date": start_dt,
                "end_date": end_dt,
                "location": location,
                "imageUrl": img["src"] if img else None,
                "detailsUrl": None,  # clubber doesn't have per-event pages
                "sourceName": "clubber.gr",
                "sourceUrl": BASE_URL,
            })

    LOGGER.info(f"✅ Completed crawling clubber.gr ({len(events)} events)")
    return events
