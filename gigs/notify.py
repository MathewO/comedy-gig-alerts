"""Email an alert when gigs appear that we have not alerted about before."""
import json
import os
import smtplib
from datetime import date
from email.message import EmailMessage
from email.utils import formataddr
from html import escape
from pathlib import Path

from . import theme
from .model import Event
from .render import when_text

PAGE = "https://mathewo.github.io/comedy-gig-alerts/"
MAX_LISTED = 50

_C = theme.LIGHT  # light email: Gmail darkens it itself in dark mode, which avoids its white frame clashing with a dark design
_F = theme.FONT


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


def _row(e: Event) -> str:
    """One gig. Two inline-block columns: side by side when there is room, stacked when there isn't.

    The <style> block in _html() makes the picture full width on phones; without it
    (clients that ignore <style>) the columns still wrap into a stack.
    """
    link = escape(e.url, quote=True)
    price = f" &nbsp;<b style=\"color:{_C['ink']}\">{escape(e.price)}</b>" if e.price else ""
    pic = ""
    if e.image:
        pic = (
            '<div class="gimg" style="display:inline-block;vertical-align:middle;width:100%;max-width:240px;'
            'box-sizing:border-box;padding-right:20px;font-size:0;line-height:0">'
            f'<a href="{link}"><img src="{escape(e.image, quote=True)}" width="220" alt="" '
            'style="display:block;width:100%;height:auto;border-radius:6px;border:0"></a></div>'
        )
    text = (
        '<div class="gtxt" style="display:inline-block;vertical-align:middle;width:100%;max-width:340px;'
        f'box-sizing:border-box;font-size:16px;line-height:1.4;font-family:{_F}">'
        f'<div style="font-size:13px;color:{_C["dim"]}">{when_text(e)}</div>'
        f'<a href="{link}" style="display:block;margin-top:4px;font-size:18px;font-weight:600;line-height:1.3;color:{_C["ink"]};text-decoration:none">{escape(e.title)}</a>'
        f'<div style="font-size:14px;color:{_C["dim"]};margin-top:4px">{escape(e.venue)}{price}</div>'
        f'<div style="margin-top:12px"><a href="{link}" style="font-size:14px;font-weight:600;color:{_C["ink"]};'
        f'text-decoration:none;border-bottom:2px solid {theme.ACCENT}">Get tickets</a></div></div>'
    )
    return (
        f'<div style="border-top:1px solid {_C["line"]};padding:20px 0;font-size:0;line-height:0">{pic}{text}</div>'
    )


def _html(new: list[Event], shown: list[Event]) -> str:
    n = len(new)
    gigs = "gig has" if n == 1 else "gigs have"
    more = ""
    if n > len(shown):
        more = f'<p style="color:{_C["dim"]};font-size:14px;margin:0 0 16px">Plus {n - len(shown)} more on the full list.</p>'
    return f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>@media only screen and (max-width:520px){{.gimg{{max-width:100%!important;padding-right:0!important}}.gtxt{{max-width:100%!important;padding-top:14px!important}}}}</style></head><body style="margin:0;background:{_C['bg']};font-family:{_F};color:{_C['ink']}">
<div style="display:none;max-height:0;overflow:hidden">{n} new comedy {gigs} been listed in Sheffield.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="height:3px;line-height:3px;font-size:0;background:{theme.ACCENT}">&nbsp;</td></tr></table>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{_C['bg']}"><tr><td align="center" style="padding:28px 16px 32px">
<table role="presentation" width="580" cellpadding="0" cellspacing="0" style="max-width:580px;width:100%;font-family:{_F}">
<tr><td align="center" style="padding:0"><img src="{PAGE}title.png" width="580" alt="{theme.TITLE}" style="display:block;width:100%;max-width:580px;height:auto;border:0;font-size:22px;font-weight:700;letter-spacing:.08em;color:{_C['ink']}"></td></tr>
<tr><td align="center" style="font-size:16px;line-height:1.6;padding:0 0 24px;text-align:center">
<p style="margin:0">Hello, {n} new comedy {gigs} been listed in Sheffield. Details below.</p></td></tr>
<tr><td>{"".join(_row(e) for e in shown)}<div style="border-top:1px solid {_C['line']};font-size:0">&nbsp;</div></td></tr>
<tr><td style="padding-top:22px">{more}<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td align="center" style="background:{_C['ink']};border-radius:8px"><a href="{PAGE}" style="display:block;padding:16px 0;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none">See all gigs</a></td></tr></table></td></tr>
<tr><td style="font-size:12px;line-height:1.6;color:{_C['dim']};padding-top:28px">Sent automatically by {theme.BRAND}, which checks the Sheffield listings every four hours and has never once laughed at a joke.</td></tr>
</table></td></tr></table></body></html>"""


def _message(new: list[Event], sender: str, recipients: list[str]) -> EmailMessage:
    shown = new[:MAX_LISTED]
    lines = [f"{e.title}\n  {e.when()} - {e.venue}\n  {e.url}" for e in shown]
    if len(new) > len(shown):
        lines.append(f"...plus {len(new) - len(shown)} more: {PAGE}")
    n = len(new)
    msg = EmailMessage()
    msg["Subject"] = f"{n} new comedy gig{'s' if n != 1 else ''} in Sheffield"
    msg["From"] = formataddr((theme.BRAND, sender))
    msg["To"] = ", ".join(recipients)
    msg.set_content(
        f"{n} new comedy gig{'s have' if n != 1 else ' has'} been listed in Sheffield.\n\n"
        + "\n\n".join(lines)
        + f"\n\nSee all gigs: {PAGE}"
    )
    msg.add_alternative(_html(new, shown), subtype="html")
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
