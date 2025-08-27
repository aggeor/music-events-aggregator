import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

BASE_URL = "https://www.clubber.gr/events"

def parse_event_time(date_str, time_str):
    """Combine date string and time string into a datetime object."""
    if not time_str:
        return None
    try:
        # Parse date like 'Thu, 28 August'
        date_obj = datetime.strptime(date_str, "%a, %d %B")
        date_obj = date_obj.replace(year=datetime.now().year)
    except ValueError:
        return None
    
    # Combine date with time
    hour, minute = map(int, time_str.split(":"))
    date_obj = date_obj.replace(hour=hour, minute=minute)
    return date_obj


def adjust_end_date(start_dt, end_dt):
    # If end time is before start time, assume it's the next day.
    # Ex. if event starts at 27/8 23:00 and ends at 08:00 we assume the day for end date is 28/8
    if start_dt and end_dt and end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return end_dt

async def crawl_clubber():
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/137.0.0.0 Safari/537.36"
    }
    res = requests.get(BASE_URL, headers=headers)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    events = []
    current_date = None

    for element in soup.select(".em-events-list-grouped > *"):
        if element.name == "h2":
            current_date = element.get_text(strip=True)
            continue

        if element.name == "div" and "display: flex" in element.get("style", ""):
            img = element.select_one("img")
            title = element.select_one("b")
            title_tag = element.select_one("b")
            title = title_tag.get_text(strip=True) if title_tag else ""

            # Remove <b> tags from div
            for b in element.select("b"):
                b.decompose()
            
            # Extract location text: remove times
            location_text = element.get_text(separator=" ", strip=True)
            location = re.sub(r"\d{1,2}:\d{2}\s*–\s*\d{1,2}:\d{2}", "", location_text).strip()

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
                "detailsUrl": None,
            })
    print(f"\n✅ Extracted {len(events)} total entries")
    print(json.dumps(events, indent=2, default=serialize))
    return events

def serialize(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")
