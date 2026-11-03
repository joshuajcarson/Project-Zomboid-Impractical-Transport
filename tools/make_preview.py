"""Draws the Workshop preview.png (256x256) and the in-mod poster.png (512x512) from primitives (PIL only, no game art):
  python tools/make_preview.py
Output: preview.png at the repo root (the Workshop folder root) and Contents/mods/ImpracticalTransport/42/poster.png."""
import pathlib
from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent

def draw(size):
    s = size / 256
    im = Image.new("RGB", (size, size), (38, 52, 44))
    d = ImageDraw.Draw(im)
    cream, red, w = (230, 220, 190), (200, 80, 60), max(2, int(7 * s))
    d.rectangle([0, 190 * s, size, size], fill=(70, 62, 52))                     # ground
    for cx, r in ((70, 38), (186, 38)):                                          # two wheels
        d.ellipse([(cx - r) * s, (190 - 2 * r) * s, (cx + r) * s, 190 * s], outline=cream, width=w)
        d.ellipse([(cx - 5) * s, (190 - r - 5) * s, (cx + 5) * s, (190 - r + 5) * s], fill=cream)
    d.line([70 * s, 152 * s, 120 * s, 90 * s, 186 * s, 152 * s], fill=red, width=w)   # frame
    d.line([120 * s, 90 * s, 120 * s, 60 * s], fill=red, width=w)
    d.ellipse([100 * s, 44 * s, 140 * s, 64 * s], fill=(240, 200, 70))           # seat
    return im

draw(256).save(ROOT / "preview.png")
draw(512).save(ROOT / "Contents/mods/ImpracticalTransport/42/poster.png")
print("wrote preview.png and 42/poster.png")
