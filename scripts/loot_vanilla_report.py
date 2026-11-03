"""Prints, for the loot lists our mod adds to, the vanilla item weights next to ours so rarities can be compared (reads the game install, copies nothing).
  python scripts/loot_vanilla_report.py [list ...]"""
import os, pathlib, re, sys
from lupa import LuaRuntime
PZ = pathlib.Path(os.environ.get("PZ_DIR", r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid"))
HERE = pathlib.Path(__file__).resolve().parent.parent
lua = LuaRuntime(unpack_returned_tuples=True)
src = (PZ / "media/lua/server/Items/ProceduralDistributions.lua").read_text(encoding="utf-8", errors="ignore")
lua.execute("ProceduralDistributions = {}; function require() end; local P; P = setmetatable({}, {__index = function() return P end, __call = function() return P end}); setmetatable(_G, {__index = function() return P end})")
lua.execute(src)
lst = lua.eval("ProceduralDistributions.list")
ours = {l: b for l, b in re.findall(r"^    (\w+) = \{(.*)\},?\s*$", (HERE / "Contents/mods/ImpracticalTransport/42/media/lua/server/ImpracticalTransportLoot.lua").read_text(encoding="utf-8"), re.M)}
names = sys.argv[1:] or [k for k in ours]
for name in names:
    d = lst[name]
    if d is None: print(name, "missing"); continue
    items = d["items"]; rows = [(items[i], items[i + 1]) for i in range(1, len(items), 2)]
    total = sum(w for _, w in rows)
    top = sorted(rows, key=lambda r: -r[1])[:6]
    print(f"{name}: {len(rows)} entries, total weight {total:.1f}, rolls={d['rolls']}, junk={'yes' if d['junk'] else 'no'}")
    print("   top:", ", ".join(f"{n.split('.')[-1]} {w:g}" for n, w in top))
    print("   ours:", (ours[name] or "").strip())
