"""Contact sheet of the middle of every frame in a burst folder: python scripts/sheet.py <folder> <out.png> [cols] [half-size]
Centres on the middle of the picture, where the rider stays whatever the window size."""
import sys, pathlib
from PIL import Image
folder, out = pathlib.Path(sys.argv[1]), sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
half = int(sys.argv[4]) if len(sys.argv) > 4 else 160
files = sorted(folder.glob("*.png"))
rows = (len(files) + cols - 1) // cols
sheet = Image.new("RGB", (240 * cols, 320 * rows))
for i, f in enumerate(files):
    im = Image.open(f); w, h = im.size
    sheet.paste(im.crop((w // 2 - half, h // 2 - int(half * 4 / 3) , w // 2 + half, h // 2 + int(half * 4 / 3))).resize((240, 320)), ((i % cols) * 240, (i // cols) * 320))
sheet.save(out); print("sheet", out, len(files))
