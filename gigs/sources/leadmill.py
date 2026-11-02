"""The Leadmill comedy listings (Steamworks, Foundry, Sheffield Plate, ...).

Uses the site's Events Calendar REST API, which is paginated (the HTML page
only shows the first 50).
"""
import html
import json
import re
from datetime import datetime

from ..http import get
from ..model import Event

NAME = "leadmill"
API = "https://leadmill.co.uk/wp-json/tribe/events/v1/events?categories=comedy&per_page=50&page={}"
MAX_PAGES = 10

# Leadmill appends the venue to act names, e.g. "Finlay Christie (The Steamworks)".
_VENUE_SUFFIX = re.compile(
    r"\s*\((?=[^)]*(foundry|steamworks|bar one|sheffield|peddler|matinee))[^)]*\)\s*$",
    re.I,
)
_MATINEE = re.compile(r"\s*[–-]\s*matinee$", re.I)


def fetch() -> list[Event]:
    events: dict[str, Event] = {}
    page, total_pages = 1, 1
    while page <= min(total_pages, MAX_PAGES):
        data = json.loads(get(API.format(page)))
        total_pages = data.get("total_pages", 1)
        for item in data["events"]:
            url = item["url"]
            title = _VENUE_SUFFIX.sub("", html.unescape(item["title"])).strip()
            image = item.get("image")
            events[url] = Event(
                title=_MATINEE.sub("", title),
                start=datetime.fromisoformat(item["start_date"]),
                venue=html.unescape((item.get("venue") or {}).get("venue") or "Leadmill"),
                url=url,
                source=NAME,
                image=image["url"] if isinstance(image, dict) else None,
            )
        page += 1
    return list(events.values())
