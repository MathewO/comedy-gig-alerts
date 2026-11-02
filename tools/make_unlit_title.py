"""Draw the title in the Retrolight font as dark tubes, fitted letter by letter to the lit neon picture.

The lit title (docs/title.png) was drawn by an image model from this font, so its letters sit a few
pixels off the real glyphs. To make the light/dark switch a clean fade, each glyph is rendered from the
font, then scaled and shifted to the position where it best matches the neon's bright tube cores.

Needs docs/fonts/Retrolight.ttf (personal-use demo font) and docs/title.png.
Writes docs/title-off.webp (same size as the lit one).

    python tools/make_unlit_title.py
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from gigs import theme  # noqa: E402

DOCS = ROOT / "docs"
FONT = str(DOCS / "fonts" / "Retrolight.ttf")
INK = (29, 29, 31)        # the light theme's ink
S = 2                      # work at 2x, then average down for smooth edges
SX = (0.94, 0.96, 0.98, 1.0, 1.02, 1.04, 1.06)   # per-letter width scales tried
SY = (1.00, 1.04, 1.08, 1.12, 1.16, 1.20)         # per-letter height scales tried
REACH = 60                 # search +/- this many work pixels around the expected spot


def ncc(field: np.ndarray, patch: np.ndarray) -> np.ndarray:
    """Normalised cross-correlation of patch over field (valid positions only)."""
    h, w = field.shape
    ph, pw = patch.shape
    fh, fw = h + ph, w + pw
    ones = np.ones_like(patch)
    centred = patch - patch.mean()
    f = np.fft.rfft2(field, (fh, fw))
    num = np.fft.irfft2(f * np.conj(np.fft.rfft2(centred, (fh, fw))), (fh, fw))[: h - ph + 1, : w - pw + 1]
    s1 = np.fft.irfft2(f * np.conj(np.fft.rfft2(ones, (fh, fw))), (fh, fw))[: h - ph + 1, : w - pw + 1]
    s2 = np.fft.irfft2(np.fft.rfft2(field**2, (fh, fw)) * np.conj(np.fft.rfft2(ones, (fh, fw))), (fh, fw))[
        : h - ph + 1, : w - pw + 1
    ]
    var = np.maximum(s2 - s1**2 / patch.size, 1e-6)
    return num / (np.sqrt(var) * np.sqrt((centred**2).sum()) + 1e-9)


def neon_cores() -> np.ndarray:
    """Bright tube cores of the lit picture at work scale, slightly blurred so matching is smooth."""
    lit = Image.open(DOCS / "title.png").convert("RGBA")
    a = np.asarray(lit).astype(np.float32) / 255
    core = ((a[..., 3] > 0.5) & (a[..., 1] > 0.5)).astype(np.uint8) * 255
    img = Image.fromarray(core).resize((lit.width * S, lit.height * S), Image.LANCZOS).filter(ImageFilter.GaussianBlur(1.6))
    return np.asarray(img).astype(np.float32) / 255, lit.size


def glyph_mask(ch: str, size: float, sy: float) -> Image.Image:
    font = ImageFont.truetype(FONT, round(size))
    left, top, right, bottom = font.getbbox(ch)
    img = Image.new("L", (right - left + 8, bottom - top + 8), 0)
    ImageDraw.Draw(img).text((4 - left, 4 - top), ch, font=font, fill=255)
    box = img.getbbox()
    img = img.crop(box)
    return img.resize((img.width, max(1, round(img.height * sy))), Image.LANCZOS)


def main() -> None:
    field, (W, H) = neon_cores()
    title = theme.TITLE
    ys, xs = np.where(field > 0.5)
    left, right, top, bottom = xs.min(), xs.max(), ys.min(), ys.max()
    base = 142 * S * (right - left) / (1098 * S)   # size that gives the neon's overall width (measured earlier at 1x: 142)
    probe = ImageFont.truetype(FONT, round(base))
    out = np.zeros(field.shape, np.float32)
    total = []
    for i, ch in enumerate(title):
        # expected left edge of this glyph if the whole word were set in the font and centred on the neon
        word_w = probe.getlength(title)
        x0 = left + (right - left - word_w) / 2 + probe.getlength(title[:i])
        best = None
        for sx in SX:
            for sy in SY:
                patch = np.asarray(glyph_mask(ch, base * sx, sy)).astype(np.float32) / 255
                ph, pw = patch.shape
                ex = int(x0 + probe.getbbox(ch)[0])          # expected patch left
                ey = int((top + bottom) / 2 - ph / 2)         # expected patch top (centred on the neon's lettering)
                xa, xb = max(ex - REACH, 0), min(ex + pw + REACH, field.shape[1])
                ya, yb = max(ey - REACH, 0), min(ey + ph + REACH, field.shape[0])
                win = field[ya:yb, xa:xb]
                if win.shape[0] < ph or win.shape[1] < pw:
                    continue
                score = ncc(win, patch)
                j = np.unravel_index(np.argmax(score), score.shape)
                if best is None or score[j] > best[0]:
                    best = (float(score[j]), xa + j[1], ya + j[0], patch)
        s, px, py, patch = best
        total.append(s)
        h, w = patch.shape
        out[py : py + h, px : px + w] = np.maximum(out[py : py + h, px : px + w], patch)
        print(f"{ch}: match {s:.2f} at ({px / S:.1f}, {py / S:.1f}) size {w / S:.0f}x{h / S:.0f}")
    print(f"mean match {np.mean(total):.3f}")
    alpha = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
    rgba = Image.new("RGBA", (W, H), INK + (0,))
    rgba.putalpha(alpha)
    rgba.save(DOCS / "title-off.webp", quality=92, method=6)
    print("wrote docs/title-off.webp", rgba.size)


if __name__ == "__main__":
    main()
