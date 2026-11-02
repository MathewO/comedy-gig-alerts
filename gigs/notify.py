"""Email an alert when gigs appear that we have not alerted about before."""
import json
import os
import smtplib
from datetime import date
from email.message import EmailMessage
from html import escape
from pathlib import Path

from .model import Event

PAGE = "https://mathewo.github.io/comedy-gig-alerts/"
MAX_LISTED = 50


def pending(events: list[Event], state_file: Path) -> tuple[list[Event], set[str]]:
    """Return (events never alerted on, full set of keys to store once alerted)."""
    current = {e.key_str() for e in events}
    if not state_file.exists():
        return [], current  # first run: record what exists, alert on nothing
    seen = set(json.loads(state_file.read_text(encoding="utf-8")))
    new = [e for e in events if e.key_str() not in seen]
    today = date.today().isoformat()
    keep = {k for k in seen if k.split("|")[0] >= today}  # drop past gigs
    return new, keep | current


def save(state_file: Path, keys: set[str]) -> None:
    state_file.parent.mkdir(exist_ok=True)
    state_file.write_text(json.dumps(sorted(keys), indent=1), encoding="utf-8")


def _message(new: list[Event], sender: str, recipients: list[str]) -> EmailMessage:
    shown = new[:MAX_LISTED]
    lines, rows = [], []
    for e in shown:
        when = e.start.strftime("%a %d %b %Y, %H:%M")
        lines.append(f"{e.title}\n  {when} - {e.venue}\n  {e.url}")
        rows.append(
            f'<p><a href="{escape(e.url, quote=True)}"><b>{escape(e.title)}</b></a><br>'
            f"{when} &middot; {escape(e.venue)}</p>"
        )
    more = len(new) - len(shown)
    if more > 0:
        lines.append(f"...and {more} more: {PAGE}")
        rows.append(f"<p>...and {more} more on the page.</p>")
    n = len(new)
    msg = EmailMessage()
    msg["Subject"] = f"{n} new Sheffield comedy gig{'s' if n != 1 else ''}"
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg.set_content("\n\n".join(lines) + f"\n\nFull list: {PAGE}")
    msg.add_alternative(
        "<div style=\"font-family:system-ui,sans-serif\">" + "".join(rows)
        + f'<p><a href="{PAGE}">See the full list</a></p></div>',
        subtype="html",
    )
    return msg


def send(new: list[Event]) -> bool:
    """Send the alert. Returns False (and sends nothing) when email isn't configured."""
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")
    recipients = [r.strip() for r in os.environ.get("ALERT_RECIPIENTS", "").split(",") if r.strip()]
    if not (user and password and recipients):
        print("email not configured - skipping alert")
        return False
    msg = _message(new, user, recipients)
    if os.environ.get("ALERT_DRY_RUN"):
        print(msg.as_string())
        return True
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(user, password)
        smtp.send_message(msg)
    return True
