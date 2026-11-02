# Sheffield comedy gigs

A scheduled GitHub Actions job scrapes Sheffield comedy listings and publishes a
date-ordered page (`docs/index.html`) via GitHub Pages. No servers, no API keys.

## How it works
- `run.py` loads every module in `gigs/sources/`, merges duplicates (same date, act and
  matinee/evening), and writes `docs/gigs.json` and `docs/index.html`.
- `.github/workflows/update.yml` runs it every 4 hours and commits the result only if
  the gig list changed.
- A source that fails is reported in the log and skipped; the others still publish.

## Sources
| File | Covers |
|---|---|
| `gigs/sources/leadmill.py` | Leadmill comedy: Steamworks, Foundry, Sheffield Plate, Peddler Warehouse, Bar One |
| `gigs/sources/standup.py` | stand-up.co.uk guide: City Hall, Octagon, Utilita Arena, Foundry |

## Email alerts
When a gig appears that has never been alerted on, one email lists the new gigs.
Alerted gigs are tracked in `state/alerted.json`; the first run only records the list.
Repo secrets (Settings > Secrets and variables > Actions):

| Secret | Value |
|---|---|
| `SMTP_USER` | Gmail address the alerts are sent from |
| `SMTP_PASSWORD` | Gmail app password (needs 2-Step Verification) |
| `ALERT_RECIPIENTS` | Comma-separated addresses to alert |

Without these secrets the page still updates and alerts are skipped.

## Adding a venue
Add `gigs/sources/<name>.py` defining `NAME` and `fetch() -> list[Event]`
(see `leadmill.py`). It is picked up automatically.

## Run locally
    python run.py

## Known gaps
No prices: the ticket sites (See Tickets, Ticketmaster) block automated requests.
