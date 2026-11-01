"""Does the playback-speed variable change how fast the hop animates? Captures 16 frames at 8 fps for each profile walk value and prints the
mean frame-to-frame pixel change of the rider area (bigger = faster animation). Needs a running game with the stick equipped."""
import os, pathlib, subprocess, sys, time
import numpy as np
from PIL import Image
HERE = pathlib.Path(__file__).resolve().parent.parent
def live(*a): subprocess.run([sys.executable, str(HERE / "scripts" / "live.py"), *a], check=True, capture_output=True)
out = HERE / "previews" / "hoprate"
for v in (0.4, 1.0, 2.5):
    live("bot", "smokeprofile", f"walk|{v}"); live("bot", "goto", "5385", "10114"); time.sleep(9); live("bot", "stop"); time.sleep(1)
    live("bot", "goto", "5425", "10114"); time.sleep(2.5)
    d = out / f"walk{v}"; subprocess.run([sys.executable, str(HERE / "scripts" / "shoot.py"), "burst", str(d), "16", "8"], check=True)
    live("bot", "stop")
    fr = [np.asarray(Image.open(f).convert("L").crop((140, 0, 500, 480)), dtype=float) for f in sorted(d.glob("*.png"))]
    print(f"walk={v}: mean frame change {np.mean([np.abs(a - b).mean() for a, b in zip(fr, fr[1:])]):.2f}")
live("bot", "smokeprofile", "walk|1.0")
