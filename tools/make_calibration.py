"""Writes the throw-away calibration set: a few copies of the pogo stick whose attachment `rotate` differs, so a human can equip each in one game
session and say which way each one leans / which way its handlebar runs. Delete the generated files once the final rotate is known.
  python tools/make_calibration.py          writes ImpracticalTransport_calibration_{models,items}.txt next to the real scripts
  python tools/make_calibration.py --remove deletes it"""
import math, pathlib, sys

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "Contents/mods/ImpracticalTransport/42/media/scripts"
OUT_MODELS, OUT_ITEMS = SCRIPTS / "ImpracticalTransport_calibration_models.txt", SCRIPTS / "ImpracticalTransport_calibration_items.txt"
# Round 1 (rotate x y z): z turned the stick sideways and y spun it about its own axis, so the lateral axis is x and a lean is a change of rotate x
# away from 90. Round 2 tests which sign of that change leans the stick toward the front: rotate x = 90 + tilt, grip kept in the hand.
TILTS = [0, -12, 12, -24, 24]
def offset(rx, grip=-0.105, height=0.69):
    # model point (grip, height, 0) after a turn of rx about x lands at (grip, height cos, height sin): cancel it so the hand holds the grip
    c, s = math.cos(math.radians(rx)), math.sin(math.radians(rx))
    return (-grip, -height * c, -height * s)
VARIANTS = [(90 + tilt, 0, 0) for tilt in TILTS]

if "--remove" in sys.argv:
    OUT_MODELS.unlink(missing_ok=True); OUT_ITEMS.unlink(missing_ok=True)
    sys.exit()

models, items = [], []
for i, (x, y, z) in enumerate(VARIANTS, 1):
    models.append(f"""    model PogoCal{i}_3d
    {{
        mesh = ImpracticalTransport/PogoStick,
        texture = ImpracticalTransport/PogoStick_texture,
        scale = 1,
        attachment Bip01_Prop1
        {{
            rotate = {x:.4f} {y:.4f} {z:.4f},
            offset = {offset(x)[0]:.4f} {offset(x)[1]:.4f} {offset(x)[2]:.4f},
        }}
    }}
""")
    items.append(f"""    item PogoCal{i}
    {{
        DisplayName = Pogo Cal {i} (rotate {x} {y} {z}),
        ItemType = base:weapon,
        Weight = 2.5,
        Icon = PogoStick,
        WeaponSprite = PogoCal{i}_3d,
        WorldStaticModel = PogoCal{i}_3d,
        TwoHandWeapon = TRUE,
        RequiresEquippedBothHands = TRUE,
        MaxRange = 0.5,
        MinDamage = 0.1,
        MaxDamage = 0.2,
        Tags = ImpracticalTransport;
    }}
""")
# models live in module Base (as the real model script does), items in the mod's module
OUT_MODELS.write_text("module Base\n{\n" + "\n".join(models) + "}\n", encoding="utf-8")
OUT_ITEMS.write_text("module ImpracticalTransport\n{\n    imports { Base }\n\n" + "\n".join(items) + "}\n", encoding="utf-8")
print("wrote", OUT_MODELS, OUT_ITEMS)
