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
USER = "Smoke1"   # fresh account: a dead character from an earlier run would otherwise be reused
ITEMS = ["ImpracticalTransport.PogoStick"]
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
            (media / "models_X" / f"{mesh}.fbx").exists() or fail(f"{s.name}: missing models_X/{mesh}.fbx")
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
    _ps(["-File", str(RL / "scripts" / "start-server.ps1"), "-JavaAgent", str(RL / "agent" / "rl-agent.jar"),
         "-ChannelPort", "17600", "-Dev"], stdout=open(log, "wb"), stderr=subprocess.STDOUT)
    deadline = time.time() + 900
    while time.time() < deadline:
        text = log.read_bytes().replace(b"\x00", b"").decode("utf-8", "replace")
        if "*** SERVER STARTED" in text: break
        time.sleep(5)
    else: fail(f"server did not start, see {log}")
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
    ch.command(f"heal|{USER}"); ch.command(f"zclear|{me['x']:.0f}|{me['y']:.0f}|80")
    bot("smokeoutfit")
    for it in ITEMS:
        bot("giveitem", it)   # client-side: a server-side AddItem never reaches a real client
    x, y = int(me["x"]) + 3, int(me["y"])
    ch.command(f"admin|{USER}")      # admin role so the chat command below is accepted
    for v in VEHICLES:
        # /addvehicle is the documented admin command (pzwiki Admin_commands).
        bot("smokechat", f'/addvehicle "{v}" "{USER}"')
        time.sleep(3)
    # speed check: bare hands first, then the pogo stick, same distance in opposite directions
    def pos():
        return next(p for p in ch.wait_obs(timeout=10)["p"] if p["u"] == USER)
    def speed(dx):
        p0 = pos(); bot("goto", f"{p0['x'] + dx:.1f}", f"{p0['y']:.1f}"); t0 = time.time(); time.sleep(8)
        p1 = pos(); return math.hypot(p1["x"] - p0["x"], p1["y"] - p0["y"]) / (time.time() - t0)
    bot("smokeunequip"); time.sleep(2)
    walk = speed(12)
    bot("equip", "PogoStick"); time.sleep(4)
    logs = sorted((RL / ".pzclient" / "Logs").glob("*DebugLog.txt"), key=lambda f: f.stat().st_mtime)
    "ImpracticalTransport riding=true" in logs[-1].read_text(encoding="utf-8", errors="replace") or fail("riding flag never set (see client log)")
    pogo = speed(-12)
    print(f"speed: walking {walk:.2f} tiles/s, pogo {pogo:.2f} tiles/s ({pogo / walk:.0%} of walking)")
    pogo > 0.1 or fail("rider did not move")
    pogo < walk or fail("pogo is not slower than walking")
    print("play ready: god mode on, dressed, pogo stick equipped")
    keep or ch.close()

if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "static"
    "--no-static" in sys.argv or static()   # --no-static: load the game anyway to see what it says about missing assets
    if stage in ("server", "play"): stage_server()
    if stage == "play": stage_play("--keep" in sys.argv)
    print("PASS", stage)
