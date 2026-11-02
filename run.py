"""Fetch comedy gigs from every source in gigs/sources and write site/index.html."""
import importlib
import json
import pkgutil
import re
import sys
from datetime import datetime
from pathlib import Path

from gigs import notify, sources
from gigs.model import Event
from gigs.render import render

DOCS = Path(__file__).parent / "docs"
STATE = Path(__file__).parent / "state" / "alerted.json"


# Sources spell some venues differently; show each venue once.
VENUE_ALIASES = {"Octagon": "Octagon Centre"}


def collect() -> tuple[list[Event], dict[str, str]]:
    merged: dict[tuple, Event] = {}
    report: dict[str, str] = {}
    for info in sorted(pkgutil.iter_modules(sources.__path__), key=lambda i: i.name):
        if info.name.startswith("_"):
            continue
        try:
            found = importlib.import_module(f"gigs.sources.{info.name}").fetch()
        except Exception as exc:  # one broken source must not kill the run
            report[info.name] = f"FAILED: {exc}"
            continue
        report[info.name] = f"{len(found)} events"
        for e in found:
            e.venue = VENUE_ALIASES.get(e.venue, e.venue)
            have = merged.setdefault(e.key(), e)
            # Earlier source wins; fill any gaps from later ones.
            have.image = have.image or e.image
            have.price = have.price or e.price
    now = datetime.now()
    upcoming = sorted((e for e in merged.values() if e.start >= now.replace(hour=0, minute=0)), key=lambda e: e.start)
    return upcoming, report


def _stable(page: str) -> str:
    return re.sub(r"Last changed .*? O-BOT checks", "O-BOT checks", page)


def snapshot(events: list[Event]) -> list[dict]:
    return [
        {"title": e.title, "start": e.start.isoformat(), "venue": e.venue, "url": e.url, "image": e.image, "until": e.until.isoformat() if e.until else None}
        for e in events
    ]


def alert(events: list[Event]) -> None:
    """Email new gigs. Alerted keys are saved only after a successful send."""
    new, keys = notify.pending(events, STATE)
    if not new:
        notify.save(STATE, keys)
        return
    try:
        sent = notify.send(new)
    except Exception as exc:  # leave state alone so the next run retries
        print(f"ALERT FAILED, will retry next run: {exc}")
        return
    print(f"{len(new)} new gigs, alert {'sent' if sent else 'skipped'}")
    if sent:
        notify.save(STATE, keys)


def main() -> int:
    events, report = collect()
    for name, result in report.items():
        print(f"{name:12} {result}")
    if all(r.startswith("FAILED") for r in report.values()):
        return 1
    DOCS.mkdir(exist_ok=True)
    alert(events)
    data_file, page_file = DOCS / "gigs.json", DOCS / "index.html"
    new = snapshot(events)
    old = json.loads(data_file.read_text(encoding="utf-8")) if data_file.exists() else None
    html = render(events, datetime.now())
    # Ignore the "Last changed" stamp so a template-only edit still rewrites the page.
    same_page = page_file.exists() and _stable(html) == _stable(page_file.read_text(encoding="utf-8"))
    if new == old and same_page:
        print(f"{len(events)} gigs, unchanged - nothing written")
        return 0
    data_file.write_text(json.dumps(new, indent=1, ensure_ascii=False), encoding="utf-8")
    page_file.write_text(html, encoding="utf-8")
    print(f"{len(events)} gigs, changed - wrote docs/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
