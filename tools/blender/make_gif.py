"""Stitch previews/demo/{side,front}_NN.png into previews/pogo_hop_demo.gif (side and front next to each other), 30 fps, looping."""
import pathlib
from PIL import Image
import os
NAME = os.environ.get("CLIP", "Bob_PogoHop")
D = pathlib.Path(__file__).resolve().parents[2] / "previews"
frames = []
for i in range(24):
    a, b = (Image.open(D / "demo" / f"{NAME}_{v}_{i:02d}.png").convert("RGB") for v in ("side", "front"))
    im = Image.new("RGB", (a.width + b.width, a.height)); im.paste(a, (0, 0)); im.paste(b, (a.width, 0)); frames.append(im)
frames[0].save(D / f"{NAME}_demo.gif", save_all=True, append_images=frames[1:], duration=1000 // 30 * 2, loop=0, optimize=True)  # x2: 24 frames at 15 fps is 1.6 s per hop, slow enough to read
