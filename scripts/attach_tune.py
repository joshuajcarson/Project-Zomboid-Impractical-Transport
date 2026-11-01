"""LIVE attachment tuner: tries several (offset, rotate) values for a held model in the running game, no reboot, and makes a contact sheet.
Needs a game left open by `python scripts/smoke_test.py play --keep`. The values are set on the model script's Bip01_Prop1 attachment in memory (the same objects the
game's debug attachment editor edits); nothing is written to disk, so a restart restores the models script. When a variant looks right, copy its numbers into
ImpracticalTransport_models.txt.
  python scripts/attach_tune.py <ItemType> <ModelName> "ox,oy,oz,rx,ry,rz" ["..." ...]
  e.g.  python scripts/attach_tune.py Unicycle Unicycle_3d "-0.1734,-0.105,-0.5744,-90,0,-163.2" "-0.1734,-0.105,-0.5744,-90,0,-175"
One row per variant; columns = the four screen facings (SE straight at the camera, NE, SW, NW). The sheet is previews/tune.png (git-ignored)."""
import os, pathlib, subprocess, sys, time
from PIL import Image
HERE = pathlib.Path(__file__).resolve().parent.parent
RL = pathlib.Path(os.environ.get("PZ_RL_REPO", r"C:\bench\project-zomboid-rl-based-players"))
USER = "Smoke1"
sys.path.insert(0, str(RL))
from pzrl.channel import ServerChannel
if len(sys.argv) < 4: sys.exit(__doc__)
item, model, variants = sys.argv[1], sys.argv[2], sys.argv[3:]
ch = ServerChannel()
def bot(*c):
    try: return ch.command("|".join(("bot", USER) + c), timeout=15)["msg"]
    except TimeoutError: return "no ack"
def pos(): return next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == USER)
def run(script, *a): subprocess.run([sys.executable, str(HERE / "scripts" / script), *map(str, a)], check=True)
FACINGS = (("SE", 1.5, 1.5), ("NE", 1.5, -1.5), ("SW", -1.5, 1.5), ("NW", -1.5, -1.5))
ch.command(f"admin|{USER}")
bot("smokeunequipaction"); time.sleep(7)
bot("smokechat", f'/additem "{USER}" ImpracticalTransport.{item}'); time.sleep(5)
bot("smokeequipaction", item); time.sleep(8)
bot("smokecalm", "1"); bot("smokeview", "3"); run("wake.py")
out = HERE / "previews"; out.mkdir(exist_ok=True)
rows = []
for v in variants:
    print(bot("smokeattach", model, v)); time.sleep(0.5)
    row = []
    for tag, dx, dy in FACINGS:
        p0 = pos(); bot("goto", f"{p0['x'] + dx:.1f}", f"{p0['y'] + dy:.1f}"); time.sleep(2.2); bot("stop"); time.sleep(1.6)
        f = out / f"tune_{len(rows)}_{tag}.png"; run("shoot.py", "shot", f)
        im = Image.open(f); w, h = im.size
        row.append(im.crop((w // 2 - 170, h // 2 - 227, w // 2 + 170, h // 2 + 227)).resize((240, 320)))
    rows.append(row)
sheet = Image.new("RGB", (240 * 4, 320 * len(rows)))
for r, row in enumerate(rows):
    for c, im in enumerate(row): sheet.paste(im, (c * 240, r * 320))
sheet.save(out / "tune.png"); print("sheet", out / "tune.png", "rows:", variants)
