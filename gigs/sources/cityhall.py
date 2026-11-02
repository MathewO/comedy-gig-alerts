"""Sheffield City Hall's own events (Oval Hall, Memorial Hall).

The site lists every show in its sitemap, but its pages carry no genre ("Default" is the only
category) and give a date without a time. So each page is read once, the answer is remembered in
state/cityhall.json, and comedy is picked out from the show description (stand-up, comedian) or
from the acts listed in gigs/comedy_acts.txt.
"""
import html
import json
import re
import time
import urllib.parse
from datetime import datetime
from pathlib import Path

from ..http import get
from ..model import Event

NAME = "cityhall"
SITEMAP = "https://www.sheffieldcityhall.co.uk/sitemap.xml"
CACHE = Path(__file__).resolve().parents[2] / "state" / "cityhall.json"
ACTS_FILE = Path(__file__).resolve().parents[1] / "comedy_acts.txt"

_LD = re.compile(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', re.S)
_DATA = re.compile(r"var data = (\{.*?\});\s", re.S)
_COMEDY = re.compile(r"stand[- ]?up|comedian|comedienne|comedy club|sketch show|improvised comedy|improv", re.I)
DEFAULT_TIME = (19, 30)   # the pages give no time; the real one is filled in from another source when it has it


def _acts() -> tuple[list[str], list[str]]:
    """(acts to include, acts to never include) from gigs/comedy_acts.txt; lines starting with - exclude."""
    lines = [l.strip().lower() for l in ACTS_FILE.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    return [l for l in lines if not l.startswith("-")], [l[1:].strip() for l in lines if l.startswith("-")]


def _plain_ticket_link(link: str, fallback: str) -> str:
    """The page's link is an affiliate wrapper around the Ticketmaster address; use the plain address."""
    inner = urllib.parse.parse_qs(urllib.parse.urlparse(link).query).get("u")
    return inner[0] if inner else (link or fallback)


def _read(url: str) -> dict | None:
    page = get(url)
    event = None
    for block in _LD.findall(page):
        try:
            data = json.loads(block, strict=False)
        except ValueError:
            continue
        for node in (data.get("@graph", [data]) if isinstance(data, dict) else data):
            if isinstance(node, dict) and "Event" in str(node.get("@type")):
                event = node
    m = _DATA.search(page)
    if not (event and m and event.get("startDate")):
        return None
    try:
        info = json.loads(m.group(1))
    except ValueError:
        return None
    text = re.sub(r"<[^>]+>", " ", html.unescape(info.get("description") or ""))
    title = html.unescape(info.get("title") or event.get("name") or "")
    image = (event.get("image") or {}).get("url") if isinstance(event.get("image"), dict) else None
    if image:
        image = re.sub(r"h_\d+", "h_700", re.sub(r"w_\d+", "w_700", image))   # lighter than the 1200px original
    return {
        "title": title,
        "start": event["startDate"],
        "end": event.get("endDate") or event["startDate"],
        "hall": info.get("hostname") or "Sheffield City Hall",
        "image": image,
        "link": _plain_ticket_link(info.get("linkUrl", ""), url),
        "desc": text[:2000],
    }


def fetch() -> list[Event]:
    urls = re.findall(r"<loc>(https://www\.sheffieldcityhall\.co\.uk/event/[^<]+)</loc>", get(SITEMAP))
    cache: dict[str, dict] = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    cache = {u: v for u, v in cache.items() if u in urls}       # forget shows that have gone from the site
    for url in urls:
        if url not in cache:
            try:
                cache[url] = _read(url) or {"skip": True}
            except Exception:                                     # one bad page must not lose the rest
                continue
            time.sleep(0.3)
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1, sort_keys=True), encoding="utf-8")
    acts, never = _acts()
    events: list[Event] = []
    for url, rec in cache.items():
        if rec.get("skip"):
            continue
        title = rec["title"].lower()
        if any(n in title for n in never):
            continue
        if not (_COMEDY.search(rec.get("desc", "")) or _COMEDY.search(title) or any(a in title for a in acts)):
            continue
        start = datetime.fromisoformat(rec["start"][:10]).replace(hour=DEFAULT_TIME[0], minute=DEFAULT_TIME[1])
        end = datetime.fromisoformat(rec["end"][:10])
        events.append(
            Event(
                title=rec["title"],
                start=start,
                venue=rec["hall"],
                url=rec["link"],
                source=NAME,
                image=rec["image"],
                until=end if end.date() != start.date() else None,
                timed=False,
            )
        )
    return events
