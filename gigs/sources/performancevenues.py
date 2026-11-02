"""University of Sheffield Performance Venues: Octagon Centre, Firth Hall, ...

The events API has no genre, but each event page carries a category label
(<a class="comedy" ...>), so comedy is picked out by reading the page once
and remembering the answer in state/performancevenues_comedy.json.
"""
import html
import json
import re
import time
from datetime import datetime
from pathlib import Path

from ..http import get
from ..model import Event, act_of

NAME = "performancevenues"
API = (
    "https://performancevenues.group.shef.ac.uk/wp-json/wp/v2/our-events"
    "?per_page=100&_fields=link,title,acf,yoast_head_json"
)
CACHE = Path(__file__).resolve().parents[2] / "state" / "performancevenues_comedy.json"

_DATE = re.compile(r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+),?\s+(\d{4})")
_TIME = re.compile(r"(\d{1,2})(?:[:.](\d{2}))?\s*(am|pm)", re.I)
_DATE_FIELDS = ("dates", "dates_second", "dates_third", "dates_fourth", "dates_fifth", "dates_sixth")


def _is_comedy(link: str, cache: dict[str, bool]) -> bool:
    if link not in cache:
        page = get(link)
        cache[link] = bool(re.search(r'<a class="comedy"', page))
        time.sleep(0.5)
    return cache[link]


def _start(date_text: str, time_text: str) -> datetime | None:
    d = _DATE.search(date_text or "")
    if not d:
        return None
    try:
        day = datetime.strptime(f"{d[1]} {d[2]} {d[3]}", "%d %B %Y")
    except ValueError:
        return None
    t = _TIME.search(time_text or "")
    if t:
        hour = int(t[1]) % 12 + (12 if t[3].lower() == "pm" else 0)
        day = day.replace(hour=hour, minute=int(t[2] or 0))
    return day


_RECORDS: list | None = None


def _records() -> list:
    global _RECORDS
    if _RECORDS is None:
        _RECORDS = json.loads(get(API))
    return _RECORDS


def university_pages() -> dict[tuple[str, str], str]:
    """(date, act) -> University event page, for every listed event (some carry a placeholder venue)."""
    pages: dict[tuple[str, str], str] = {}
    for item in _records():
        acf = item.get("acf") or {}
        act = act_of(html.unescape(item["title"]["rendered"]))
        for field in _DATE_FIELDS:
            start = _start(acf.get(field, ""), "")
            if start:
                pages[(start.date().isoformat(), act)] = item["link"]
    return pages


def fetch() -> list[Event]:
    cache: dict[str, bool] = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    events: list[Event] = []
    for item in _records():
        acf = item.get("acf") or {}
        link = item["link"]
        starts = [s for f in _DATE_FIELDS if (s := _start(acf.get(f, ""), acf.get("time", "")))]
        if not starts or not _is_comedy(link, cache):
            continue
        og = (item.get("yoast_head_json") or {}).get("og_image") or []
        cost = (acf.get("cost") or "").strip()
        for start in starts:
            events.append(
                Event(
                    title=html.unescape(item["title"]["rendered"]).strip(),
                    start=start,
                    venue=acf.get("venue23") or "Octagon Centre",
                    url=link,
                    source=NAME,
                    image=og[0]["url"] if og else None,
                    price=cost or None,
                )
            )
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1, sort_keys=True))
    return events
