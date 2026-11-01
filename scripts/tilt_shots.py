"""Rest pictures of every UniCal item (tools/make_tilt_calibration.py) at the four real screen facings, for a game left open by `smoke_test.py play --keep`.
Facings are the isometric diagonals: southeast is straight at the camera (key S), northeast right (D), southwest left (A), northwest away (W).
One sheet, one row per item, columns SE, NE, SW, NW, lands in previews/calibration/tilt.png (git-ignored).
  python scripts/tilt_shots.py [UniCal1 UniCal3 ...]   (default: every UniCal item in the generated file)"""
import os, pathlib, re, subprocess, sys, time
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
def pos(): return next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == USER)
def run(script, *a): subprocess.run([sys.executable, str(HERE / "scripts" / script), *map(str, a)], check=True)
items = HERE / "Contents/mods/ImpracticalTransport/42/media/scripts/ImpracticalTransport_tilt_cal_items.txt"
names = sys.argv[1:] or (re.findall(r"item ((?:Uni|Pogo)Cal\d+)", items.read_text(encoding="utf-8")) if items.exists() else [])      # any item type works, e.g. Unicycle Tricycle PogoStick
labels = dict(re.findall(r"item ((?:Uni|Pogo)Cal\d+)\s*\{\s*DisplayName = ([^,]+),", items.read_text(encoding="utf-8"))) if items.exists() else {}
FACINGS = (("SE", 1.5, 1.5), ("NE", 1.5, -1.5), ("SW", -1.5, 1.5), ("NW", -1.5, -1.5))
OUT.mkdir(parents=True, exist_ok=True)
ch.command(f"admin|{USER}"); bot("smokecalm", "1"); bot("smokeview", "3"); run("wake.py")
rows = []
for name in names:
    bot("smokeunequipaction"); time.sleep(6)
    bot("smokechat", f'/additem "{USER}" ImpracticalTransport.{name}'); time.sleep(4)      # the smoke test removes the extra items again
    bot("smokeequipaction", name); time.sleep(7)
    row = []
    for tag, dx, dy in FACINGS:
        p0 = pos(); bot("goto", f"{p0['x'] + dx:.1f}", f"{p0['y'] + dy:.1f}"); time.sleep(2.2)
        bot("stop"); time.sleep(2.0)
        f = OUT / f"{name}_{tag}.png"; run("shoot.py", "shot", f)
        im = Image.open(f); w, h = im.size
        row.append(im.crop((w // 2 - 170, h // 2 - 227, w // 2 + 170, h // 2 + 227)).resize((240, 320)))
    rows.append((name, row)); print(name, labels.get(name, ""))
sheet = Image.new("RGB", (240 * 4, 320 * len(rows)))
for r, (_, row) in enumerate(rows):
    for c, im in enumerate(row): sheet.paste(im, (c * 240, r * 320))
sheet.save(OUT / "tilt.png"); print("sheet", OUT / "tilt.png", [labels.get(n, n) for n, _ in rows])
