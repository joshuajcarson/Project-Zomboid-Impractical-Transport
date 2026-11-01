"""Hop speed and a picture for each gait (walk, run, sprint) of the rider in a game left open by `smoke_test.py play --keep`.
  python scripts/gait_probe.py        prints tiles/s per gait, writes previews/gait_<gait>.png"""
import math, os, pathlib, subprocess, sys, time
HERE = pathlib.Path(__file__).resolve().parent.parent
RL = pathlib.Path(os.environ.get("PZ_RL_REPO", r"C:\bench\project-zomboid-rl-based-players"))
USER = "Smoke1"
sys.path.insert(0, str(RL))
from pzrl.channel import ServerChannel
ch = ServerChannel()
def bot(*c):
    try: return ch.command("|".join(("bot", USER) + c), timeout=15)["msg"]
    except TimeoutError: return "no ack"
def pos(): return next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == USER)
(HERE / "previews").mkdir(exist_ok=True)
bot("smokeview", "6")
for gait in ("walk", "run", "sprint"):
    bot("smokegait", gait)
    p0 = pos(); bot("goto", f"{p0['x'] + 18:.1f}", f"{p0['y']:.1f}"); time.sleep(2.5)      # let the hop get up to speed
    a = pos(); t0 = time.time(); time.sleep(4); b = pos()
    speed = math.hypot(b["x"] - a["x"], b["y"] - a["y"]) / (time.time() - t0)
    subprocess.run([sys.executable, str(HERE / "scripts" / "shoot.py"), "shot", str(HERE / "previews" / f"gait_{gait}.png")], check=True)
    print(f"{gait}: {speed:.2f} tiles/s"); bot("stop"); time.sleep(2)
    p1 = pos(); bot("goto", f"{p1['x'] - 20:.1f}", f"{p1['y']:.1f}"); time.sleep(8); bot("stop"); time.sleep(1)   # walk back to keep room
bot("smokegait", "walk")
