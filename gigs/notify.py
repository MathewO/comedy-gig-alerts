"""Email an alert when gigs appear that we have not alerted about before."""
import json
import os
import smtplib
from datetime import date
from email.message import EmailMessage
from email.utils import formataddr
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


_BRAND = "O-BOT"
_ACCENT = "#c2410c"


def _card(e: Event) -> str:
    when = e.when()
    link = escape(e.url, quote=True)
    pic = ""
    if e.image:
        pic = (
            f'<td width="104" valign="top" style="padding-right:14px">'
            f'<a href="{link}"><img src="{escape(e.image, quote=True)}" width="104" alt="{escape(e.title, quote=True)}" '
            f'style="display:block;width:104px;border-radius:8px;border:0"></a></td>'
        )
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="border-top:1px solid #e5e2db;padding:14px 0"><tr>'
        f'{pic}<td valign="top">'
        f'<div style="font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:{_ACCENT};font-weight:700">{when}</div>'
        f'<div style="font-size:18px;font-weight:700;margin:3px 0"><a href="{link}" style="color:#1c1b1a;text-decoration:none">{escape(e.title)}</a></div>'
        f'<div style="font-size:14px;color:#6b665f">{escape(e.venue)}</div>'
        f'<div style="margin-top:8px"><a href="{link}" style="font-size:14px;color:{_ACCENT};font-weight:600">Get tickets &rarr;</a></div>'
        "</td></tr></table>"
    )


def _html(new: list[Event], shown: list[Event]) -> str:
    n = len(new)
    gigs = "gig" if n == 1 else "gigs"
    intro = (
        f"I have been scanning every comedy listing in Sheffield so you don't have to, "
        f"and I found <b>{n} new {gigs}</b>. I can't laugh myself (my sense of humour "
        f"module is on back-order), so please go on my behalf."
    )
    more = ""
    if n > len(shown):
        more = f'<p style="color:#6b665f">...plus {n - len(shown)} more on the full list.</p>'
    return f"""<!doctype html><html><body style="margin:0;background:#f1eee8;font-family:Helvetica,Arial,sans-serif;color:#1c1b1a">
<div style="display:none;max-height:0;overflow:hidden">{n} new comedy {gigs} in Sheffield, courtesy of your friendly family robot.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f1eee8"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#ffffff;border-radius:12px;overflow:hidden">
<tr><td align="center" style="background:#1c1b1a;padding:28px 20px">
<div style="font-size:34px;font-weight:900;letter-spacing:.12em;color:#ffffff">{_BRAND}</div>
<div style="font-size:12px;letter-spacing:.18em;color:#fb923c;margin-top:4px">THE FRIENDLY FAMILY ROBOT</div></td></tr>
<tr><td style="padding:28px 32px 8px">
<div style="text-align:center;font-size:13px;letter-spacing:.2em;font-weight:700;border-bottom:1px solid #d9d5cc;padding-bottom:16px">SHEFFIELD COMEDY ALERT</div>
<p style="font-size:16px;margin:22px 0 8px"><b>Beep boop, humans!</b></p>
<p style="font-size:15px;line-height:1.55;margin:0 0 18px">{intro}</p>
{"".join(_card(e) for e in shown)}
{more}
<table role="presentation" align="center" cellpadding="0" cellspacing="0" style="margin:24px auto"><tr><td style="background:#1c1b1a;border-radius:8px">
<a href="{PAGE}" style="display:inline-block;padding:14px 28px;color:#ffffff;text-decoration:none;font-weight:700">See the full list</a></td></tr></table>
<p style="font-size:15px;margin:0 0 4px">Beep boop,</p>
<p style="font-size:15px;margin:0 0 24px"><b>{_BRAND}</b> &#129302;</p></td></tr>
<tr><td style="background:#f6f4ef;padding:18px 32px;font-size:12px;line-height:1.5;color:#6b665f;text-align:center">
Sent with love and a moderate amount of electricity by {_BRAND}.<br>
I do not eat, sleep or heckle. Checking the Sheffield listings every 4 hours.</td></tr>
</table></td></tr></table></body></html>"""


def _message(new: list[Event], sender: str, recipients: list[str]) -> EmailMessage:
    shown = new[:MAX_LISTED]
    lines = [
        f"{e.title}\n  {e.when()} - {e.venue}\n  {e.url}"
        for e in shown
    ]
    if len(new) > len(shown):
        lines.append(f"...plus {len(new) - len(shown)} more: {PAGE}")
    n = len(new)
    msg = EmailMessage()
    msg["Subject"] = f"{_BRAND} found {n} new comedy gig{'s' if n != 1 else ''} in Sheffield"
    msg["From"] = formataddr((_BRAND, sender))
    msg["To"] = ", ".join(recipients)
    msg.set_content(
        "Beep boop, humans! It's O-BOT, your friendly family robot.\n\n"
        + "\n\n".join(lines)
        + f"\n\nFull list: {PAGE}\n\nBeep boop,\nO-BOT"
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
