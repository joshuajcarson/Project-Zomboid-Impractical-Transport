"""Talks to a game that `python scripts/smoke_test.py play --keep` left running, so Lua probes need no 6-minute server boot.
  python scripts/live.py reload                 re-append scripts/smoke_bot.lua to the client's bot file and reload it
  python scripts/live.py raw <server command>   e.g. settime|12, zclear|x|y|r, heal|Smoke1
  python scripts/live.py bot <command> [args]   send one bot command (e.g. smokebones 90) and print the ack
Output of probes lands in the newest client DebugLog (<RL>/.pzclient/Logs)."""
import os, pathlib, sys, time
HERE = pathlib.Path(__file__).resolve().parent.parent
RL = pathlib.Path(os.environ.get("PZ_RL_REPO", r"C:\bench\project-zomboid-rl-based-players"))
USER = "Smoke1"
sys.path.insert(0, str(RL))
from pzrl.channel import ServerChannel

ch = ServerChannel()
def bot(*c):
    try: print(ch.command("|".join(("bot", USER) + c), timeout=15)["msg"])
    except TimeoutError: print("no ack (the command may still have run)")

cmd = sys.argv[1] if len(sys.argv) > 1 else ""
if cmd == "reload":
    lua = RL / ".pzclient" / "Lua" / "rl_bot_dev.lua"
    text = lua.read_text(encoding="utf-8")
    marker = "-- Appended to the RL harness's client-side rl_bot_dev.lua"
    lua.write_text(text.split(marker)[0] + "\n" + (HERE / "scripts" / "smoke_bot.lua").read_text(encoding="utf-8"), encoding="utf-8")
    bot("reload")
elif cmd == "bot": bot(*sys.argv[2:])
elif cmd == "raw": print(ch.command(sys.argv[2], timeout=15))   # a harness server command, e.g. "settime|12" or "zclear|5377|10114|80"
else: print(__doc__)
