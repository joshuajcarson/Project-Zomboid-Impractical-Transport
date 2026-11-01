"""Smoke test for the mod, reusing the launch/login/channel code from project-zomboid-rl-based-players (PZ_RL_REPO).
  python scripts/smoke_test.py static          files only, no game
  python scripts/smoke_test.py server          + boot a dev server with the mod, scan its log for errors
  python scripts/smoke_test.py play [--keep]   + (any stage takes --no-static) rendered client logs in, gets the items, vehicle spawned next to it; leaves the game open for you
Stages run in order and stop at the first failure. Exit 0 = pass. Stop everything afterwards: python <RL repo>/scripts/cleanup.py"""
import math, os, pathlib, re, shutil, subprocess, sys, time

HERE = pathlib.Path(__file__).resolve().parent.parent
MOD = HERE / "Contents" / "mods" / "ImpracticalTransport"
MOD_ID = "ImpracticalTransport"
RL = pathlib.Path(os.environ.get("PZ_RL_REPO", r"C:\bench\project-zomboid-rl-based-players"))
ARENA = (5385, 10114)   # the RL harness's bare dirt field (5377,10114; its west corner has traffic cones, so start 8 tiles east); the old arena at 10770,9410 sits beside a house, shed and playground, and 4010,11767 is a crop field that hides the rider; the character otherwise resumes wherever it was left
USER = "Smoke1"   # fresh account: a dead character from an earlier run would otherwise be reused
ITEMS = ["ImpracticalTransport.PogoStick", "ImpracticalTransport.Tricycle", "ImpracticalTransport.Unicycle"]
# throw-away rotate calibration set, only present while tools/make_calibration.py has generated it
CAL = MOD / "42/media/scripts/ImpracticalTransport_calibration_items.txt"
ITEMS += [f"ImpracticalTransport.{n}" for n in re.findall(r"item (PogoCal\d+)", CAL.read_text(encoding="utf-8") if CAL.exists() else "")]
TRIKE_CAL = MOD / "42/media/scripts/ImpracticalTransport_trike_cal_items.txt"      # throw-away, see tools/make_trike_calibration.py
ITEMS += [f"ImpracticalTransport.{n}" for n in re.findall(r"item (TrikeCal\d+)", TRIKE_CAL.read_text(encoding="utf-8") if TRIKE_CAL.exists() else "")]
VEHICLES = []   # the tricycle vehicle script is parked while the transports move to held items
ERR = re.compile(r"ERROR|Exception|WARN.*(script|model|texture)", re.I)

def fail(msg): print("FAIL", msg); sys.exit(1)

def static():
    ver = MOD / "42"
    for f in (ver / "mod.info", MOD / "common" / "mod.info"):
        f.exists() or fail(f"missing {f}")
    media = ver / "media"
    for s in (media / "scripts").rglob("*.txt"):
        text = s.read_text(encoding="utf-8")
        for mesh in re.findall(rf"mesh\s*=\s*(\S*{MOD_ID}\S*?),", text):   # vanilla assets live in the game, only check ours
            any((media / "models_X" / f"{mesh}{ext}").exists() for ext in (".X", ".x", ".fbx")) or fail(f"{s.name}: missing models_X/{mesh}")
        for tex in re.findall(rf"texture\s*=\s*(\S*{MOD_ID}\S*?)\s*,", text):
            (media / "textures" / f"{tex}.png").exists() or fail(f"{s.name}: missing textures/{tex}.png")
    print("static ok")

def stage_server():
    rc = subprocess.run([sys.executable, str(RL / "scripts" / "track_game_version.py")], cwd=RL).returncode
    rc and print("WARN game classes the RL harness depends on changed (see its docs/version-notes.md); results may be unreliable")
    for dst in (RL / ".pzdata" / "mods", RL / ".pzclient" / "mods"):
        dst.mkdir(parents=True, exist_ok=True)
        shutil.rmtree(dst / MOD_ID, ignore_errors=True); shutil.copytree(MOD, dst / MOD_ID)
    sys.path.insert(0, str(RL))
    from pzrl.launcher import kill_stale, _ps, LOGS
    kill_stale()
    subprocess.run(["powershell", "-NoProfile", "-File", str(RL / "scripts" / "install-mods.ps1"), "-Enable", "RLBridge"], check=True)
    # install-mods.ps1 gets one string from -File, so it cannot take two mods: write the list (';'-separated) ourselves.
    ini = RL / ".pzdata" / "Server" / "rl.ini"
    ini.write_text(re.sub(r"(?m)^Mods=.*$", f"Mods=RLBridge;{MOD_ID}", ini.read_text(encoding="utf-8")), encoding="utf-8")
    LOGS.mkdir(exist_ok=True)
    log = LOGS / f"smoke-server-{time.strftime('%Y%m%d-%H%M%S')}.log"
    sandbox = RL / ".pzdata" / "Server" / "rl_SandboxVars.lua"      # DayLength 27 = real time, so noon stays noon for the whole run
    original = sandbox.read_text(encoding="utf-8")
    sandbox.write_text(re.sub(r"(?m)^(\s*DayLength = )\d+", r"\g<1>27", original), encoding="utf-8")
    _ps(["-File", str(RL / "scripts" / "start-server.ps1"), "-JavaAgent", str(RL / "agent" / "rl-agent.jar"),
         "-ChannelPort", "17600", "-Dev"], stdout=open(log, "wb"), stderr=subprocess.STDOUT)
    deadline = time.time() + 900
    while time.time() < deadline:      # the RL repo's own runs want their usual day length back as soon as the server has read the file
        text = log.read_bytes().replace(b"\x00", b"").decode("utf-8", "replace")
        if "*** SERVER STARTED" in text: break
        time.sleep(5)
    else: sandbox.write_text(original, encoding="utf-8"); fail(f"server did not start, see {log}")
    sandbox.write_text(original, encoding="utf-8")
    bad = [l for l in text.splitlines() if MOD_ID.lower() in l.lower() and ERR.search(l)] or \
          [l for l in text.splitlines() if re.search(r"Tricycle|PogoStick", l) and ERR.search(l)]
    re.search(r"required mod .* not found", text) and fail(f"server could not find a mod in its list, see {log}")
    re.search(rf"loading {MOD_ID}", text) or fail(f"server never loaded {MOD_ID}, see {log}")
    bad and fail("mod errors in server log:\n" + "\n".join(bad[:10]))
    print("server ok, log", log)

def stage_play(keep):
    from pzrl.channel import ServerChannel
    from pzrl.launcher import _ps, LOGS
    env = dict(os.environ, RL_AGENT_JAR=str(RL / "agent" / "rl-agent-client.jar"))
    _ps(["-File", str(RL / "scripts" / "start-client.ps1"), "-Small", "-User", USER, "-Pass", USER, "-Hash", "0"],
        stdout=open(LOGS / f"smoke-client-{time.strftime('%Y%m%d-%H%M%S')}.log", "wb"), stderr=subprocess.STDOUT, env=env)
    ch = ServerChannel()
    deadline = time.time() + 600
    while time.time() < deadline:
        try:
            me = next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == USER); break
        except (StopIteration, TimeoutError): continue
    else: fail("client never appeared in the world")
    print("player at", me["x"], me["y"])
    time.sleep(25)   # let the world settle before touching the character
    def bot(*c):
        try: a = ch.command("|".join(("bot", USER) + c), timeout=15)
        except TimeoutError: print(" ".join(c), "-> no ack (double quotes in a command defeat the ack match; the command still runs)"); return None
        print(" ".join(c), "->", a["msg"]); return a
    lua = RL / ".pzclient" / "Lua" / "rl_bot_dev.lua"      # append after login: start-client.ps1 overwrites this file when it starts
    lua.write_text(lua.read_text(encoding="utf-8") + "\n" + (HERE / "scripts" / "smoke_bot.lua").read_text(encoding="utf-8"), encoding="utf-8")
    bot("reload"); time.sleep(3)
    bot("god", "1")      # keep the tester alive; a dead character costs minutes to replace
    bot("tp", str(ARENA[0]), str(ARENA[1])); time.sleep(10)      # start every run in the open, not at a fence
    me = next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == USER)
    ch.command(f"heal|{USER}"); ch.command(f"zclear|{me['x']:.0f}|{me['y']:.0f}|80")
    bot("smokeoutfit")
    ch.command(f"admin|{USER}")      # admin role so the chat commands below are accepted
    for it in ITEMS:
        # the account persists between runs: clear old copies first. Never empty the hands directly on the client: the server keeps its own
        # hand slot, and a client-only change leaves the two disagreeing, after which no equip action works.
        bot("smokeunequipaction"); time.sleep(4)
        bot("smokechat", f"/removeitem {it} 0"); time.sleep(2)
        bot("smokeclear", it.split(".")[-1])         # client-only leftovers from older runs
        time.sleep(1)
        # /additem (pzwiki Admin_commands) adds the item on the SERVER and syncs it to the client. The bot's client-side giveitem
        # would leave the server without the item, so every real unequip/drop/place action would fail server-side.
        bot("smokechat", f'/additem "{USER}" {it}')
    time.sleep(3)
    x, y = int(me["x"]) + 3, int(me["y"])
    for v in VEHICLES:
        # /addvehicle is the documented admin command (pzwiki Admin_commands).
        bot("smokechat", f'/addvehicle "{v}" "{USER}"')
        time.sleep(3)
    # speed check: bare hands first, then the pogo stick, same distance in opposite directions
    def pos():
        return next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == USER)
    def speed(dx):
        p0 = pos(); bot("goto", f"{p0['x'] + dx:.1f}", f"{p0['y']:.1f}"); t0 = time.time(); time.sleep(8)
        p1 = pos(); v = math.hypot(p1["x"] - p0["x"], p1["y"] - p0["y"]) / (time.time() - t0)
        bot("stop"); time.sleep(1)      # a walk still in progress sits ahead of any later equip/unequip action in the timed-action queue
        return v
    for it in ITEMS[1:]:      # every extra item is weight that slows the pogo measurements (ITEMS[0] is the one under test); they only had to load and add
        bot("smokeunequipaction"); time.sleep(4); bot("smokechat", f"/removeitem {it} 0"); time.sleep(2)
    # fixed conditions: needs met, noon, no corpses, clear sky, carrying only what is expected; fails when any of it is off
    ch.command(f"heal|{USER}"); ch.command("settime|12"); ch.command(f"corpses|{me['x']:.0f}|{me['y']:.0f}|25|1")
    bot("smokechat", "/stopweather"); time.sleep(3)      # the tester is an admin by now; weather is the server's, a client override is not enough
    bot("smokereset"); time.sleep(5); bot("smokecheck"); time.sleep(3)
    checks = re.findall(r"SMOKECHECK (.*)", sorted((RL / ".pzclient" / "Logs").glob("*DebugLog.txt"), key=lambda f: f.stat().st_mtime)[-1].read_text(encoding="utf-8", errors="replace"))
    print("conditions:", checks[-1] if checks else "no SMOKECHECK line")
    checks or fail("smokecheck never reported (see client log)")
    "PROBLEMS" in checks[-1] and fail("test conditions are not ideal: " + checks[-1])
    def expected_speed(name, measured):
        """The mod logs the speed it expects once a second ("pace ... expected=x"); the measured one has to be within 30% of the latest."""
        lines = re.findall(r"ImpracticalTransport pace .*expected=(-?\d+\.\d+)", sorted((RL / ".pzclient" / "Logs").glob("*DebugLog.txt"), key=lambda f: f.stat().st_mtime)[-1].read_text(encoding="utf-8", errors="replace"))
        lines or fail(f"{name}: no pace line in the client log")
        want = float(lines[-1]); print(f"{name}: measured {measured:.2f} tiles/s, mod expected {want:.2f}")
        want > 0 and abs(measured - want) > 0.3 * want and fail(f"{name} moves at {measured:.2f} tiles/s but the mod expects {want:.2f}")
    bot("smokecalm", "1")      # random slips and falls would spoil the speed readings
    bot("smokeunequipaction"); time.sleep(4)
    walk = speed(12)
    bot("smokenode", "900")      # logs which anim nodes play, to see that the mount clip is chosen
    bot("smokeequipaction", "PogoStick"); time.sleep(5)
    logs = sorted((RL / ".pzclient" / "Logs").glob("*DebugLog.txt"), key=lambda f: f.stat().st_mtime)
    "ImpracticalTransport riding=true" in logs[-1].read_text(encoding="utf-8", errors="replace") or fail("riding flag never set (see client log)")
    "mount_pogo/Bob_PogoMount" in logs[-1].read_text(encoding="utf-8", errors="replace") or fail("the mount anim node never played (see NODE lines in the client log)")
    pogo = speed(-12)
    expected_speed("pogo", pogo)
    bot("smokecalm", "0"); bot("smokestumble"); time.sleep(8)      # the fall animation has to finish before the unequip below is queued
    "ImpracticalTransport stumble" in logs[-1].read_text(encoding="utf-8", errors="replace") or fail("forced stumble never ran (see client log)")
    log = logs[-1].read_text(encoding="utf-8", errors="replace")
    errors = [l for l in log.splitlines() if "(MOD:Impractical Transport)" in l and "ERROR" in l] + re.findall(r"ImpracticalTransport \w+ disabled: .*", log)
    errors and fail(f"{len(errors)} mod Lua errors in the client log, first: {errors[0][:200]}")
    print("terrain readings:", sorted(set(re.findall(r"ImpracticalTransport terrain (.*)", log))))
    print(f"speed: walking {walk:.2f} tiles/s, pogo {pogo:.2f} tiles/s ({pogo / walk:.0%} of walking)")
    pogo > 0.1 or fail("rider did not move")
    # put it away like a player: a real unequip action must finish while the pogo anim nodes are active
    bot("smokeunequipaction"); time.sleep(6); bot("smokehands"); time.sleep(1)
    "RLBOT smokehands -> true true hands empty" in logs[-1].read_text(encoding="utf-8", errors="replace") or fail("unequip action never finished: hands still full")
    walk2 = speed(12)   # one walk is noisy (path, terrain, loading chunks): compare against the faster of two bare-hand walks
    base = max(walk, walk2)
    print(f"bare-hand walks {walk:.2f} and {walk2:.2f}, pogo {pogo:.2f} tiles/s ({pogo / base:.0%} of the faster walk)")
    pogo < base * 0.97 or fail("pogo is not slower than walking")   # walks on this field vary 0.9 to 1.5 tiles/s with the pathing; the pogo is steady at ~0.85
    # the other transports, one item at a time in the pack so the weight stays comparable
    carried = "ImpracticalTransport.PogoStick"
    for item, slip_node in (("Tricycle", "slip_trike/Bob_TrikeSlip"), ("Unicycle", "slip_uni/Bob_UniSlip")):
        full, label = f"ImpracticalTransport.{item}", item.lower()
        bot("smokechat", f"/removeitem {carried} 0"); time.sleep(2)
        bot("smokechat", f'/additem "{USER}" {full}'); time.sleep(4)
        bot("smokeequipaction", item); time.sleep(5)
        bot("smokecalm", "1"); item_speed = speed(12)
        expected_speed(label, item_speed)
        print(f"{label} {item_speed:.2f} tiles/s ({item_speed / base:.0%} of the faster walk)")
        item_speed > 0.1 or fail(f"{label} rider did not move")
        item_speed < base * 0.97 or fail(f"{label} is not slower than walking")
        bot("smokenode", "600"); p0 = pos(); bot("goto", f"{p0['x'] + 12:.1f}", f"{p0['y']:.1f}"); time.sleep(3)
        bot("smokeslip"); time.sleep(4); time.sleep(1); bot("stop"); time.sleep(1)
        log = sorted((RL / ".pzclient" / "Logs").glob("*DebugLog.txt"), key=lambda f: f.stat().st_mtime)[-1].read_text(encoding="utf-8", errors="replace")
        slip_node in log or fail(f"the {label} slip node never played (see NODE lines in the client log)")
        bot("smokeunequipaction"); time.sleep(6)
        carried = full
    bot("smokechat", f"/removeitem {carried} 0"); time.sleep(2)
    bot("smokechat", f'/additem "{USER}" ImpracticalTransport.PogoStick'); time.sleep(4)
    bot("smokeequipaction", "PogoStick")   # leave it in hand for whoever plays next
    print("play ready: god mode on, dressed, pogo stick equipped")
    keep or ch.close()

if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "static"
    "--no-static" in sys.argv or static()   # --no-static: load the game anyway to see what it says about missing assets
    if stage in ("server", "play"): stage_server()    # the server checksums scripts too, so any mod edit needs a full boot
    if stage == "play": stage_play("--keep" in sys.argv)
    print("PASS", stage)
