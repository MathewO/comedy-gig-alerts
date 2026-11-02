from datetime import datetime
from html import escape
from itertools import groupby

from . import theme
from .model import Event

_CSS = """
:root{%(dark)s;--led:%(led)s;color-scheme:dark}
:root[data-theme=light]{%(light)s;color-scheme:light}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 %(body)s}
main{max-width:820px;margin:0 auto;padding:20px 16px 72px}
a{color:inherit}
:focus-visible{outline:3px solid var(--led);outline-offset:2px}
h1,h2,.act,.day{font-family:%(display)s}
.top{display:flex;align-items:center;gap:18px;margin:8px 0 22px}
.bot{flex:0 0 88px;width:88px;height:auto}
.eyes{transform-origin:60px 60px}
@media (prefers-reduced-motion:no-preference){.eyes{animation:blink .5s ease-in-out .8s 1}}
@keyframes blink{50%%{transform:scaleY(.08)}}
.bubble{position:relative;background:var(--panel);border:2px solid var(--line);border-radius:18px;padding:12px 16px}
.bubble::before{content:"";position:absolute;left:-10px;top:50%%;margin-top:-9px;border:9px solid transparent;border-left:0;border-right-color:var(--line)}
.bubble::after{content:"";position:absolute;left:-6px;top:50%%;margin-top:-7px;border:7px solid transparent;border-left:0;border-right-color:var(--panel)}
h1{font-size:1.7rem;line-height:1.15;margin:0 0 4px;font-weight:800}
.bubble p{margin:0;color:var(--dim)}
.bubble b{color:var(--ink)}
.tools{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:6px}
.tools input,.tools select,.tools button{font:inherit;color:var(--ink);background:var(--panel);border:2px solid var(--line);border-radius:12px;padding:9px 12px}
.tools input{flex:1 1 200px}
.tools button{cursor:pointer}
.tools button[aria-pressed=true]{background:var(--led);border-color:var(--led);color:%(chassis)s;font-weight:700}
h2{position:sticky;top:0;z-index:2;margin:26px 0 8px;padding:8px 0;font-size:1.15rem;font-weight:600;color:var(--dim);background:var(--bg)}
.gig{display:flex;align-items:center;gap:14px;padding:10px;margin-bottom:8px;background:var(--panel);border:2px solid var(--line);border-radius:16px;text-decoration:none}
.gig:hover{border-color:var(--led)}
.date{flex:0 0 62px;background:%(chassis)s;border-radius:10px;padding:6px 0 7px;text-align:center;color:var(--led);line-height:1}
.date small{display:block;font-size:.72rem;letter-spacing:.04em;opacity:.85}
.day{display:block;font-size:1.6rem;font-weight:800;margin:3px 0 2px}
.day.run{font-size:1.15rem;margin:7px 0 6px}
.pic{flex:0 0 76px;height:76px;border-radius:10px;background:var(--panel-hi) center/cover no-repeat}
.body{flex:1;min-width:0}
.act{display:block;font-size:1.1rem;font-weight:600;line-height:1.25}
.meta{display:flex;flex-wrap:wrap;gap:2px 14px;color:var(--dim);font-size:.9rem;margin-top:2px}
.price{color:var(--ink);font-weight:600}
.cta{flex:0 0 auto;background:var(--led);color:%(chassis)s;font-weight:700;border-radius:999px;padding:8px 16px}
.empty{color:var(--dim);padding:28px 0}
@media (max-width:560px){.cta{display:none}.pic{flex-basis:64px;height:64px}.bot{flex-basis:64px;width:64px}}
"""

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
try{if(localStorage.theme==='light')root.dataset.theme='light'}catch(e){}
document.getElementById('t').onclick=()=>{const l=root.dataset.theme!=='light';
if(l)root.dataset.theme='light';else delete root.dataset.theme;
try{localStorage.theme=l?'light':'dark'}catch(e){}};
"""


def _row(e: Event) -> str:
    end = e.until or e.start
    if e.until:
        day = f"{e.start.day}-{e.until.day}"
        day_cls, month = "day run", e.until.strftime("%b")
    else:
        day, day_cls, month = str(e.start.day), "day", e.start.strftime("%b")
    pic = ""
    if e.image:
        pic = f'<span class="pic" style="background-image:url(&quot;{escape(e.image, quote=True)}&quot;)"></span>'
    time = "" if e.until else f"<span>{e.start:%H:%M}</span>"
    price = f'<span class="price">{escape(e.price)}</span>' if e.price else ""
    search = escape((e.title + " " + e.venue).lower(), quote=True)
    return (
        f'<a class="gig" href="{escape(e.url, quote=True)}" target="_blank" rel="noopener" '
        f'data-t="{search}" data-v="{escape(e.venue, quote=True)}" '
        f'data-d="{e.start:%Y-%m-%d}" data-u="{end:%Y-%m-%d}">'
        f'<span class="date"><small>{e.start:%a}</small><span class="{day_cls}">{day}</span><small>{month}</small></span>'
        f'{pic}<span class="body"><span class="act">{escape(e.title)}</span>'
        f'<span class="meta"><span>{escape(e.venue)}</span>{time}{price}</span></span>'
        '<span class="cta">Tickets</span></a>'
    )


def _bubble(events: list[Event]) -> str:
    if not events:
        return "<p>I can't find any gigs just now. I'll keep looking.</p>"
    first = events[0]
    return (
        f"<p><b>Beep boop! {len(events)} gigs coming up.</b> "
        f"First is {escape(first.title)} at {escape(first.venue)} on {first.when(False)}.</p>"
    )


def render(events: list[Event], generated: datetime) -> str:
    venues = sorted({e.venue for e in events})
    options = "".join(f'<option value="{escape(x, quote=True)}">{escape(x)}</option>' for x in venues)
    sections = [
        f"<section><h2>{month}</h2>{''.join(_row(e) for e in group)}</section>"
        for month, group in groupby(events, key=lambda e: e.start.strftime("%B %Y"))
    ]
    css = _CSS % {
        "dark": theme.css_vars(theme.DARK),
        "light": theme.css_vars(theme.LIGHT),
        "led": theme.LED,
        "chassis": theme.CHASSIS,
        "body": theme.BODY_FONT,
        "display": theme.DISPLAY_FONT,
    }
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>Sheffield comedy</title>"
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        f'<link rel="stylesheet" href="{theme.FONT_LINK}"><style>{css}</style></head><body><main>'
        f'<div class="top">{theme.robot_svg()}<div class="bubble"><h1>Sheffield comedy</h1>{_bubble(events)}</div></div>'
        '<div class="tools"><input id="q" type="search" placeholder="Search act or venue" aria-label="Search act or venue">'
        f'<select id="v" aria-label="Venue"><option value="">All venues</option>{options}</select>'
        '<button id="w" type="button" aria-pressed="false">This weekend</button>'
        '<button id="t" type="button" aria-label="Switch between dark and light">Theme</button></div>'
        f"{''.join(sections)}"
        '<p id="none" class="empty" hidden>No gigs match. Try a different search or venue.</p>'
        f'<p class="empty">Last changed {generated:%d %b %Y, %H:%M}. O-BOT checks every 4 hours.</p>'
        f"<script>{_JS}</script></main></body></html>"
    )
