"""Make the title images from a neon picture shot on a black and on a white background.

Because the same neon is shown on both backgrounds, the difference between them gives
real transparency and the true glow colour. Output:
  docs/title.webp  the page header (small, transparent)
  docs/title.png   the email header (transparent PNG; mail apps don't all read WebP)

Usage:  python tools/make_neon_title.py [on_black.png] [on_white.png]
Defaults: _neon_trials/4_header_dark.png and _neon_trials/neon_header_on_white.png (kept out of git).
"""
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parents[1]
BLACK = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "_neon_trials" / "4_header_dark.png"
WHITE = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "_neon_trials" / "neon_header_on_white.png"
DOCS = ROOT / "docs"
WIDTH = 1160   # 2x the email column, 2.5x the page header


def main() -> None:
    on_black = Image.open(BLACK).convert("RGB")
    on_white = Image.open(WHITE).convert("RGB").resize(on_black.size, Image.LANCZOS)
    b = np.asarray(on_black).astype(np.float32) / 255
    w = np.asarray(on_white).astype(np.float32) / 255
    alpha = np.clip(1 - (w - b).mean(axis=2), 0, 1)           # white minus black = how much light the neon blocks
    floor = float(np.median(alpha[:60, :]))                    # empty strip at the top should be 0; remove the faint haze
    alpha = np.clip((alpha - floor - 0.03) / (1 - floor - 0.03), 0, 1)
    colour = np.clip(np.where(alpha[..., None] > 0.01, b / np.maximum(alpha[..., None], 0.01), 0), 0, 1)
    img = Image.fromarray((np.dstack([colour, alpha]) * 255).astype(np.uint8), "RGBA")
    box = img.getchannel("A").point(lambda v: 255 if v > 30 else 0).getbbox()
    pad = 60
    crop = (max(box[0] - pad, 0), max(box[1] - pad, 0), min(box[2] + pad, img.width), min(box[3] + pad, img.height))

    def finish(im):
        return im.crop(crop).resize((WIDTH, round((crop[3] - crop[1]) * WIDTH / (crop[2] - crop[0]))), Image.LANCZOS)

    img = finish(img)
    img.save(DOCS / "title.png", optimize=True)
    img.save(DOCS / "title.webp", quality=92, method=6)
    for name in ("title.png", "title.webp"):
        print(name, img.size, os.path.getsize(DOCS / name) // 1024, "KB")


if __name__ == "__main__":
    main()
