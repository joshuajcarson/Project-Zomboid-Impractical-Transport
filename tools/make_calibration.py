"""Writes the throw-away calibration set: 7 copies of the pogo stick whose attachment `rotate` differs, so a human can equip each in one game
session and say which way each one leans / which way its handlebar runs. Delete the generated files once the final rotate is known.
  python tools/make_calibration.py          writes ImpracticalTransport_calibration_{models,items}.txt next to the real scripts
  python tools/make_calibration.py --remove deletes it"""
import pathlib, sys

SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "Contents/mods/ImpracticalTransport/42/media/scripts"
OUT_MODELS, OUT_ITEMS = SCRIPTS / "ImpracticalTransport_calibration_models.txt", SCRIPTS / "ImpracticalTransport_calibration_items.txt"
VARIANTS = [(90, 0, 0), (90, 0, 90), (90, 0, -90), (90, 25, 0), (90, -25, 0), (90, 0, 25), (90, 0, -25)]

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
            offset = 0.1050 0.0000 -0.6900,
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
