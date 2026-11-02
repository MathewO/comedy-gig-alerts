"""Octagon Centre's own listing (all genres, no category labels).

Only acts named in gigs/comedy_acts.txt are kept. Comedy that the University's
Performance Venues site labels is picked up by performancevenues.py instead.
"""
import html
import json
import re
from datetime import datetime
from pathlib import Path

from ..http import get
from ..model import Event

NAME = "octagon"
URL = "https://sheffieldoctagon.com/"
ACTS_FILE = Path(__file__).resolve().parents[1] / "comedy_acts.txt"

_LD = re.compile(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', re.S)


def _acts() -> list[str]:
    lines = ACTS_FILE.read_text(encoding="utf-8").splitlines()
    return [l.strip().lower() for l in lines if l.strip() and not l.startswith("#")]


def _starts(page: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for block in _LD.findall(page):
        try:
            data = json.loads(block, strict=False)
        except ValueError:
            continue
        for item in data.get("itemListElement", []) if isinstance(data, dict) else []:
            out[item["url"]] = item["startDate"]
    return out


def _price(url: str) -> str | None:
    """Cheapest ticket from the event page's JSON-LD offers."""
    for block in _LD.findall(get(url)):
        try:
            data = json.loads(block, strict=False)
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("offers"):
            prices = [float(o["price"]) for o in data["offers"] if o.get("price")]
            if prices:
                return f"from £{min(prices):.2f}".replace(".00", "")
    return None


def fetch() -> list[Event]:
    acts = _acts()
    page = get(URL)
    starts = _starts(page)
    events: list[Event] = []
    for chunk in page.split('<div class="g-event-list-item')[1:]:
        link = re.search(r'<a href="([^"]+)"', chunk)
        title = re.search(r'<h2[^>]*>\s*(.*?)\s*</h2>', chunk, re.S)
        if not (link and title and link[1] in starts):
            continue
        name = html.unescape(re.sub(r"\s+", " ", title[1])).strip()
        if not any(a in name.lower() for a in acts):
            continue
        image = re.search(r'<img src="([^"]+)"', chunk)
        events.append(
            Event(
                title=name,
                start=datetime.fromisoformat(starts[link[1]][:19]),
                venue="Octagon Centre",
                url=link[1],
                source=NAME,
                image=image[1] if image else None,
                price=_price(link[1]),
            )
        )
    return events
