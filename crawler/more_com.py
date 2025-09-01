import asyncio
from datetime import datetime, timedelta
from urllib.parse import urljoin
from playwright.async_api import async_playwright

from utils.helper import LOGGER

BASE_URL = "https://www.more.com/gr-el/tickets/music/"

CURRENT_YEAR = datetime.now().year

GREEK_MONTHS = {
    "ΙΑΝΟΥΑΡΙΟΥ": 1, "ΦΕΒΡΟΥΑΡΙΟΥ": 2, "ΜΑΡΤΙΟΥ": 3, "ΑΠΡΙΛΙΟΥ": 4,
    "ΜΑΙΟΥ": 5, "ΙΟΥΝΙΟΥ": 6, "ΙΟΥΛΙΟΥ": 7, "ΑΥΓΟΥΣΤΟΥ": 8,
    "ΣΕΠΤΕΜΒΡΙΟΥ": 9, "ΟΚΤΩΒΡΙΟΥ": 10, "ΝΟΕΜΒΡΙΟΥ": 11, "ΔΕΚΕΜΒΡΙΟΥ": 12
}

ENGLISH_MONTHS = {
    "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4,
    "MAY": 5, "JUNE": 6, "JULY": 7, "AUGUST": 8,
    "SEPTEMBER": 9, "OCTOBER": 10, "NOVEMBER": 11, "DECEMBER": 12
}

async def scroll_until_footer(page, pause=0.8):
    footer_selector = "div.footer__copyright"
    while True:
        footer_visible = await page.evaluate(f"""
            () => {{
                const el = document.querySelector("{footer_selector}");
                if (!el) return false;
                const rect = el.getBoundingClientRect();
                return rect.top <= window.innerHeight;
            }}
        """)
        if footer_visible:
            break
        await page.mouse.wheel(0, 400)
        await asyncio.sleep(pause)

# Find substring of month in GREEK_MONTHS
# ex. ΣΕΠ in ΣΕΠΤΕΜΒΡΙΟΥ
def find_greek_month(substring: str):
    """Return month number by matching substring with Greek month names."""
    substring = substring.upper()
    for month_name, month_num in GREEK_MONTHS.items():
        if substring in month_name:
            return month_num
    return None

def parse_greek_date(date_text: str):
    """Parse a date string like '5 - 6 Σεπτεμβριου' or '18 Σεπτεμβριου' into start and end datetime objects."""
    date_text = date_text.replace("\xa0", " ").strip()
    parts = date_text.split()
    
    if len(parts) == 2 and "/" not in parts[1]:  # single-day format: "18 Σεπτεμβριου"
        day = int(parts[0])
        month = GREEK_MONTHS.get(parts[1])
        if month:
            dt = datetime(CURRENT_YEAR, month, day)
            return dt, dt
    elif len(parts) == 2 and "/" in parts[1]:
        date = parts[1].split("/")
        day = int(date[0])
        month = int(date[1])
        dt = datetime(CURRENT_YEAR, month, day)
        return dt, dt
    elif len(parts) == 4 and parts[1] in ["-", "–"]:  # range format: "5 - 6 Σεπτεμβριου"
        start_day = int(parts[0])
        end_day = int(parts[2])
        month = GREEK_MONTHS.get(parts[3])
        if month:
            start_dt = datetime(CURRENT_YEAR, month, start_day)
            end_dt = datetime(CURRENT_YEAR, month, end_day)
            return start_dt, end_dt

    # Special case for Rock Hard Festival Greece
    elif len(parts) == 4 and parts[1] in ["&"]:  # range format: "12 & 13 September"
        start_day = int(parts[0])
        end_day = int(parts[2])
        month = ENGLISH_MONTHS.get(parts[3])
        if month:
            start_dt = datetime(CURRENT_YEAR, month, start_day)
            end_dt = datetime(CURRENT_YEAR, month, end_day)
            return start_dt, end_dt
    elif len(parts) == 5 and parts[2] in ["-", "–"]: # range format: "12 Νοε - 3 Δεκ"
        start_day = int(parts[0])
        start_month = find_greek_month(parts[1])
        end_day = int(parts[3])
        end_month = find_greek_month(parts[4])
        if start_month and end_month:
            start_dt = datetime(CURRENT_YEAR,start_month,start_day)
            end_year = CURRENT_YEAR
            if end_month<start_month:
                end_year+=1
            end_dt = datetime(end_year,end_month,end_day)
            return start_dt, end_dt
    return None, None

async def crawl_more_com():
    LOGGER.info(f"Crawling more.com")
    LOGGER.info(f"URL: "+BASE_URL)
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-http2", "--disable-blink-features=AutomationControlled"]
        )
        page = await browser.new_page()

        await page.goto(BASE_URL, wait_until="domcontentloaded")

        # Accept cookies automatically
        try:
            cookie_button = await page.wait_for_selector("a.cc-btn.cc-btn--accept", timeout=10000)
            if cookie_button:
                await cookie_button.click()
                await asyncio.sleep(1)
        except:
            pass

        # Scroll until footer
        await scroll_until_footer(page, pause=0.8)

        await page.wait_for_selector("aside.playimage img[src*='/getattachment/']", timeout=10000)

        events = await page.query_selector_all("a.play-template__main")
        results = []

        # Get data
        for event_el in events:
            title_el = await event_el.query_selector("h3.playinfo__title")
            title = await title_el.inner_text() if title_el else None

            loc_el = await event_el.query_selector("div.playinfo__venue")
            location = await loc_el.inner_text() if loc_el else None

            details_url = await event_el.get_attribute("href")

            img_el = await event_el.query_selector("aside.playimage img")
            image_url = await img_el.get_attribute("src") if img_el else None

            date_el = await event_el.query_selector("time.playinfo__date")
            date_text = await date_el.inner_text() if date_el else ""
            start_date, end_date = parse_greek_date(date_text)

            if details_url and details_url.startswith("/"):
                details_url = urljoin("https://www.more.com", details_url)
            if image_url and image_url.startswith("/"):
                image_url = urljoin("https://www.more.com", image_url)

            results.append({
                "title": title,
                "location": location,
                "detailsUrl": details_url,
                "imageUrl": image_url,
                "start_date": start_date,
                "end_date": end_date,
                "sourceName": "more.com",
                "sourceUrl" : BASE_URL
            })

        await browser.close()

        LOGGER.info(f"✅ Completed crawling more.com")
        return results