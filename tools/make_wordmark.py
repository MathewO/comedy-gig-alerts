"""Render the title as a PNG for the email (mail apps can't load web fonts).

The lettering is scaled so its ink spans the full 580px email column, and the
canvas is cropped to the letters plus a little padding.

Run after changing the title or font:  python tools/make_wordmark.py
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gigs import theme  # noqa: E402

DOCS = Path(__file__).resolve().parents[1] / "docs"
SCALE = 2      # drawn at 2x so it stays sharp on phones
WIDTH = 580    # email column width (1x px)
PAD_TOP, PAD_BOTTOM = 14, 8   # space above and below the letters (1x px)


def main() -> None:
    path = str(DOCS / "fonts" / "BebasNeue.ttf")
    probe = ImageFont.truetype(path, 200)
    box = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), theme.TITLE, font=probe)
    size = round(200 * (WIDTH * SCALE) / (box[2] - box[0]))
    font = ImageFont.truetype(path, size)
    left, top, right, bottom = ImageDraw.Draw(Image.new("RGB", (1, 1))).textbbox((0, 0), theme.TITLE, font=font)
    img = Image.new("RGB", (WIDTH * SCALE, (bottom - top) + (PAD_TOP + PAD_BOTTOM) * SCALE), theme.DARK["bg"])
    ImageDraw.Draw(img).text((-left, PAD_TOP * SCALE - top), theme.TITLE, font=font, fill=theme.DARK["ink"])
    img.save(DOCS / "wordmark.png", optimize=True)
    print("wrote", DOCS / "wordmark.png", img.size)


if __name__ == "__main__":
    main()
