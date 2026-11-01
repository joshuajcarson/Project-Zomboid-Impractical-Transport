"""Writes throw-away calibration items for the tricycle's hand attachment: the same model with different (rotate, offset), to be equipped one after
another and photographed (scripts/calibrate_shots.py TrikeCal1 ...). The model's right grip (Blender x = +0.24, y = 0.30, z = 0.70 m; the .X mesh is
x, y = up, z = forward in game units) has to land on the right hand (bone Bip01_Prop1, hand frame X right, Y forward, Z up).
  python tools/make_trike_calibration.py          writes the files
  python tools/make_trike_calibration.py --remove deletes them"""
import pathlib, sys
SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "Contents/mods/ImpracticalTransport/42/media/scripts"
OUT_MODELS, OUT_ITEMS = SCRIPTS / "ImpracticalTransport_trike_cal_models.txt", SCRIPTS / "ImpracticalTransport_trike_cal_items.txt"
S = 0.75
GRIP = (0.24 * S, 0.70 * S, 0.30 * S)       # right grip in the .X frame (x right, y up, z forward), game units

def rot(rx, ry):
    """Apply Ry then Rx (the game applies z first, then y, then x) to a point; degrees."""
    import math
    def f(p):
        x, y, z = p
        c, s = math.cos(math.radians(ry)), math.sin(math.radians(ry)); x, z = x * c + z * s, -x * s + z * c
        c, s = math.cos(math.radians(rx)), math.sin(math.radians(rx)); y, z = y * c - z * s, y * s + z * c
        return x, y, z
    return f

# (rotate x, rotate y, which grip x sign is held): the hand holds the grip at model x = sign * 0.18
VARIANTS = [(90, 180, -1), (90, 180, 1), (90, 0, 1), (90, 0, -1)]

if "--remove" in sys.argv:
    OUT_MODELS.unlink(missing_ok=True); OUT_ITEMS.unlink(missing_ok=True); sys.exit()
models, items = [], []
for i, (rx, ry, sign) in enumerate(VARIANTS, 1):
    p = (sign * GRIP[0], GRIP[1], GRIP[2]); r = rot(rx, ry)(p); off = (-r[0], -r[1], -r[2])
    models.append(f"""    model TrikeCal{i}_3d
    {{
        mesh = ImpracticalTransport/Tricycle,
        texture = ImpracticalTransport/Tricycle_texture,
        scale = 1,
        attachment Bip01_Prop1
        {{
            rotate = {rx:.4f} {ry:.4f} 0.0000,
            offset = {off[0]:.4f} {off[1]:.4f} {off[2]:.4f},
        }}
    }}
""")
    items.append(f"""    item TrikeCal{i}
    {{
        DisplayName = Trike Cal {i} (rotate {rx} {ry} 0 grip {sign:+d}),
        ItemType = base:weapon,
        Weight = 2.5,
        Icon = Tricycle,
        WeaponSprite = TrikeCal{i}_3d,
        WorldStaticModel = TrikeCal{i}_3d,
        TwoHandWeapon = TRUE,
        RequiresEquippedBothHands = TRUE,
        MaxRange = 0.5,
        MinDamage = 0.1,
        MaxDamage = 0.2,
        Tags = ImpracticalTransport;
    }}
""")
OUT_MODELS.write_text("module Base\n{\n" + "\n".join(models) + "}\n", encoding="utf-8")
OUT_ITEMS.write_text("module ImpracticalTransport\n{\n    imports { Base }\n\n" + "\n".join(items) + "}\n", encoding="utf-8")
print("wrote", OUT_MODELS.name, OUT_ITEMS.name)
