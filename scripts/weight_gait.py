"""Plain walking, running and sprinting (REAL keys, no transport) at growing carried weight: does the game itself slow or block them? Needs a game left open by `smoke_test.py play --keep`
(Smoke1 at the arena, nothing equipped); the window is raised and the keyboard must be left alone. Adds Base.Sledgehammer one at a time, removes them at the end.
  python scripts/weight_gait.py [max sledgehammers, default 6]     prints weight, then tiles/s and the sprint/run flags for walk, run, sprint"""
import ctypes, math, os, pathlib, re, subprocess, sys, time
HERE = pathlib.Path(__file__).resolve().parent.parent
RL = pathlib.Path(os.environ.get("PZ_RL_REPO", r"C:\bench\project-zomboid-rl-based-players"))
USER = "Smoke1"; ARENA = (5385, 10114)
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
def log(): return sorted((RL / ".pzclient" / "Logs").glob("*DebugLog.txt"), key=lambda f: f.stat().st_mtime)[-1].read_text(encoding="utf-8", errors="replace")
def shoot(): subprocess.run([sys.executable, str(HERE / "scripts" / "shoot.py"), "shot", str(HERE / "previews" / "wg.png")], check=True)
top = int(sys.argv[1]) if len(sys.argv) > 1 else 6
bot("smokegait", "walk"); bot("smokecalm", "1"); bot("smokehold", "1")
print(f"{'sledges':>7} {'weight':>6}  {'gait':6} {'tiles/s':>7}  engine flags (running sprinting)")
for n in range(top + 1):
    if n: bot("smokechat", f'/additem "{USER}" Base.Sledgehammer'); time.sleep(3)
    bot("smokecheck"); time.sleep(1.5)
    w = re.findall(r"weight=([\d.]+)/([\d.]+)", log())[-1]
    for gait, mods in (("walk", []), ("run", [LSHIFT]), ("sprint", [LALT])):
        bot("tp", str(ARENA[0]), str(ARENA[1])); time.sleep(4)
        shoot()
        try:
            for m in mods: key(m, True)
            key(W, True); time.sleep(2.5)
            a = pos(); t0 = time.time(); time.sleep(3); b = pos(); v = math.hypot(b["x"] - a["x"], b["y"] - a["y"]) / (time.time() - t0)
            bot("smokestate")
        finally:
            key(W, False)
            for m in mods: key(m, False)
        time.sleep(1.5)
        fl = re.findall(r"STATE running=(\w+) sprinting=(\w+)", log())[-1]
        print(f"{n:>7} {w[0]:>6}  {gait:6} {v:7.2f}  {fl[0]} {fl[1]}", flush=True)
bot("smokeclear", "Sledgehammer"); bot("smokechat", "/removeitem Base.Sledgehammer 0"); bot("smokehold"); bot("smokecalm", "0")
