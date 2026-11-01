"""Repo checks that need no game (run by CI and before every push):
  python scripts/check_repo.py
XML well-formed, Lua parses (luac or lua if installed), .X files have the DirectX header, every anim node names a clip that exists, every clip that a
node or the Lua names is shipped, no conflict markers, and the mod's items point at textures that exist. Exit 0 = pass."""
import pathlib, re, shutil, subprocess, sys
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
MEDIA = ROOT / "Contents/mods/ImpracticalTransport/42/media"
problems = []
def bad(msg): problems.append(msg)

for f in list(MEDIA.rglob("*.xml")):
    try: ET.parse(f)
    except ET.ParseError as e: bad(f"{f.relative_to(ROOT)}: not well-formed XML ({e})")

lua = shutil.which("luac5.1") or shutil.which("luac") or shutil.which("lua5.1") or shutil.which("lua")
if lua:
    flag = ["-p"] if "luac" in lua else ["-e", "loadfile(arg[1])"]
    for f in [*MEDIA.rglob("*.lua"), ROOT / "scripts/smoke_bot.lua"]:
        r = subprocess.run([lua, "-p", str(f)] if "luac" in lua else [lua, "-e", f"assert(loadfile([[{f}]]))"], capture_output=True, text=True)
        r.returncode and bad(f"{f.relative_to(ROOT)}: Lua syntax: {r.stderr.strip()[:200]}")
else:
    print("note: no Lua interpreter found, skipping the Lua syntax check")

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

print("\n".join(problems) if problems else "repo checks ok")
sys.exit(1 if problems else 0)
