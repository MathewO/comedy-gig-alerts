"""Sheffield Theatres comedy category (Montgomery, Playhouse, Lyceum, Crucible).

Each card carries its start (and, for runs, end) time as <time datetime=...>.
"""
import html
import re
import time
from datetime import datetime

from ..http import get
from ..model import Event

NAME = "theatres"
URL = "https://www.sheffieldtheatres.co.uk/whats-on/category/comedy"
MAX_PAGES = 10
# The category also lists comic plays and musicals; stand-up plays the Montgomery.
VENUES = {"Montgomery Theatre"}

_CARD = re.compile(
    r'<a href="(https://www\.sheffieldtheatres\.co\.uk/events/[^"]+)"\s+class="c-card\s+c-card--event".*?</a>',
    re.S,
)
_NEXT = re.compile(r'<a href="([^"]+)"[^>]*aria-label="Next"')


def _local(stamp: str) -> datetime:
    """The site's own clock time; drop the UTC offset."""
    return datetime.fromisoformat(stamp[:19])


def fetch() -> list[Event]:
    events: dict[str, Event] = {}
    url = URL
    for _ in range(MAX_PAGES):
        page = get(url)
        for card in _CARD.finditer(page):
            body, link = card.group(0), card.group(1)
            times = re.findall(r'<time datetime="([^"]+)"', body)
            title = re.search(r'c-card__title-text">(.*?)</span>', body, re.S)
            venue = re.search(r'c-card__posttitle">(.*?)<', body, re.S)
            image = re.search(r'<img[^>]*\ssrc="([^"]+)"', body)
            if not (times and title):
                continue
            venue_name = html.unescape(venue.group(1)).strip() if venue else ""
            if venue_name not in VENUES:
                continue
            start = _local(times[0])
            end = _local(times[1]) if len(times) > 1 else None
            events[link] = Event(
                title=html.unescape(title.group(1)).strip(),
                start=start,
                venue=venue_name,
                url=link,
                source=NAME,
                image=html.unescape(image.group(1)) if image else None,
                until=end if end and end.date() != start.date() else None,
            )
        nxt = _NEXT.search(page)
        if not nxt:
            break
        url = html.unescape(nxt.group(1))
        time.sleep(1)
    return list(events.values())
