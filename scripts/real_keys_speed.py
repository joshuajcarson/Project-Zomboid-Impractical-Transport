"""Speed with the REAL keys (W, Left Shift run, Left Alt sprint) for plain walking and for one worn transport, on the open pavement of the parking lot (needs `smoke_test.py play --keep` running; keep the keyboard free).
  python scripts/real_keys_speed.py [RollerSkates|Stilts]      prints tiles/s for none and the item; Smoke1 ends with the item removed"""
import ctypes, math, os, pathlib, subprocess, sys, time
HERE = pathlib.Path(__file__).resolve().parent.parent
RL = pathlib.Path(os.environ.get("PZ_RL_REPO", r"C:\bench\project-zomboid-rl-based-players"))
USER = "Smoke1"; item = sys.argv[1] if len(sys.argv) > 1 else "RollerSkates"
sys.path.insert(0, str(RL))
from pzrl.channel import ServerChannel
u = ctypes.windll.user32
W, LSHIFT, LALT = 0x11, 0x2A, 0x38
key = lambda scan, down: u.keybd_event(0, scan, 8 | (0 if down else 2), 0)
ch = ServerChannel()
def bot(*c):
    try: return ch.command("|".join(("bot", USER) + c), timeout=15)["msg"]
    except TimeoutError: return "no ack"
pos = lambda: next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == USER)
def shoot(): subprocess.run([sys.executable, str(HERE / "scripts" / "shoot.py"), "shot", str(HERE / "previews" / "rk.png")], check=True)
def measure(label):
    for gait, mods in (("walk", []), ("run", [LSHIFT]), ("sprint", [LALT])):
        bot("tp", "7740", "11755"); time.sleep(4); shoot()
        try:
            for m in mods: key(m, True)
            key(W, True); time.sleep(2.5)
            a = pos(); t0 = time.time(); time.sleep(2.5); b = pos()
            print(f"{label:12} {gait:6} {math.hypot(b['x'] - a['x'], b['y'] - a['y']) / (time.time() - t0):5.2f} tiles/s", flush=True)
        finally:
            key(W, False)
            for m in mods: key(m, False)
bot("smokegait", "walk"); bot("smokecalm", "1"); bot("smokehold", "1")
measure("none")
bot("smokechat", f'/additem "{USER}" ImpracticalTransport.{item}'); time.sleep(3); bot("smokewear", item); time.sleep(6)
measure(item)
bot("smokeunwear", item); time.sleep(5); bot("smokechat", f"/removeitem ImpracticalTransport.{item} 0"); bot("smokehold"); bot("smokecalm", "0")
