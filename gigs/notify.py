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

PAGE = "https://mathewo.github.io/comedy-gig-alerts/"
MAX_LISTED = 50

_C = theme.LIGHT  # email is always the light look: clients can't switch themes like the page does
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
    link = escape(e.url, quote=True)
    if e.until:
        day, size, month = f"{e.start.day}-{e.until.day}", 18, e.until.strftime("%b")
    else:
        day, size, month = str(e.start.day), 26, e.start.strftime("%b")
    clock = "" if e.until else f" &nbsp;{e.start:%H:%M}"
    price = f" &nbsp;<b style=\"color:{_C['ink']}\">{escape(e.price)}</b>" if e.price else ""
    pic = ""
    if e.image:
        pic = (
            f'<td width="72" valign="top" style="padding-left:14px"><a href="{link}">'
            f'<img src="{escape(e.image, quote=True)}" width="72" alt="" '
            'style="display:block;width:72px;border-radius:6px;border:0"></a></td>'
        )
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="border-top:1px solid {_C["line"]}"><tr>'
        f'<td width="56" valign="top" style="padding:16px 0;font-size:12px;line-height:1.3;color:{_C["dim"]}">{e.start:%a}'
        f'<div style="font-size:{size}px;font-weight:600;line-height:1.1;color:{_C["ink"]}">{day}</div>{month}</td>'
        '<td valign="top" style="padding:16px 0">'
        f'<a href="{link}" style="font-size:16px;font-weight:600;line-height:1.3;color:{_C["ink"]};text-decoration:none">{escape(e.title)}</a>'
        f'<div style="font-size:14px;color:{_C["dim"]};margin-top:3px">{escape(e.venue)}{clock}{price}</div>'
        f'<div style="margin-top:8px"><a href="{link}" style="font-size:14px;font-weight:600;color:{_C["ink"]};'
        f'text-decoration:none;border-bottom:2px solid {theme.ACCENT}">Get tickets</a></div></td>'
        f'{pic}</tr></table>'
    )


def _html(new: list[Event], shown: list[Event]) -> str:
    n = len(new)
    gigs = "gig has" if n == 1 else "gigs have"
    more = ""
    if n > len(shown):
        more = f'<p style="color:{_C["dim"]};font-size:14px;margin:0 0 16px">Plus {n - len(shown)} more on the full list.</p>'
    return f"""<!doctype html><html><body style="margin:0;background:{_C['bg']};font-family:{_F};color:{_C['ink']}">
<div style="display:none;max-height:0;overflow:hidden">{n} new comedy {gigs} been listed in Sheffield.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{_C['bg']}"><tr><td align="center" style="padding:40px 16px 32px">
<table role="presentation" width="580" cellpadding="0" cellspacing="0" style="max-width:580px;width:100%;font-family:{_F}">
<tr><td align="center" style="border-top:3px solid {theme.ACCENT};padding:16px 0 8px"><img src="{PAGE}wordmark.png" width="580" alt="{theme.TITLE}" style="display:block;width:100%;max-width:580px;height:auto;border:0;font-size:22px;font-weight:700;letter-spacing:.08em;color:{_C['ink']}"></td></tr>
<tr><td align="center" style="border-top:1px solid {_C['line']};padding:20px 0 26px;font-size:13px;letter-spacing:.12em;text-transform:uppercase">New gigs</td></tr>
<tr><td style="font-size:16px;line-height:1.6;padding-bottom:22px">
<p style="margin:0 0 14px">Hello,</p>
<p style="margin:0">{n} new comedy {gigs} been listed in Sheffield. Details below.</p></td></tr>
<tr><td>{"".join(_row(e) for e in shown)}<div style="border-top:1px solid {_C['line']};font-size:0">&nbsp;</div></td></tr>
<tr><td style="padding-top:22px">{more}<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr>
<td align="center" style="background:{_C['ink']};border-radius:8px"><a href="{PAGE}" style="display:block;padding:16px 0;font-size:15px;color:#ffffff;text-decoration:none">See all gigs</a></td></tr></table></td></tr>
<tr><td style="font-size:16px;line-height:1.6;padding:28px 0 8px">Kind regards,<br>{theme.BRAND}</td></tr>
<tr><td style="font-size:12px;line-height:1.6;color:{_C['dim']};padding-top:8px">Sent automatically by {theme.BRAND}, which checks the Sheffield listings every four hours and has never once laughed at a joke.</td></tr>
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
        + f"\n\nSee all gigs: {PAGE}\n\nKind regards,\n{theme.BRAND}"
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
