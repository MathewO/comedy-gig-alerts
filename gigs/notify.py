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

_D = theme.DARK  # email is always the dark look: clients can't switch themes the way the page does


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
        day, size, month = f"{e.start.day}-{e.until.day}", 19, e.until.strftime("%b")
    else:
        day, size, month = str(e.start.day), 26, e.start.strftime("%b")
    clock = "" if e.until else f" &nbsp; {e.start:%H:%M}"
    price = f" &nbsp; <b style=\"color:{_D['ink']}\">{escape(e.price)}</b>" if e.price else ""
    pic = ""
    if e.image:
        pic = (
            f'<td width="72" valign="middle" style="padding-left:12px"><a href="{link}">'
            f'<img src="{escape(e.image, quote=True)}" width="72" alt="" '
            'style="display:block;width:72px;border-radius:10px;border:0"></a></td>'
        )
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'style="background:{_D["panel"]};border:2px solid {_D["line"]};border-radius:16px;margin-bottom:10px"><tr>'
        '<td width="62" valign="middle" style="padding:10px 0 10px 10px">'
        f'<table role="presentation" width="62" cellpadding="0" cellspacing="0"><tr>'
        f'<td align="center" style="background:{theme.CHASSIS};border-radius:10px;padding:7px 0;color:{theme.LED};line-height:1">'
        f'<div style="font-size:11px">{e.start:%a}</div>'
        f'<div style="font-family:{theme.DISPLAY_FONT};font-size:{size}px;font-weight:800;margin:4px 0">{day}</div>'
        f'<div style="font-size:11px">{month}</div></td></tr></table></td>'
        f'<td valign="middle" style="padding:10px 4px 10px 14px">'
        f'<a href="{link}" style="font-family:{theme.DISPLAY_FONT};font-size:17px;font-weight:600;line-height:1.25;'
        f'color:{_D["ink"]};text-decoration:none">{escape(e.title)}</a>'
        f'<div style="font-size:14px;color:{_D["dim"]};margin-top:3px">{escape(e.venue)}{clock}{price}</div>'
        f'<table role="presentation" cellpadding="0" cellspacing="0" style="margin-top:9px"><tr>'
        f'<td style="background:{theme.LED};border-radius:999px"><a href="{link}" '
        f'style="display:inline-block;padding:7px 16px;font-size:14px;font-weight:700;color:{theme.CHASSIS};'
        'text-decoration:none">Tickets</a></td></tr></table></td>'
        f"{pic}"
        '<td width="10" style="font-size:0">&nbsp;</td></tr></table>'
    )


def _html(new: list[Event], shown: list[Event]) -> str:
    n = len(new)
    gigs = "gig" if n == 1 else "gigs"
    more = ""
    if n > len(shown):
        more = f'<p style="color:{_D["dim"]};margin:4px 0 14px">Plus {n - len(shown)} more on the full list.</p>'
    return f"""<!doctype html><html><body style="margin:0;background:{_D['bg']};font-family:{theme.BODY_FONT};color:{_D['ink']}">
<div style="display:none;max-height:0;overflow:hidden">{n} new comedy {gigs} in Sheffield, courtesy of your friendly family robot.</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{_D['bg']}"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%">
<tr><td align="center" style="padding:6px 0 18px">{theme.robot_email()}</td></tr>
<tr><td style="background:{_D['panel']};border:2px solid {_D['line']};border-radius:18px;padding:16px 20px">
<div style="font-family:{theme.DISPLAY_FONT};font-size:24px;font-weight:800;line-height:1.15">Sheffield comedy</div>
<p style="font-size:15px;line-height:1.55;margin:8px 0 0;color:{_D['dim']}"><b style="color:{_D['ink']}">Beep boop! {n} new {gigs}.</b>
I scanned every comedy listing in Sheffield so you don't have to. I can't laugh myself (my sense of humour module is on back-order), so please go on my behalf.</p>
</td></tr>
<tr><td style="padding:18px 0 4px">{"".join(_row(e) for e in shown)}{more}</td></tr>
<tr><td align="center" style="padding:6px 0 18px"><table role="presentation" cellpadding="0" cellspacing="0"><tr>
<td style="background:{theme.LED};border-radius:999px"><a href="{PAGE}" style="display:inline-block;padding:12px 26px;font-weight:700;color:{theme.CHASSIS};text-decoration:none">See the full list</a></td></tr></table></td></tr>
<tr><td align="center" style="padding:6px 12px 8px;font-size:13px;line-height:1.5;color:{_D['dim']}">
Beep boop, {theme.BRAND}<br>Sent with a moderate amount of electricity. I do not eat, sleep or heckle.<br>I check the Sheffield listings every 4 hours.</td></tr>
</table></td></tr></table></body></html>"""


def _message(new: list[Event], sender: str, recipients: list[str]) -> EmailMessage:
    shown = new[:MAX_LISTED]
    lines = [f"{e.title}\n  {e.when()} - {e.venue}\n  {e.url}" for e in shown]
    if len(new) > len(shown):
        lines.append(f"...plus {len(new) - len(shown)} more: {PAGE}")
    n = len(new)
    msg = EmailMessage()
    msg["Subject"] = f"{theme.BRAND} found {n} new comedy gig{'s' if n != 1 else ''} in Sheffield"
    msg["From"] = formataddr((theme.BRAND, sender))
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
