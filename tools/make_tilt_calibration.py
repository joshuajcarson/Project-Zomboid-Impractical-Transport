"""Throw-away calibration items for the held models' sideways lean. The held-item bone (Bip01_Prop1) is rolled about 17 degrees about the rider's forward
axis in the riding pose (measured in Blender: its z axis leans 0.29 toward the rider's right), so the nominal rotate 90 180 0 leaves the unicycle leaning.
Each variant rolls the model by theta about the bone's y axis on top of the nominal rotation (R = Ry(theta) Rx(90) Ry(180)) and keeps the handle on the
bone (offset = -R * handle). Equip UniCal1..n one after another and photograph them at the real screen facings (scripts/tilt_shots.py).
  python tools/make_tilt_calibration.py            writes the files
  python tools/make_tilt_calibration.py --remove   deletes them
`retilt` is also used to move the pogo and the tricycle to the winning angle."""
import math, pathlib, sys
SCRIPTS = pathlib.Path(__file__).resolve().parents[1] / "Contents/mods/ImpracticalTransport/42/media/scripts"
OUT_MODELS, OUT_ITEMS = SCRIPTS / "ImpracticalTransport_tilt_cal_models.txt", SCRIPTS / "ImpracticalTransport_tilt_cal_items.txt"
S = 0.75
HANDLE = (0.0, 0.80 * S, 0.14 * S)          # the unicycle's saddle handle in the .X frame (x right, y up, z forward), game units
THETAS = [17, 8, 0, -8, -17, 26]

def rx(a): c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); return [[1, 0, 0], [0, c, -s], [0, s, c]]
def ry(a): c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); return [[c, 0, s], [0, 1, 0], [-s, 0, c]]
def mul(a, b): return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
def app(m, v): return tuple(sum(m[i][k] * v[k] for k in range(3)) for i in range(3))

def euler(R):
    """The attachment's rotate x y z (degrees): R = Rx(x) Ry(y) Rz(z), z applied first."""
    b = math.asin(max(-1, min(1, R[0][2])))
    return math.degrees(math.atan2(-R[1][2], R[2][2])), math.degrees(b), math.degrees(math.atan2(-R[0][1], R[0][0]))

def retilt(R_old, point, theta):
    """New (rotate, offset) after rolling by theta about the bone y axis; `point` is the model point that must stay on the bone origin."""
    R = mul(ry(theta), R_old)
    off = tuple(-v for v in app(R, point))
    return euler(R), off

if "--remove" in sys.argv:
    OUT_MODELS.unlink(missing_ok=True); OUT_ITEMS.unlink(missing_ok=True); sys.exit()
POGO = "pogo" in sys.argv       # python tools/make_tilt_calibration.py pogo: PogoCal1..6, the pogo stick at different pitches (rotate x base) with the roll fixed at 16.8
PITCHES = [54, 66, 78, 90, 102, 114]
if POGO:
    old_off = (0.105, 0.1434, -0.6749)          # the pogo's original fitted offset for rotate 102 0 0: the model point on the bone is -R^T * offset
    point = app([[1, 0, 0], [0, math.cos(math.radians(-102)), -math.sin(math.radians(-102))], [0, math.sin(math.radians(-102)), math.cos(math.radians(-102))]], tuple(-v for v in old_off))
    variants = [(f"PogoCal{i}", "PogoStick", f"pitch {pit}", mul(ry(16.8), rx(pit)), point) for i, pit in enumerate(PITCHES, 1)]
else:
    nominal = mul(rx(90), ry(180))
    variants = [(f"UniCal{i}", "Unicycle", f"roll {th:+d}", mul(ry(th), nominal), HANDLE) for i, th in enumerate(THETAS, 1)]
models, items = [], []
for name, mesh, label, R, point_ in variants:
    ax, ay, az = euler(R); off = tuple(-v for v in app(R, point_)); i = name
    models.append(f"""    model {name}_3d
    {{
        mesh = ImpracticalTransport/{mesh},
        texture = ImpracticalTransport/{mesh}_texture,
        scale = 1,
        attachment Bip01_Prop1
        {{
            rotate = {ax:.4f} {ay:.4f} {az:.4f},
            offset = {off[0]:.4f} {off[1]:.4f} {off[2]:.4f},
        }}
    }}
""")
    items.append(f"""    item {name}
    {{
        DisplayName = {name} ({label}),
        ItemType = base:weapon,
        Weight = 1.0,
        Icon = {mesh},
        WeaponSprite = {name}_3d,
        WorldStaticModel = {name}_3d,
        TwoHandWeapon = TRUE,
        RequiresEquippedBothHands = TRUE,
        MaxRange = 0.5,
        MinDamage = 0.1,
        MaxDamage = 0.2,
        Tags = ImpracticalTransport;
    }}
""")
    print(name, label, "rotate %.2f %.2f %.2f" % (ax, ay, az), "offset %.4f %.4f %.4f" % off)
OUT_MODELS.write_text("module Base\n{\n" + "\n".join(models) + "}\n", encoding="utf-8")
OUT_ITEMS.write_text("module ImpracticalTransport\n{\n    imports { Base }\n\n" + "\n".join(items) + "}\n", encoding="utf-8")
print("wrote", OUT_MODELS.name, OUT_ITEMS.name)
