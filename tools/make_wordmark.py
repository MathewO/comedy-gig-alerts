"""Render the title as a PNG for the email (mail apps can't load web fonts).

Run after changing the title or font:  python tools/make_wordmark.py
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gigs import theme  # noqa: E402

DOCS = Path(__file__).resolve().parents[1] / "docs"
SCALE = 2          # drawn at 2x so it stays sharp on phones
WIDTH, HEIGHT = 580, 84
TRACKING = 5       # extra pixels between letters (1x)
SIZE = 62


def main() -> None:
    font = ImageFont.truetype(str(DOCS / "fonts" / "BebasNeue.ttf"), SIZE * SCALE)
    img = Image.new("RGB", (WIDTH * SCALE, HEIGHT * SCALE), theme.LIGHT["bg"])
    draw = ImageDraw.Draw(img)
    text = theme.TITLE
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + TRACKING * SCALE * (len(text) - 1)
    x = (img.width - total) / 2
    ascent, descent = font.getmetrics()
    y = (img.height - (ascent + descent)) / 2
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=theme.LIGHT["ink"])
        x += w + TRACKING * SCALE
    img.save(DOCS / "wordmark.png", optimize=True)
    print("wrote", DOCS / "wordmark.png", img.size)


if __name__ == "__main__":
    main()
