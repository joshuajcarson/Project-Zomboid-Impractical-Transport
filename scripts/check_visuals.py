"""Screenshot checks for a game left open by `smoke_test.py play --keep`, one contact sheet each in previews/visual/:
  mount     equip the stick and watch the rider hop on (Bob_PogoMount)
  hop       a few frames of walking
  run       the real Left Shift held while walking (W)
  stumble   a forced stumble
  dismount  put the stick away (Bob_PogoDismount)
  icon      the inventory panel with the item list (UI shown)
  python scripts/check_visuals.py [mount hop run stumble dismount icon]   (default: all)"""
import ctypes, os, pathlib, subprocess, sys, time
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent.parent
RL = pathlib.Path(os.environ.get("PZ_RL_REPO", r"C:\bench\project-zomboid-rl-based-players"))
USER = "Smoke1"
OUT = HERE / "previews" / "visual"
sys.path.insert(0, str(RL))
from pzrl.channel import ServerChannel

ch = ServerChannel()
u = ctypes.windll.user32
key = lambda scan, down: u.keybd_event(0, scan, 8 | (0 if down else 2), 0)
def bot(*c):
    try: return ch.command("|".join(("bot", USER) + c), timeout=15)["msg"]
    except TimeoutError: return "no ack"
def pos(): return next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == USER)
def shoot(*a): subprocess.run([sys.executable, str(HERE / "scripts" / "shoot.py"), *map(str, a)], check=True)
def sheet(name, folder, cols=4, rows=3, box=(140, 0, 500, 480), size=(240, 320)):
    files = sorted(folder.glob("*.png"))[:cols * rows]
    out = Image.new("RGB", (size[0] * cols, size[1] * rows))
    for i, f in enumerate(files): out.paste(Image.open(f).crop(box).resize(size), ((i % cols) * size[0], (i // cols) * size[1]))
    out.save(OUT / f"{name}.png"); print("sheet", OUT / f"{name}.png")
def home(): bot("goto", "5385", "10114"); time.sleep(9); bot("stop"); time.sleep(1)

OUT.mkdir(parents=True, exist_ok=True)
want = sys.argv[1:] or ["mount", "hop", "run", "stumble", "dismount", "icon"]
bot("smokeview", "6")
if "mount" in want:
    bot("smokeunequipaction"); time.sleep(7); home()
    shoot("shot", OUT / "raise.png")                      # window to the front first: the mount lasts under a second
    bot("smokeequipaction", "PogoStick"); shoot("burst", OUT / "mount", 20, 8); sheet("mount", OUT / "mount", cols=5, rows=4, size=(192, 256))
if "hop" in want:
    bot("goto", "5420", "10114"); time.sleep(2); shoot("burst", OUT / "hop", 12, 8); bot("stop"); sheet("hop", OUT / "hop"); time.sleep(1); home()
if "run" in want:
    shoot("shot", OUT / "raise.png")                      # brings the window to the front before the keys go down
    key(0x2A, True); key(0x11, True); time.sleep(2)
    try: shoot("burst", OUT / "run", 12, 8)
    finally: key(0x11, False); key(0x2A, False)
    sheet("run", OUT / "run"); time.sleep(2); home()
if "stumble" in want:
    bot("goto", "5420", "10114"); time.sleep(2); bot("smokestumble"); shoot("burst", OUT / "stumble", 12, 4); bot("stop"); sheet("stumble", OUT / "stumble"); time.sleep(8); home()
if "dismount" in want:
    shoot("shot", OUT / "raise.png")
    bot("smokeunequipaction"); shoot("burst", OUT / "dismount", 12, 8); sheet("dismount", OUT / "dismount"); time.sleep(3)
    bot("smokeequipaction", "PogoStick"); time.sleep(7)
if "icon" in want:
    bot("smokeui"); time.sleep(1)
    shoot("shot", OUT / "icon.png"); bot("smokeview", "0")
    print("icon picture", OUT / "icon.png")
