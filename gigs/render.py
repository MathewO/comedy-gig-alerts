from datetime import datetime
from html import escape
from itertools import groupby
from string import Template

from . import theme
from .model import Event

_CSS = Template("""
:root{$dark;--accent:$accent;color-scheme:dark}
:root[data-theme=light]{$light;color-scheme:light}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 $font;-webkit-font-smoothing:antialiased}
body::before{content:"";display:block;height:3px;background:var(--accent)}
main{max-width:1000px;margin:0 auto;padding:0 24px 80px}
a{color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
header{text-align:center;padding:31px 0 12px}
.brand{display:inline-block}
.mark{margin:0;line-height:0}
.mark img{display:block;width:min(calc(100vw - 32px),460px);height:auto}
.lede{width:0;min-width:100%;margin:3px 0 0;color:var(--dim);font-size:clamp(.8rem,3.2vw,1rem);line-height:1.4;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;text-align:center}
.tools{display:flex;justify-content:center;gap:8px;flex-wrap:wrap;padding:4px 0 0}
.tools input,.tools select,.tools button{font:inherit;font-size:.95rem;color:var(--ink);background:var(--subtle);border:1px solid var(--line);border-radius:8px;padding:9px 14px}
.tools input{flex:0 1 260px}
.tools button{cursor:pointer;display:inline-flex;align-items:center;justify-content:center;width:42px;padding:0}
.tools button svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
h2{margin:44px 0 0;font-size:1rem;font-weight:600;text-align:center;color:var(--ink);letter-spacing:.04em}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(min(280px,100%),1fr));gap:40px 28px;padding:24px 0 0}
.gig{display:block;min-width:0;text-decoration:none;overflow-wrap:anywhere}
.gig[hidden],section[hidden]{display:none}
.pic{display:block;aspect-ratio:1/1;border-radius:6px;background:var(--subtle) center/cover no-repeat}
.when{display:block;margin-top:14px;font-size:.85rem;color:var(--dim)}
.act{display:block;margin-top:2px;font-size:1.15rem;font-weight:600;line-height:1.3}
.gig:hover .act{text-decoration:underline;text-decoration-color:var(--accent);text-underline-offset:3px}
.meta{display:block;margin-top:2px;color:var(--dim);font-size:.9rem}
.price{color:var(--ink);font-weight:600}
.cta{display:inline-block;margin-top:10px;font-size:.9rem;font-weight:600;border-bottom:2px solid var(--accent);padding-bottom:1px}
.empty{color:var(--dim);padding:32px 0 0;text-align:center}
@media (max-width:640px){header{padding:20px 0 10px}main{padding:0 16px 64px}
.grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:28px 14px}
.tools{display:grid;grid-template-columns:minmax(0,1fr) 42px}.tools input{grid-column:1/-1;width:100%}.tools select{width:100%;min-width:0}.act{font-size:1rem}.meta{font-size:.82rem}}
""")

_JS = """
const q=document.getElementById('q'),v=document.getElementById('v'),root=document.documentElement;
function apply(){const t=q.value.toLowerCase(),vv=v.value;
document.querySelectorAll('.gig').forEach(g=>{g.hidden=!((!t||g.dataset.t.includes(t))&&(!vv||g.dataset.v===vv))});
document.querySelectorAll('section').forEach(s=>{s.hidden=![...s.querySelectorAll('.gig')].some(g=>!g.hidden)});
document.getElementById('none').hidden=[...document.querySelectorAll('.gig')].some(g=>!g.hidden)}
q.oninput=v.onchange=apply;
function fit(){const l=document.querySelector('.lede'),m=document.querySelector('.mark');l.style.fontSize='';
const need=l.scrollWidth,box=m.getBoundingClientRect().width;
if(need>box){l.style.fontSize=(parseFloat(getComputedStyle(l).fontSize)*box/need*.98)+'px'}}
fit();document.fonts.ready.then(fit);addEventListener('resize',fit);
try{if(localStorage.theme==='light')root.dataset.theme='light'}catch(e){}
const tb=document.getElementById('t');
const SUN='<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
const MOON='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/></svg>';
const isDark=()=>root.dataset.theme!=='light';
function paint(){const d=isDark();tb.innerHTML=d?SUN:MOON;tb.setAttribute('aria-label',d?'Switch to light theme':'Switch to dark theme')}
tb.onclick=()=>{if(isDark())root.dataset.theme='light';else delete root.dataset.theme;try{localStorage.theme=isDark()?'dark':'light'}catch(e){}paint()};
paint();
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
    stamp = f"{checked.day} {checked:%b %Y} at {checked:%H:%M}"
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{theme.TITLE}</title><style>{css}</style></head><body><main>"
        f'<header><div class="brand"><h1 class="mark"><img src="title.webp" width="1160" height="184" alt="{theme.TITLE}"></h1>'
        f'<p class="lede">{len(events)} upcoming gigs, last checked {stamp}</p></div></header>'
        '<div class="tools"><input id="q" type="search" placeholder="Search act or venue" aria-label="Search act or venue">'
        f'<select id="v" aria-label="Venue"><option value="">All venues</option>{options}</select>'
        '<button id="t" type="button"></button></div>'
        f"{''.join(sections)}"
        '<p id="none" class="empty" hidden>No gigs match. Try a different search or venue.</p>'
        f"<script>{_JS}</script></main></body></html>"
    )
