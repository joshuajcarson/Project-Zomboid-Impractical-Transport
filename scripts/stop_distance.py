"""How far the rider travels after the move order stops (skates should glide on, everything else stops at once):
  python scripts/stop_distance.py [gait]   gait walk (default) or run (the bot's goto sets the engine's running flag but plays the walk clip, see the README)
Walks 12 tiles east, sends `stop`, and reports the distance covered 0.3 s and 2.5 s after the stop was sent."""
import math, subprocess, sys, time
sys.path.insert(0, r"C:\bench\project-zomboid-rl-based-players")
from pzrl.channel import ServerChannel
ch = ServerChannel()
pos = lambda: next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == "Smoke1")
live = lambda *a: subprocess.run([sys.executable, "scripts/live.py", "bot", *a], capture_output=True)
p0 = pos(); live("goto", f"{p0['x'] + 12:.1f}", f"{p0['y']:.1f}"); time.sleep(5)
p1 = pos(); live("stop"); t0 = time.time()
time.sleep(0.3); p2 = pos(); time.sleep(2.2); p3 = pos()
d = lambda a, b: math.hypot(a["x"] - b["x"], a["y"] - b["y"])
print("before stop: moved %.2f tiles in 5 s; after the stop order: %.2f tiles in 0.3 s, %.2f tiles by 2.5 s" % (d(p0, p1), d(p1, p2), d(p1, p3)))
