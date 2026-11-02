"""Draw the title as a PNG for the email (mail apps can't load web fonts).

The lettering is scaled so it spans the full 580px email column, on a transparent
background in the brand orange (readable on white and on Gmail's dark mode).

Run after changing the title or font:  python tools/make_wordmark.py
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gigs import theme  # noqa: E402

DOCS = ROOT / "docs"
FONT = str(DOCS / "fonts" / "Retrolight.ttf")
SCALE = 2          # drawn at 2x so it stays sharp on phones
WIDTH = 580        # email column width (1x px)
PAD_TOP, PAD_BOTTOM = 14, 8   # space above and below the letters (1x px)


def main() -> None:
    measure = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    probe = ImageFont.truetype(FONT, 200)
    box = measure.textbbox((0, 0), theme.TITLE, font=probe)
    size = round(200 * (WIDTH * SCALE) / (box[2] - box[0]))
    font = ImageFont.truetype(FONT, size)
    left, top, right, bottom = measure.textbbox((0, 0), theme.TITLE, font=font)
    img = Image.new("RGBA", (WIDTH * SCALE, (bottom - top) + (PAD_TOP + PAD_BOTTOM) * SCALE), (0, 0, 0, 0))
    ImageDraw.Draw(img).text((-left, PAD_TOP * SCALE - top), theme.TITLE, font=font, fill=theme.ACCENT)
    img.save(DOCS / "wordmark.png", optimize=True)
    print("wrote", DOCS / "wordmark.png", img.size)


if __name__ == "__main__":
    main()
