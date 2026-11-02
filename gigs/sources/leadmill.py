"""The Leadmill comedy listings (Steamworks, Foundry, Sheffield Plate, ...).

The page embeds schema.org Event JSON-LD, so no HTML parsing is needed.
"""
import html
import json
import re
from datetime import datetime

from ..http import get
from ..model import Event

NAME = "leadmill"
URL = "https://leadmill.co.uk/events/comedy/"

_LD = re.compile(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', re.S)
# Leadmill appends the venue to act names, e.g. "Finlay Christie (The Steamworks)".
_VENUE_SUFFIX = re.compile(
    r"\s*\((?=[^)]*(foundry|steamworks|bar one|sheffield|peddler|matinee))[^)]*\)\s*$",
    re.I,
)


def fetch() -> list[Event]:
    events: dict[str, Event] = {}
    for block in _LD.findall(get(URL)):
        try:
            data = json.loads(block, strict=False)
        except ValueError:
            continue
        nodes = data if isinstance(data, list) else data.get("@graph", [data])
        for node in nodes:
            if not isinstance(node, dict) or node.get("@type") != "Event":
                continue
            url = node.get("url", "")
            if url in events:
                continue
            title = _VENUE_SUFFIX.sub("", html.unescape(node["name"])).strip()
            title = re.sub(r"\s*[–-]\s*matinee$", "", title, flags=re.I)
            location = node.get("location") or {}
            events[url] = Event(
                title=title,
                # The feed labels local time as +00:00 all year; keep the clock time as-is.
                start=datetime.fromisoformat(node["startDate"][:19]),
                venue=html.unescape(location.get("name", "Leadmill")),
                url=url,
                source=NAME,
                image=node.get("image") or None,
            )
    return list(events.values())
