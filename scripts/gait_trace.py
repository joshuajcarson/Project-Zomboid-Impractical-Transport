"""Position trace while holding W (+ optionally Left Shift = run) in the running game: python scripts/gait_trace.py [walk|run|sprint] [seconds]  (sprint = Left Alt)"""
import ctypes, math, os, pathlib, subprocess, sys, time
HERE = pathlib.Path(__file__).resolve().parent.parent
RL = pathlib.Path(os.environ.get("PZ_RL_REPO", r"C:\bench\project-zomboid-rl-based-players"))
sys.path.insert(0, str(RL))
from pzrl.channel import ServerChannel
u = ctypes.windll.user32
key = lambda scan, down: u.keybd_event({0x38: 0xA4}.get(scan, 0), scan, 8 | (0 if down else 2), 0)    # Left Alt also needs its virtual key (VK_LMENU)
ch = ServerChannel()
pos = lambda: next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == "Smoke1")
gait, secs = (sys.argv[1] if len(sys.argv) > 1 else "walk"), float(sys.argv[2]) if len(sys.argv) > 2 else 8
subprocess.run([sys.executable, str(HERE / "scripts" / "shoot.py"), "shot", str(HERE / "previews" / "trace.png")], check=True)   # raises the window
mods = {"run": [0x2A], "sprint": [0x38], "both": [0x2A, 0x38]}.get(gait, [])
for m in mods: key(m, True)
key(0x11, True); t0 = time.time(); last = pos(); lt = t0; out = []
try:
    while time.time() - t0 < secs:
        time.sleep(0.5); p = pos(); t = time.time()
        if not out and t - t0 > secs / 2: pass
        if len(out) == int(secs) // 1 - 1: subprocess.run([sys.executable, str(HERE / "scripts" / "live.py"), "bot", "smokestate"], capture_output=True)   # log the state while the keys are still down
        out.append(round(math.hypot(p["x"] - last["x"], p["y"] - last["y"]) / (t - lt), 2)); last, lt = p, t
finally:
    key(0x11, False)
    for m in mods: key(m, False)
print(gait, "tiles/s per ~0.5 s:", out, "mean", round(sum(out[2:]) / max(1, len(out) - 2), 2))
