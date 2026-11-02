"""One look for the page and the email: O-BOT, the friendly family robot.

Colours are named once here. The page uses them as CSS variables; the email
(which can't use variables) reads the same values directly.
"""

BRAND = "O-BOT"
TAGLINE = "The friendly family robot"

# Sheffield's orange, black and steel grey. Always the same in both themes:
# the robot's eyes, the buttons and the little date panels.
LED = "#F47B20"      # bright works-orange
CHASSIS = "#141312"  # forge black; text on orange, date panels, robot pupils

DARK = {
    "bg": "#1C1B1A",
    "panel": "#292725",
    "panel-hi": "#38352F",
    "line": "#524D46",
    "ink": "#F6F2EB",
    "dim": "#B8B1A6",
}
LIGHT = {
    "bg": "#E3E6E8",
    "panel": "#FFFFFF",
    "panel-hi": "#D3D8DC",
    "line": "#B7BEC4",
    "ink": "#1C1B1A",
    "dim": "#565C62",
}

DISPLAY_FONT = "'Baloo 2','Arial Rounded MT Bold','Trebuchet MS',Verdana,sans-serif"
BODY_FONT = "system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
FONT_LINK = "https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;800&display=swap"


def css_vars(palette: dict[str, str]) -> str:
    return ";".join(f"--{k}:{v}" for k, v in palette.items())


def robot_svg() -> str:
    """O-BOT's face. Fills use the page's CSS variables so it follows the theme."""
    return (
        '<svg class="bot" viewBox="0 0 120 112" role="img" aria-label="O-BOT the robot">'
        f'<line x1="60" y1="6" x2="60" y2="24" stroke="var(--line)" stroke-width="5" stroke-linecap="round"/>'
        f'<circle cx="60" cy="8" r="7" fill="{LED}"/>'
        '<rect x="4" y="46" width="12" height="28" rx="6" fill="var(--panel-hi)" stroke="var(--line)" stroke-width="3"/>'
        '<rect x="104" y="46" width="12" height="28" rx="6" fill="var(--panel-hi)" stroke="var(--line)" stroke-width="3"/>'
        '<rect x="14" y="24" width="92" height="82" rx="26" fill="var(--panel-hi)" stroke="var(--line)" stroke-width="4"/>'
        f'<g class="eyes" fill="{LED}"><circle cx="43" cy="60" r="12"/><circle cx="77" cy="60" r="12"/></g>'
        f'<g fill="{CHASSIS}"><circle cx="46" cy="57" r="4"/><circle cx="80" cy="57" r="4"/></g>'
        '<g stroke="var(--line)" stroke-width="4" stroke-linecap="round"><line x1="44" y1="90" x2="76" y2="90"/>'
        '<line x1="50" y1="98" x2="70" y2="98"/></g></svg>'
    )


def robot_email() -> str:
    """The same face for email, which can't use SVG or CSS variables: two glowing eyes on a rounded head."""
    eye = (
        f'<td width="20" height="20" style="width:20px;height:20px;background:{LED};border-radius:10px;'
        'font-size:0;line-height:0">&nbsp;</td>'
    )
    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" align="center"><tr>'
        f'<td style="background:{DARK["panel-hi"]};border:3px solid {DARK["line"]};border-radius:22px;padding:16px 20px">'
        f'<table role="presentation" cellpadding="0" cellspacing="0"><tr>{eye}<td width="22">&nbsp;</td>{eye}</tr></table>'
        f'<div style="height:3px;width:34px;background:{DARK["line"]};border-radius:2px;margin:12px auto 0;font-size:0">&nbsp;</div>'
        "</td></tr></table>"
    )
