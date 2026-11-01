"""Screenshots of every calibration stick (tools/make_calibration.py) for a game left open by `smoke_test.py play --keep`.
For each PogoCal<i>: equip it, a picture at rest facing each of four directions, then a wide circle with a picture at eight points; one contact
sheet per stick (top row and the next: rest facing east, south, west, north; then the eight circle points) lands in previews/calibration/ (git-ignored).
This mirrors the human test. Pick the stick that leans toward the way the rider faces or travels with the pads under the feet.
  python scripts/calibrate_shots.py [1 2 3]      only those sticks (default: all PogoCal items in the generated items file)"""
import math, os, pathlib, re, subprocess, sys, time
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent.parent
RL = pathlib.Path(os.environ.get("PZ_RL_REPO", r"C:\bench\project-zomboid-rl-based-players"))
USER = "Smoke1"
OUT = HERE / "previews" / "calibration"
sys.path.insert(0, str(RL))
from pzrl.channel import ServerChannel

ch = ServerChannel()
def bot(*c):
    try: return ch.command("|".join(("bot", USER) + c), timeout=15)["msg"]
    except TimeoutError: return "no ack"
def pos():
    return next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == USER)
def shoot(*args):
    subprocess.run([sys.executable, str(HERE / "scripts" / "shoot.py"), *map(str, args)], check=True)
def crop(path):   # the camera follows the rider, who stays near the middle of the 640x480 window (the rider's feet reach the bottom edge)
    return Image.open(path).crop((140, 0, 500, 480)).resize((240, 320))

items = HERE / "Contents/mods/ImpracticalTransport/42/media/scripts/ImpracticalTransport_calibration_items.txt"
names = re.findall(r"item (PogoCal\d+)", items.read_text(encoding="utf-8")) if items.exists() else []
want = [a if not a.isdigit() else f"PogoCal{a}" for a in sys.argv[1:]] or names   # a bare number means PogoCal<n>; any other word is an item type, e.g. PogoStick
labels = dict(re.findall(r"item (PogoCal\d+)\s*\{\s*DisplayName = ([^,]+),", items.read_text(encoding="utf-8"))) if items.exists() else {}
OUT.mkdir(parents=True, exist_ok=True)
bot("smokeview", "6")
for name in want:
    bot("smokeunequipaction"); time.sleep(5)
    bot("smokeequipaction", name); time.sleep(7)
    tag = OUT / name; tag.mkdir(exist_ok=True)
    # at rest facing each way: a short hop that way, then stop (the rider keeps facing where it last moved)
    for k, (dx, dy) in enumerate(((1.5, 0), (0, 1.5), (-1.5, 0), (0, -1.5))):
        p0 = pos(); bot("goto", f"{p0['x'] + dx:.1f}", f"{p0['y'] + dy:.1f}"); time.sleep(2.5)
        bot("stop"); time.sleep(1.5); shoot("shot", tag / f"rest{k}.png")
    # a wide circle (radius 5 tiles) around where it stands, one picture while hopping towards each of eight points
    c = pos(); cx, cy = c["x"] - 5, c["y"]
    for k in range(8):
        a = math.radians(45 * (k + 1))
        bot("goto", f"{cx + 5 * math.cos(a):.1f}", f"{cy + 5 * math.sin(a):.1f}"); time.sleep(3.0)
        shoot("shot", tag / f"circle{k}.png")
    bot("stop"); time.sleep(1)
    frames = sorted(tag.glob("rest*.png")) + sorted(tag.glob("circle*.png"))
    sheet = Image.new("RGB", (240 * 4, 320 * 3))
    for i, f in enumerate(frames[:12]): sheet.paste(crop(f), ((i % 4) * 240, (i // 4) * 320))
    sheet.save(OUT / f"{name}.png"); print("sheet", OUT / f"{name}.png", labels.get(name, ""))
