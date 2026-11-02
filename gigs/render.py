from datetime import datetime
from html import escape
from itertools import groupby
from string import Template

from . import theme
from .model import Event

_CSS = Template("""
:root{$light;--accent:$accent;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){$dark;color-scheme:dark}}
:root[data-theme=dark]{$dark;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 $font;-webkit-font-smoothing:antialiased}
body::before{content:"";display:block;height:3px;background:var(--accent)}
main{max-width:760px;margin:0 auto;padding:0 20px 80px}
a{color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
header{padding:52px 0 28px;border-bottom:1px solid var(--line)}
.mark{margin:0;font-size:1.5rem;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.lede{margin:10px 0 0;color:var(--dim)}
.tools{display:flex;gap:8px;flex-wrap:wrap;padding:20px 0 4px}
.tools input,.tools select,.tools button{font:inherit;font-size:.95rem;color:var(--ink);background:var(--subtle);border:1px solid var(--line);border-radius:8px;padding:9px 12px}
.tools input{flex:1 1 200px}
.tools button{cursor:pointer}
.tools button[aria-pressed=true]{background:var(--ink);border-color:var(--ink);color:var(--bg)}
h2{position:sticky;top:0;z-index:2;margin:28px 0 0;padding:10px 0;font-size:.9rem;font-weight:600;color:var(--dim);background:var(--bg);border-bottom:1px solid var(--line)}
.gig{display:grid;grid-template-columns:56px 72px 1fr auto;gap:16px;align-items:center;padding:16px 0;border-bottom:1px solid var(--line);text-decoration:none}
.gig[hidden]{display:none}
.date{font-size:.8rem;line-height:1.25;color:var(--dim)}
.day{display:block;font-size:1.7rem;font-weight:600;line-height:1.1;color:var(--ink)}
.day.run{font-size:1.2rem}
.pic{width:72px;height:72px;border-radius:6px;background:var(--subtle) center/cover no-repeat}
.act{display:block;font-weight:600;line-height:1.3}
.gig:hover .act{text-decoration:underline;text-decoration-color:var(--accent);text-underline-offset:3px}
.meta{display:flex;flex-wrap:wrap;gap:0 14px;color:var(--dim);font-size:.9rem;margin-top:2px}
.price{color:var(--ink);font-weight:600}
.cta{font-size:.9rem;font-weight:600;border-bottom:2px solid var(--accent);padding-bottom:1px}
.empty{color:var(--dim);padding:28px 0 0;font-size:.9rem}
@media (max-width:560px){.gig{grid-template-columns:48px 60px 1fr;gap:12px}.cta{display:none}.pic{width:60px;height:60px}}
""")

_JS = """
const q=document.getElementById('q'),v=document.getElementById('v'),w=document.getElementById('w'),root=document.documentElement;
function weekend(){const t=new Date();t.setHours(0,0,0,0);const d=t.getDay();
const fri=new Date(t);fri.setDate(t.getDate()+(d===0?-2:d===6?-1:5-d));
const sun=new Date(fri);sun.setDate(fri.getDate()+2);return[fri,sun]}
const iso=d=>d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');
function apply(){const t=q.value.toLowerCase(),vv=v.value,on=w.getAttribute('aria-pressed')==='true',[a,b]=weekend().map(iso);
document.querySelectorAll('.gig').forEach(g=>{const ok=(!t||g.dataset.t.includes(t))&&(!vv||g.dataset.v===vv)&&(!on||(g.dataset.u>=a&&g.dataset.d<=b));g.hidden=!ok});
document.querySelectorAll('section').forEach(s=>{s.hidden=![...s.querySelectorAll('.gig')].some(g=>!g.hidden)});
document.getElementById('none').hidden=[...document.querySelectorAll('.gig')].some(g=>!g.hidden)}
q.oninput=v.onchange=apply;
w.onclick=()=>{w.setAttribute('aria-pressed',w.getAttribute('aria-pressed')!=='true');apply()};
try{const s=localStorage.theme;if(s==='light'||s==='dark')root.dataset.theme=s}catch(e){}
document.getElementById('t').onclick=()=>{
const dark=root.dataset.theme?root.dataset.theme==='dark':matchMedia('(prefers-color-scheme:dark)').matches;
root.dataset.theme=dark?'light':'dark';try{localStorage.theme=root.dataset.theme}catch(e){}};
"""


def _row(e: Event) -> str:
    end = e.until or e.start
    if e.until:
        day, day_cls, month = f"{e.start.day}-{e.until.day}", "day run", e.until.strftime("%b")
    else:
        day, day_cls, month = str(e.start.day), "day", e.start.strftime("%b")
    style = f' style="background-image:url(&quot;{escape(e.image, quote=True)}&quot;)"' if e.image else ""
    time = "" if e.until else f"<span>{e.start:%H:%M}</span>"
    price = f'<span class="price">{escape(e.price)}</span>' if e.price else ""
    search = escape((e.title + " " + e.venue).lower(), quote=True)
    return (
        f'<a class="gig" href="{escape(e.url, quote=True)}" target="_blank" rel="noopener" '
        f'data-t="{search}" data-v="{escape(e.venue, quote=True)}" '
        f'data-d="{e.start:%Y-%m-%d}" data-u="{end:%Y-%m-%d}">'
        f'<span class="date">{e.start:%a}<span class="{day_cls}">{day}</span>{month}</span>'
        f'<span class="pic"{style}></span>'
        f'<span><span class="act">{escape(e.title)}</span>'
        f'<span class="meta"><span>{escape(e.venue)}</span>{time}{price}</span></span>'
        '<span class="cta">Tickets</span></a>'
    )


def _lede(events: list[Event]) -> str:
    if not events:
        return "No upcoming gigs found just now."
    first = events[0]
    return f"{len(events)} upcoming gigs. Next: {escape(first.title)}, {first.when(False)}."


def render(events: list[Event], generated: datetime) -> str:
    venues = sorted({e.venue for e in events})
    options = "".join(f'<option value="{escape(x, quote=True)}">{escape(x)}</option>' for x in venues)
    sections = [
        f"<section><h2>{month}</h2>{''.join(_row(e) for e in group)}</section>"
        for month, group in groupby(events, key=lambda e: e.start.strftime("%B %Y"))
    ]
    css = _CSS.substitute(
        light=theme.css_vars(theme.LIGHT),
        dark=theme.css_vars(theme.DARK),
        accent=theme.ACCENT,
        font=theme.FONT,
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{theme.TITLE}</title><style>{css}</style></head><body><main>"
        f'<header><h1 class="mark">{theme.TITLE}</h1><p class="lede">{_lede(events)}</p></header>'
        '<div class="tools"><input id="q" type="search" placeholder="Search act or venue" aria-label="Search act or venue">'
        f'<select id="v" aria-label="Venue"><option value="">All venues</option>{options}</select>'
        '<button id="w" type="button" aria-pressed="false">This weekend</button>'
        '<button id="t" type="button" aria-label="Switch between light and dark">Theme</button></div>'
        f"{''.join(sections)}"
        '<p id="none" class="empty" hidden>No gigs match. Try a different search or venue.</p>'
        f'<p class="empty">Updated {generated:%d %b %Y, %H:%M}. Checked every four hours by {theme.BRAND}.</p>'
        f"<script>{_JS}</script></main></body></html>"
    )
