"""Speed of the held transport over three 7 s walks from where the tester stands, with the mod's pace log lines next to it:
  python scripts/ground_speed.py     (tp the tester to the ground to test first, e.g. `python scripts/live.py bot tp 6400 5300`, and use only coordinates a
  `smokescan` showed as loaded: a teleport outside the loaded map leaves the client in a void)"""
import math, pathlib, subprocess, sys, time
sys.path.insert(0, r"C:\bench\project-zomboid-rl-based-players")
from pzrl.channel import ServerChannel
ch = ServerChannel()
pos = lambda: next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == "Smoke1")
live = lambda *a: subprocess.run([sys.executable, "scripts/live.py", "bot", *a], capture_output=True)
for dx, dy in ((10, 0), (0, 10), (-10, 0)):
    p0 = pos(); live("goto", f"{p0['x'] + dx:.1f}", f"{p0['y'] + dy:.1f}"); t0 = time.time(); time.sleep(7)
    p1 = pos(); print("moved %.2f tiles/s" % (math.hypot(p1["x"] - p0["x"], p1["y"] - p0["y"]) / (time.time() - t0)))
    live("stop"); time.sleep(2)
