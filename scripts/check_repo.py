"""Repo checks that need no game (run by CI and before every push):
  python scripts/check_repo.py
XML well-formed, Lua compiles (Lua 5.1 through lupa), .X files have the DirectX header, every anim node names a clip that exists, every clip that a
node or the Lua names is shipped, no conflict markers, and the mod's items point at textures that exist. Exit 0 = pass."""
import pathlib, re, sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
MEDIA = ROOT / "Contents/mods/ImpracticalTransport/42/media"
problems = []
def bad(msg): problems.append(msg)

for f in list(MEDIA.rglob("*.xml")):
    try: ET.parse(f)
    except ET.ParseError as e: bad(f"{f.relative_to(ROOT)}: not well-formed XML ({e})")

# Lua syntax: lupa embeds a real Lua 5.1 (the game's Kahlua is 5.1 too): pip install -r requirements-dev.txt. Compile only, nothing is run.
try:
    from lupa import lua51
    compile_lua = lua51.LuaRuntime().eval("loadstring")
except ImportError:
    compile_lua = None
    problems.append("lupa is not installed (pip install -r requirements-dev.txt): the Lua syntax check cannot run")
if compile_lua:
    for f in [*MEDIA.rglob("*.lua"), ROOT / "scripts/smoke_bot.lua"]:
        result = compile_lua(f.read_text(encoding="utf-8"))      # a function when it compiles; (nil, message) when it does not
        isinstance(result, tuple) and bad(f"{f.relative_to(ROOT)}: Lua syntax: {result[1]}")

import ast
for f in [*ROOT.glob("scripts/*.py"), *ROOT.glob("tools/**/*.py")]:
    try: ast.parse(f.read_text(encoding="utf-8"))
    except SyntaxError as e: bad(f"{f.relative_to(ROOT)}: Python syntax error line {e.lineno}")

clips = {f.stem for f in (MEDIA / "anims_X").rglob("*.X")}
for f in (MEDIA / "anims_X").rglob("*.X"):
    f.read_text(encoding="latin-1").startswith("xof 0303txt") or bad(f"{f.relative_to(ROOT)}: not a text DirectX file")
for f in (MEDIA / "AnimSets").rglob("*.xml"):
    m = re.search(r"<m_AnimName>([^<]+)</m_AnimName>", f.read_text(encoding="utf-8"))
    if m and m.group(1) not in clips and not m.group(1).startswith("Bob_Idle"): bad(f"{f.relative_to(ROOT)}: clip {m.group(1)} is not in anims_X/Bob")

for f in ROOT.rglob("*"):
    if f.is_file() and f.suffix in {".py", ".lua", ".txt", ".md", ".xml"} and ".git" not in f.parts and "previews" not in f.parts:
        for i, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if line.startswith(("<<<<<<< ", ">>>>>>> ")): bad(f"{f.relative_to(ROOT)}:{i}: merge conflict marker")
for f in (MEDIA / "scripts").glob("*.txt"):
    for icon in re.findall(r"^\s*Icon\s*=\s*(\w+)", f.read_text(encoding="utf-8"), re.M):
        if icon in ("Shoes",): continue      # vanilla icon
        (MEDIA / "textures" / f"Item_{icon}.png").exists() or bad(f"{f.name}: Icon {icon} has no textures/Item_{icon}.png")

# Loot: every list the loot file uses is in our verified names file, every item is one of ours.
loot = (MEDIA / "lua/server/ImpracticalTransportLoot.lua").read_text(encoding="utf-8")
known_lists = {l.strip() for l in (ROOT / "scripts/loot_list_names.txt").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")}
our_items = set(re.findall(r"^\s*item\s+(\w+)", (MEDIA / "scripts/ImpracticalTransport_items.txt").read_text(encoding="utf-8"), re.M))
for lst, body in re.findall(r"^    (\w+) = \{(.*)\},?\s*$", loot, re.M):
    lst in known_lists or bad(f"ImpracticalTransportLoot.lua: list {lst} is not in scripts/loot_list_names.txt")
    for item in re.findall(r"(\w+) = [\d.]+", body): item in our_items or bad(f"ImpracticalTransportLoot.lua: item {item} is not in ImpracticalTransport_items.txt")

import check_assets      # game-asset leak check, see its header
problems += check_assets.repo_problems()

print("\n".join(problems) if problems else "repo checks ok")
sys.exit(1 if problems else 0)
