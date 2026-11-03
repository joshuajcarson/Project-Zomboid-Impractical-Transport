"""Speed of each transport on every ground class, against what the mod expects. Needs a game left open by `smoke_test.py play --keep` (the tester at the arena,
dressed, god mode); it forces the ground with the bot's `smokeground` (calm switch only, so no real map tiles are needed) and walks the same distance on each.
  python scripts/ground_speed.py [Pogo,Tricycle,Unicycle]     items to test (default: all three held ones); prints a table, exit 1 when a reading is >30% off
The mod prints "pace ... ground=<factor> expected=<tiles/s>" once a second while moving; the measured speed is compared with the last such line of each walk."""
import math, os, pathlib, re, subprocess, sys, time
HERE = pathlib.Path(__file__).resolve().parent.parent
RL = pathlib.Path(os.environ.get("PZ_RL_REPO", r"C:\bench\project-zomboid-rl-based-players"))
sys.path.insert(0, str(RL))
from pzrl.channel import ServerChannel
USER = "Smoke1"
CLASSES = ["neutral", "water", "mud", "sand", "snow", "gravel", "dirt", "grass", "road_"]      # one label per SURFACES class (the paved ones share numbers), see scripts/terrain_classes.json
items = (sys.argv[1] if len(sys.argv) > 1 else "PogoStick,Tricycle,Unicycle").split(",")
ch = ServerChannel()
def bot(*c):
    try: return ch.command("|".join(("bot", USER) + c), timeout=15)["msg"]
    except TimeoutError: return "no ack"
pos = lambda: next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == USER)
def log(): return sorted((RL / ".pzclient" / "Logs").glob("*DebugLog.txt"), key=lambda f: f.stat().st_mtime)[-1].read_text(encoding="utf-8", errors="replace")
def cruise(dx):
    """speed over the middle of a walk (1.5 s run-in, 3.5 s measured), as smoke_test.py does"""
    p0 = pos(); bot("goto", f"{p0['x'] + dx:.1f}", f"{p0['y']:.1f}"); time.sleep(1.5)
    a = pos(); t0 = time.time(); time.sleep(3.5); b = pos(); v = math.hypot(b["x"] - a["x"], b["y"] - a["y"]) / (time.time() - t0)
    bot("stop"); time.sleep(2); return v
bad = 0
bot("smokecalm", "1"); bot("smokehold", "1")      # no random falls, endurance full: the readings are the ground's alone
print(f"{'item':10} {'ground':8} {'factor':>6} {'tier':>4} {'measured':>8} {'expected':>8}  verdict")
for item in items:
    bot("smokeunequipaction"); time.sleep(4)
    bot("smokechat", f'/additem "{USER}" ImpracticalTransport.{item}'); time.sleep(4)
    bot("smokeequipaction", item); time.sleep(5)
    for cls in CLASSES:
        bot("smokeground", cls)
        v = cruise(12 if CLASSES.index(cls) % 2 == 0 else -12)      # back and forth so the walks stay in the arena
        m = re.findall(r"ImpracticalTransport pace .*ground=([\d.]+) pace=[\d.]+ tier=(\d) expected=(-?\d+(?:\.\d+)?)", log())
        factor, tier, want = (m[-1][0], m[-1][1], float(m[-1][2])) if m else ("?", "?", -1.0)
        ok = want > 0 and abs(v - want) <= 0.3 * want
        bad += not ok
        print(f"{item:10} {cls:8} {factor:>6} {tier:>4} {v:8.2f} {want:8.2f}  {'ok' if ok else 'OFF' if want > 0 else 'no pace line'}")
    bot("smokeground", "off")
    bot("smokeunequipaction"); time.sleep(6); bot("smokechat", f"/removeitem ImpracticalTransport.{item} 0"); time.sleep(2)
bot("smokehold"); bot("smokecalm", "0")
print("PASS" if not bad else f"{bad} readings off")
sys.exit(1 if bad else 0)
