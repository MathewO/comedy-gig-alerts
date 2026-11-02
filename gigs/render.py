from datetime import datetime
from html import escape
from itertools import groupby
from string import Template

from . import theme
from .model import Event

_CSS = Template("""
@font-face{font-family:"Bebas Neue";src:url(fonts/BebasNeue.ttf) format("truetype");font-display:swap}
:root{$light;--accent:$accent;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){$dark;color-scheme:dark}}
:root[data-theme=dark]{$dark;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 $font;-webkit-font-smoothing:antialiased}
body::before{content:"";display:block;height:3px;background:var(--accent)}
main{max-width:1000px;margin:0 auto;padding:0 24px 80px}
a{color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
header{text-align:center;padding:64px 0 32px}
.mark{margin:0;font-family:"Bebas Neue",Impact,$font;font-size:4.6rem;font-weight:400;letter-spacing:.07em;line-height:1;text-transform:uppercase}
.lede{margin:16px 0 0;color:var(--dim);line-height:1.6}
.tools{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;padding:20px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.tools input,.tools select,.tools button{font:inherit;font-size:.95rem;color:var(--ink);background:var(--subtle);border:1px solid var(--line);border-radius:8px;padding:9px 14px}
.tools input{flex:0 1 260px}
.tools button{cursor:pointer}
h2{margin:44px 0 0;font-size:1rem;font-weight:600;text-align:center;color:var(--ink);letter-spacing:.04em}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:40px 28px;padding:24px 0 0}
.gig{display:block;text-decoration:none}
.gig[hidden],section[hidden]{display:none}
.pic{display:block;aspect-ratio:1/1;border-radius:6px;background:var(--subtle) center/cover no-repeat}
.when{display:block;margin-top:14px;font-size:.85rem;color:var(--dim)}
.act{display:block;margin-top:2px;font-size:1.15rem;font-weight:600;line-height:1.3}
.gig:hover .act{text-decoration:underline;text-decoration-color:var(--accent);text-underline-offset:3px}
.meta{display:block;margin-top:2px;color:var(--dim);font-size:.9rem}
.price{color:var(--ink);font-weight:600}
.cta{display:inline-block;margin-top:10px;font-size:.9rem;font-weight:600;border-bottom:2px solid var(--accent);padding-bottom:1px}
.empty{color:var(--dim);padding:32px 0 0;text-align:center}
@media (max-width:640px){.mark{font-size:3rem}header{padding:44px 0 26px}main{padding:0 16px 64px}
.grid{grid-template-columns:repeat(2,1fr);gap:28px 14px}.act{font-size:1rem}.meta{font-size:.82rem}}
""")

_JS = """
const q=document.getElementById('q'),v=document.getElementById('v'),root=document.documentElement;
function apply(){const t=q.value.toLowerCase(),vv=v.value;
document.querySelectorAll('.gig').forEach(g=>{g.hidden=!((!t||g.dataset.t.includes(t))&&(!vv||g.dataset.v===vv))});
document.querySelectorAll('section').forEach(s=>{s.hidden=![...s.querySelectorAll('.gig')].some(g=>!g.hidden)});
document.getElementById('none').hidden=[...document.querySelectorAll('.gig')].some(g=>!g.hidden)}
q.oninput=v.onchange=apply;
try{const s=localStorage.theme;if(s==='light'||s==='dark')root.dataset.theme=s}catch(e){}
document.getElementById('t').onclick=()=>{
const dark=root.dataset.theme?root.dataset.theme==='dark':matchMedia('(prefers-color-scheme:dark)').matches;
root.dataset.theme=dark?'light':'dark';try{localStorage.theme=root.dataset.theme}catch(e){}};
"""


def when_text(e: Event) -> str:
    if e.until:
        return f"{e.start:%a} {e.start.day} - {e.until:%a} {e.until.day} {e.until:%b}"
    return f"{e.start:%a} {e.start.day} {e.start:%b}, {e.start:%H:%M}"


def _card(e: Event) -> str:
    style = f' style="background-image:url(&quot;{escape(e.image, quote=True)}&quot;)"' if e.image else ""
    price = f' <span class="price">{escape(e.price)}</span>' if e.price else ""
    search = escape((e.title + " " + e.venue).lower(), quote=True)
    return (
        f'<a class="gig" href="{escape(e.url, quote=True)}" target="_blank" rel="noopener" '
        f'data-t="{search}" data-v="{escape(e.venue, quote=True)}">'
        f'<span class="pic"{style}></span>'
        f'<span class="when">{when_text(e)}</span>'
        f'<span class="act">{escape(e.title)}</span>'
        f'<span class="meta">{escape(e.venue)}{price}</span>'
        '<span class="cta">Tickets</span></a>'
    )


def render(events: list[Event], checked: datetime) -> str:
    venues = sorted({e.venue for e in events})
    options = "".join(f'<option value="{escape(x, quote=True)}">{escape(x)}</option>' for x in venues)
    sections = [
        f'<section><h2>{month}</h2><div class="grid">{"".join(_card(e) for e in group)}</div></section>'
        for month, group in groupby(events, key=lambda e: e.start.strftime("%B %Y"))
    ]
    css = _CSS.substitute(
        light=theme.css_vars(theme.LIGHT),
        dark=theme.css_vars(theme.DARK),
        accent=theme.ACCENT,
        font=theme.FONT,
    )
    stamp = f"{checked.day} {checked:%b %Y, %H:%M}"
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{theme.TITLE}</title><style>{css}</style></head><body><main>"
        f'<header><h1 class="mark">{theme.TITLE}</h1>'
        f'<p class="lede">{len(events)} upcoming gigs<br>Last checked {stamp}</p></header>'
        '<div class="tools"><input id="q" type="search" placeholder="Search act or venue" aria-label="Search act or venue">'
        f'<select id="v" aria-label="Venue"><option value="">All venues</option>{options}</select>'
        '<button id="t" type="button">Theme</button></div>'
        f"{''.join(sections)}"
        '<p id="none" class="empty" hidden>No gigs match. Try a different search or venue.</p>'
        f"<script>{_JS}</script></main></body></html>"
    )
