"""Which floor sprite families the mod's ground classes (SURFACES in ImpracticalTransport.lua) cover, derived from the game's tile definitions (read only).
Writes scripts/terrain_classes.json with OUR derived data only (family prefixes, FloorMaterial names, counts), no tile definitions are copied.
  python scripts/terrain_classes.py [path to media/newtiledefinitions.tiles.txt]
The match mirrors groundAt: label = FloorMaterial + " " + sprite name, lower case; the first SURFACES pattern found at a word start wins."""
import collections, json, pathlib, re, sys
HERE = pathlib.Path(__file__).resolve().parent.parent
LUA = HERE / "Contents/mods/ImpracticalTransport/42/media/lua/client/ImpracticalTransport.lua"
TILES = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media\newtiledefinitions.tiles.txt")
# families a rider can stand on (the ground under the feet, not walls, roofs or furniture): anything with "floor" in its name plus the outdoor ground sets
FLOOR_FAMILY = re.compile(r"floor|^blends_natural|^blends_street_|^e_exterior_snow|^e_newgrassbase_snow|^industry_railroad")

surfaces = [(m.group(1), float(m.group(2)), float(m.group(3)), "paved" in m.group(0))
            for m in re.finditer(r'\{ "([^"]+)",\s*speed = ([\d.]+), stumble = ([\d.]+)[^}]*\}', LUA.read_text(encoding="utf-8"))]
assert surfaces, "no SURFACES found in the Lua"

def classify(label):
    for pat, speed, stumble, paved in surfaces:
        if re.search(r"(?<![a-z])" + re.escape(pat), label): return pat
    return None

families = collections.defaultdict(lambda: {"tiles": 0, "materials": collections.Counter(), "classes": collections.Counter()})
name = props = None
for line in TILES.read_text(encoding="utf-8", errors="replace").splitlines():
    s = line.strip()
    m = re.match(r"// (\S+)$", s)
    if m and props is None: name = m.group(1)
    elif s == "tile": props = {}
    elif props is not None and s == "}":
        family = re.sub(r"_\d+$", "", name)
        if FLOOR_FAMILY.search(family) and ("solidfloor" in props or "FloorMaterial" in props):
            f = families[family]; material = props.get("FloorMaterial", "")
            f["tiles"] += 1; f["materials"][material or "-"] += 1; f["classes"][classify((material + " " + name).lower()) or "unclassified"] += 1
        props = None
    elif props is not None and "=" in s:
        k, v = [x.strip() for x in s.split("=", 1)]; props[k] = v

out = {"_note": "derived by scripts/terrain_classes.py from the game's tile definitions; sprite families only, regenerate after a game update",
       "classes": {pat: {"speed": speed, "stumble": stumble, "paved": paved, "families": {}} for pat, speed, stumble, paved in surfaces},
       "unclassified": {}}
for family, f in sorted(families.items()):
    for cls, n in f["classes"].items():
        entry = {"tiles": n, "materials": sorted(f["materials"])}
        (out["unclassified"] if cls == "unclassified" else out["classes"][cls]["families"])[family] = entry
(HERE / "scripts" / "terrain_classes.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
for cls, c in out["classes"].items(): print(f"{cls:14} speed {c['speed']:.2f} stumble {c['stumble']:.1f}  families: {', '.join(c['families']) or '(none in the tile definitions)'}")
print("unclassified:", ", ".join(f"{k} ({v['tiles']})" for k, v in out["unclassified"].items()))
