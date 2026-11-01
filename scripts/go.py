"""Teleport the tester to a named test place (scripts/test_places.json) through the client bot, wait for the area to load, and scan it:
  python scripts/go.py <place> [scan radius] [--clear-cars]
Use only places listed in the file: a teleport outside the loaded map leaves the client in a void. Output of the scan ("SCAN <ground> n=<squares>") is in the client log."""
import json, os, pathlib, re, subprocess, sys, time
HERE = pathlib.Path(__file__).resolve().parent.parent
RL = pathlib.Path(os.environ.get("PZ_RL_REPO", r"C:\bench\project-zomboid-rl-based-players"))
sys.path.insert(0, str(RL))
from pzrl.channel import ServerChannel
places = json.loads((HERE / "scripts" / "test_places.json").read_text(encoding="utf-8"))
name = sys.argv[1] if len(sys.argv) > 1 else sys.exit("places: " + ", ".join(places))
place = places[name]
radius = next((a for a in sys.argv[2:] if a.isdigit()), "25")
ch = ServerChannel()
def bot(*c):
    try: return ch.command("|".join(("bot", "Smoke1") + c), timeout=15)["msg"]
    except TimeoutError: return "no ack"
bot("tp", str(place["x"]), str(place["y"])); time.sleep(18)
if "--clear-cars" in sys.argv: bot("smokecars", "40|remove"); time.sleep(6)      # remove parked cars within 40 tiles (server side)
bot("smokescan", radius); time.sleep(4)
logs = sorted((RL / ".pzclient" / "Logs").glob("*DebugLog.txt"), key=lambda f: f.stat().st_mtime)
text = logs[-1].read_text(encoding="utf-8", errors="replace")
scan = re.findall(r"SCAN (\S+) n=(\d+)", text)[-8:]
p = next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == "Smoke1")
print(f"{name}: at ({p['x']:.0f},{p['y']:.0f}) wanted ({place['x']},{place['y']}); scan: " + ", ".join(f"{g} {n}" for g, n in scan))
