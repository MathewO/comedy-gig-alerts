"""One look for the page and the email: plain, white, one system font.

Colours are named once here. The page uses them as CSS variables; the email
(which can't use variables) reads the LIGHT values directly.
"""

BRAND = "OBOT"  # sender name and sign-off only
TITLE = "OBOT - COMEDY"

# Sheffield orange, used sparingly: one top rule, link underlines, focus ring.
ACCENT = "#F47B20"

FONT = "-apple-system,BlinkMacSystemFont,'Helvetica Neue',Helvetica,Arial,sans-serif"

LIGHT = {
    "bg": "#FFFFFF",
    "subtle": "#F5F5F7",
    "line": "#E3E3E0",
    "ink": "#1D1D1F",
    "dim": "#6E6E73",
}
DARK = {
    "bg": "#111113",
    "subtle": "#1C1C1E",
    "line": "#2E2E30",
    "ink": "#F5F5F7",
    "dim": "#A1A1A6",
}


def css_vars(palette: dict[str, str]) -> str:
    return ";".join(f"--{k}:{v}" for k, v in palette.items())
