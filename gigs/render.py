from datetime import datetime
from html import escape
from itertools import groupby

from .model import Event

_CSS = """
:root{--bg:#f6f4ef;--card:#fff;--ink:#1c1b1a;--mute:#6b665f;--line:#e4dfd6;--accent:#c2410c}
@media (prefers-color-scheme:dark){:root{--bg:#161514;--card:#201f1d;--ink:#f1eee8;--mute:#a39d93;--line:#34312d;--accent:#fb923c}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 system-ui,sans-serif}
main{max-width:860px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.6rem;margin:0 0 4px}
.sub{color:var(--mute);margin:0 0 20px}
.tools{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px}
.tools input,.tools select{font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink)}
.tools input{flex:1 1 200px}
h2{font-size:1rem;text-transform:uppercase;letter-spacing:.06em;color:var(--mute);margin:28px 0 10px;border-bottom:1px solid var(--line);padding-bottom:6px}
.gig{display:flex;gap:14px;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden;margin-bottom:10px;color:inherit;text-decoration:none}
.gig:hover{border-color:var(--accent)}
.pic{flex:0 0 120px;background:var(--line) center/cover no-repeat;min-height:96px}
.body{padding:10px 14px 10px 0;min-width:0}
.when{color:var(--accent);font-weight:600;font-size:.85rem}
.act{font-size:1.05rem;font-weight:650;margin:2px 0}
.meta{color:var(--mute);font-size:.9rem}
.price{font-weight:600;color:var(--ink)}
.empty{color:var(--mute);padding:24px 0}
@media (max-width:520px){.pic{flex-basis:88px}}
"""

_JS = """
const q=document.getElementById('q'),v=document.getElementById('v');
function apply(){const t=q.value.toLowerCase(),vv=v.value;
document.querySelectorAll('.gig').forEach(g=>{g.hidden=!((!t||g.dataset.t.includes(t))&&(!vv||g.dataset.v===vv))});
document.querySelectorAll('section').forEach(s=>{s.hidden=![...s.querySelectorAll('.gig')].some(g=>!g.hidden)})}
q.oninput=v.onchange=apply;
"""


def _card(e: Event) -> str:
    when = e.start.strftime("%a %d %b %Y, %H:%M").replace(" 0", " ")
    pic = f' style="background-image:url(\'{escape(e.image, quote=True)}\')"' if e.image else ""
    price = f' · <span class="price">{escape(e.price)}</span>' if e.price else ""
    return (
        f'<a class="gig" href="{escape(e.url, quote=True)}" target="_blank" rel="noopener" '
        f'data-t="{escape((e.title + " " + e.venue).lower(), quote=True)}" data-v="{escape(e.venue, quote=True)}">'
        f'<div class="pic"{pic}></div><div class="body">'
        f'<div class="when">{when}</div><div class="act">{escape(e.title)}</div>'
        f'<div class="meta">{escape(e.venue)}{price}</div></div></a>'
    )


def render(events: list[Event], generated: datetime) -> str:
    venues = sorted({e.venue for e in events})
    options = "".join(f'<option value="{escape(x, quote=True)}">{escape(x)}</option>' for x in venues)
    sections = []
    for month, group in groupby(events, key=lambda e: e.start.strftime("%B %Y")):
        sections.append(f"<section><h2>{month}</h2>{''.join(_card(e) for e in group)}</section>")
    body = "".join(sections) or '<p class="empty">No upcoming gigs found.</p>'
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>Sheffield comedy</title><style>{_CSS}</style></head><body><main>"
        "<h1>Sheffield comedy</h1>"
        f'<p class="sub">{len(events)} upcoming gigs · last changed {generated:%d %b %Y %H:%M}</p>'
        '<div class="tools"><input id="q" type="search" placeholder="Search act or venue">'
        f'<select id="v"><option value="">All venues</option>{options}</select></div>'
        f"{body}<script>{_JS}</script></main></body></html>"
    )
