"""Fetch comedy gigs from every source in gigs/sources and write site/index.html."""
import importlib
import json
import pkgutil
import sys
from pathlib import Path

from gigs import notify, sources
from gigs.model import Event, act_of, uk_now
from gigs.sources import performancevenues
from gigs.render import render

DOCS = Path(__file__).parent / "docs"
STATE = Path(__file__).parent / "state" / "alerted.json"


# Sources spell some venues differently; show each venue once.
VENUE_ALIASES = {"Octagon": "Octagon Centre"}


def prefer_university_pages(events, report: dict[str, str]) -> None:
    """Octagon tickets are better (choose your seats) on the University's page than on Ticketmaster."""
    try:
        pages = performancevenues.university_pages()
    except Exception as exc:  # keep the original links rather than fail the run
        report["university-links"] = f"FAILED: {exc}"
        return
    swapped = 0
    for e in events:
        link = pages.get((e.start.date().isoformat(), act_of(e.title))) if e.venue == "Octagon Centre" else None
        if link and e.url != link:
            e.url, swapped = link, swapped + 1
    report["university-links"] = f"{swapped} Octagon links switched"


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
            if not have.timed and e.timed:      # a source with a real start time fills in the gap
                have.start, have.timed = e.start, True
            # Earlier source wins; fill any gaps from later ones.
            have.image = have.image or e.image
            have.price = have.price or e.price
    prefer_university_pages(merged.values(), report)
    now = uk_now()
    upcoming = sorted((e for e in merged.values() if e.start >= now.replace(hour=0, minute=0)), key=lambda e: e.start)
    return upcoming, report


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
    # Written every run so the page's "last checked" time is true; git only
    # commits when something differs, which is every run because of that stamp.
    (DOCS / "gigs.json").write_text(json.dumps(snapshot(events), indent=1, ensure_ascii=False), encoding="utf-8")
    (DOCS / "index.html").write_text(render(events, uk_now()), encoding="utf-8")
    print(f"{len(events)} gigs, wrote docs/index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
