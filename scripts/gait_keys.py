"""Hop speed per gait with the REAL keys held (the bot cannot press them): W = forward, Left Shift = run, Left Alt = sprint (the game's default
bindings, scancodes in <RL>/.pzclient/Lua/keysB42.ini). Needs a game left open by `smoke_test.py play --keep`; the window is raised to the front.
  python scripts/gait_keys.py        prints tiles/s per gait, writes previews/keys_<gait>.png"""
import ctypes, math, os, pathlib, subprocess, sys, time
HERE = pathlib.Path(__file__).resolve().parent.parent
RL = pathlib.Path(os.environ.get("PZ_RL_REPO", r"C:\bench\project-zomboid-rl-based-players"))
USER = "Smoke1"
sys.path.insert(0, str(RL))
from pzrl.channel import ServerChannel
u = ctypes.windll.user32
W, LSHIFT, LALT = 0x11, 0x2A, 0x38          # scancodes
def key(scan, down): u.keybd_event(0, scan, 8 | (0 if down else 2), 0)    # KEYEVENTF_SCANCODE (8), KEYEVENTF_KEYUP (2)
ch = ServerChannel()
def bot(*c):
    try: return ch.command("|".join(("bot", USER) + c), timeout=15)["msg"]
    except TimeoutError: return "no ack"
def pos(): return next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == USER)
def shoot(name): subprocess.run([sys.executable, str(HERE / "scripts" / "shoot.py"), "shot", str(HERE / "previews" / name)], check=True)
(HERE / "previews").mkdir(exist_ok=True)
bot("smokeview", "6")
for gait, mods in (("walk", []), ("run", [LSHIFT]), ("sprint", [LALT])):
    bot("smokegait", "walk")                      # no forced gait: the keys decide
    shoot(f"keys_{gait}_start.png")               # raises the game window to the front
    try:
        for m in mods: key(m, True)
        key(W, True); time.sleep(2.5)             # let the hop get up to speed
        a = pos(); t0 = time.time(); time.sleep(3)
        shoot(f"keys_{gait}.png")
        b = pos(); speed = math.hypot(b["x"] - a["x"], b["y"] - a["y"]) / (time.time() - t0)
        bot("smokestate")
        print(f"{gait}: {speed:.2f} tiles/s from {a['x']:.0f},{a['y']:.0f} to {b['x']:.0f},{b['y']:.0f}")
    finally:
        key(W, False)
        for m in mods: key(m, False)
    time.sleep(2)
    p = pos(); bot("goto", "5385", "10114"); time.sleep(10); bot("stop"); time.sleep(1)    # back to the start of the field
