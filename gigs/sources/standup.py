"""stand-up.co.uk Sheffield guide: covers City Hall (Last Laugh, tours) and Foundry."""
import html
import re
import time
from datetime import datetime

from ..http import get
from ..model import Event

NAME = "standup"
URL = "https://stand-up.co.uk/comedy-sheffield"
MAX_PAGES = 15

_CARD = re.compile(r'<a class="public-event-card".*?</a>', re.S)


def _field(pattern: str, card: str) -> str:
    m = re.search(pattern, card, re.S)
    return html.unescape(m.group(1)).strip() if m else ""


def _parse_start(date: str, clock: str) -> datetime:
    date = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", date)
    day = datetime.strptime(date, "%a %d %b %Y")
    clock = clock.strip("() ").lower()
    fmt = "%I:%M%p" if ":" in clock else "%I%p"
    t = datetime.strptime(clock, fmt)
    return day.replace(hour=t.hour, minute=t.minute)


def fetch() -> list[Event]:
    events: dict[str, Event] = {}
    for page in range(1, MAX_PAGES + 1):
        cards = _CARD.findall(get(URL if page == 1 else f"{URL}?page={page}"))
        new = 0
        for card in cards:
            if _field(r'public-event-card-town">(.*?)<', card) != "Sheffield":
                continue
            url = _field(r'href="([^"]+)"', card)
            if url in events:
                continue
            venue = _field(r'public-event-card-venue"[^>]*>(.*?)<', card)
            events[url] = Event(
                title=_field(r'public-event-card-title">(.*?)<', card),
                start=_parse_start(
                    _field(r"<strong>(.*?)</strong>", card),
                    _field(r'public-event-card-time">(.*?)<', card),
                ),
                venue=re.sub(r",\s*Sheffield$", "", venue),
                url=url,
                source=NAME,
                image=_field(r"background-image:\s*url\('([^']+)'\)", card) or None,
            )
            new += 1
        if not cards or not new:
            break
        time.sleep(1)
    return list(events.values())
