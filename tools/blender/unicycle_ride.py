"""Build the seated unicycle ride for the game's survivor: pedalling feet, hands on the grips, and write the clips.
  blender -b -P tools/blender/unicycle_ride.py       writes media/anims_X/Bob/Bob_Uni{Idle,Ride,RideRun}{,T1,T2}.X and previews/unicycle_*.png
The rider sits on the saddle of tools/blender/unicycle.py (the unicycle is at the world origin facing the rider's forward), the feet go round a
circle about the front hub (the model has no pedals: they would not turn with the feet), the hands hold the grips. Travel per pedal turn
is baked into each clip (the engine's speed controls and playback variables do not change the rider's speed; see the README)."""
import bpy, sys, math, os, pathlib
from mathutils import Vector, Matrix
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import zomboid_x as zx
import pogo_stick
import unicycle as tri

GAME = pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media")
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_X = ROOT / "Contents/mods/ImpracticalTransport/42/media/anims_X/Bob/Bob_UniRide.X"
PREVIEW = ROOT / "previews"; PREVIEW.mkdir(exist_ok=True)
FPS = 30
s = pogo_stick.GAME_UNITS_PER_METRE
SWAY = 0.025 * s      # the rider rocks from side to side as the wheel turns
WAVE = 0.06 * s      # the free arm waves for balance
LEAN = math.radians(float(os.environ.get("UNI_LEAN_DEG", 3)))      # torso leans forward over the handlebar

bpy.ops.wm.read_factory_settings(use_empty=True)
arm, meshes, rl0, _ = zx.import_body(GAME / "models_X/Skinned/MaleBody.x")
bpy.context.view_layer.update()
pb = arm.pose.bones
# The stick's hand attachment was measured against the hand in Bob_Idle, so in the hop the hands must keep that orientation or the stick swings away.
zx.import_animation(GAME / "anims_X/Bob/Bob_Idle.X", arm, rl0, "Bob_Idle", fps=FPS)
bpy.context.scene.frame_set(0); bpy.context.view_layer.update()
idle_hand = {n: pb[n].matrix.to_3x3().copy() for n in ("Bip01_L_Hand", "Bip01_R_Hand")}
# Bip01_Prop1 is the bone the model attaches to and Bob_Idle poses it off the hand; keep that offset or the stick tilts away from the grip
prop_rel = {(h, pr): pb[h].matrix.inverted() @ pb[pr].matrix for h, pr in (("Bip01_R_Hand", "Bip01_Prop1"), ("Bip01_L_Hand", "Bip01_Prop2"))}
idle_local = {}
for b in arm.data.bones:     # Bob_Idle frame 0 as bone-local matrices: the standing pose the mount clip starts from and the dismount clip ends on
    par = pb[b.name].parent
    idle_local[b.name] = (par.matrix.inverted() @ pb[b.name].matrix) if par else pb[b.name].matrix.copy()
arm.animation_data_clear()
for p in pb: p.rotation_mode = "QUATERNION"
rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
order = [b.name for b in arm.data.bones]          # parents come before children
Mi = arm.matrix_world.inverted()
wrest = lambda n: arm.matrix_world @ rest[n].translation
up = Vector((0, 0, 1))
fwd = wrest("Bip01_L_Toe0") - wrest("Bip01_L_Foot"); fwd.z = 0; fwd.normalize()
side = up.cross(fwd)
if (wrest("Bip01_L_Hand") - wrest("Bip01_R_Hand")).dot(side) < 0: side = -side     # side = rider's left
dist = lambda a, b: (rest[a].translation - rest[b].translation).length
Larm = dist("Bip01_L_UpperArm", "Bip01_L_Forearm") + dist("Bip01_L_Forearm", "Bip01_L_Hand")
hip_z = wrest("Bip01_L_Thigh").z
sh_off = wrest("Bip01_L_UpperArm").z - hip_z
ankle = wrest("Bip01_L_Foot").z

# --- two-bone solver (armature space), same method as pogo_rider.py
def aim(name, child, new_dir, head):
    """Pose bone `name` so the direction to its child bone becomes new_dir, head at `head` (armature space); returns the swing.
    Bone axes in this skeleton are arbitrary (the limb is not along Y), so the limb direction is read from the bind pose."""
    rm = rest[name].to_3x3()
    along = (rm.inverted() @ (rest[child].translation - rest[name].translation)).normalized()
    q = (rm @ along).rotation_difference(new_dir)
    pb[name].matrix = Matrix.Translation(head) @ (q.to_matrix() @ rm).to_4x4()
    bpy.context.view_layer.update()
    return q

def limb(root, mid, end, target_world, pole_world, foot, Rm=None):
    Rm = Rm if Rm is not None else globals()["Rm"]
    T, pole = Mi @ target_world, Mi.to_3x3() @ pole_world
    Mp, Ep = rest[mid].translation, rest[end].translation
    Hp = pb[root].matrix.translation        # the hip/shoulder after the pelvis lift
    L1, L2 = (Mp - rest[root].translation).length, (Ep - Mp).length
    d = min(max((T - Hp).length, 0.05), (L1 + L2) * 0.995)
    u = (T - Hp).normalized(); T = Hp + u * d
    a = (L1 * L1 - L2 * L2 + d * d) / (2 * d); h = math.sqrt(max(L1 * L1 - a * a, 0))
    pp = (pole - pole.dot(u) * u).normalized()
    E = Hp + u * a + pp * h
    aim(root, mid, (E - Hp).normalized(), Hp)
    q2 = aim(mid, end, (T - E).normalized(), E)
    rm = rest[end].to_3x3()
    pb[end].matrix = Matrix.Translation(T) @ (Rm @ (rm if foot else idle_hand[end])).to_4x4()
    bpy.context.view_layer.update()


# --- the seated pose
# unicycle model frame (metres: x to the rider's right, y forward, z up) -> world (game units)
def at(p): return fwd * p[1] * s - side * p[0] * s + up * p[2] * s
SADDLE = Vector(tri.SEAT)
HIP_ABOVE_SADDLE = 0.05 * s                       # the thigh root sits a little above the saddle top
seat_lift = (at(SADDLE).z + HIP_ABOVE_SADDLE) - hip_z
Rlean = Matrix.Rotation(LEAN, 3, up.cross(fwd))   # a positive turn tips the top forward (see pogo_hop.py)
Rlean_m = Mi.to_3x3() @ Rlean @ arm.matrix_world.to_3x3()

def pose(phase, hold=0.0):
    """phase: pedal angle in turns (0..1); the right pedal is ahead at 0. hold: 1 = the right hand is on the saddle handle, 0 = both arms out for balance."""
    for p in pb: p.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    pivot = at(SADDLE) + up * HIP_ABOVE_SADDLE + fwd * (-0.02 * s)     # the hip: the torso turns about it
    tilt = lambda v: pivot + Rlean @ (v - pivot)
    pelvis = arm.matrix_world @ rest["Bip01"].translation
    pelvis = pelvis + up * seat_lift + fwd * (-0.02 * s) + side * (SWAY * math.sin(2 * math.pi * phase))
    pb["Bip01"].matrix = Matrix.Translation(Mi @ pelvis) @ (Rlean_m @ rest["Bip01"].to_3x3()).to_4x4()
    bpy.context.view_layer.update()
    for pre, sgn in (("L_", 1), ("R_", -1)):         # sgn: +1 = rider's left (side), -1 = right
        right = sgn < 0
        ang = -2 * math.pi * (phase + (0.0 if right else 0.5))      # clockwise seen from the rider's right: the top of the circle moves forward
        pedal = (-sgn * (tri.PEDAL_X + 0.02), tri.HUB[1] + tri.CRANK * math.cos(ang), tri.HUB[2] + tri.CRANK * math.sin(ang) + 0.02)
        foot_t = at(pedal) + up * ankle
        hand = f"Bip01_{pre}Hand"
        prop_off = arm.matrix_world.to_3x3() @ (Rlean_m @ idle_hand[hand]) @ next(r for (h, _), r in prop_rel.items() if h == hand).translation
        out = at((-sgn * 0.50, 0.05, 0.95)) + side * (WAVE * math.sin(2 * math.pi * phase * 2 * (1 if sgn > 0 else -1))) + up * (WAVE * math.cos(2 * math.pi * phase))      # arm out
        if sgn < 0: grip = (1 - hold) * (out + prop_off) + hold * at((-sgn * tri.GRIP[0], tri.GRIP[1], tri.GRIP[2]))               # right hand: from the handle to out
        else: grip = out + prop_off
        limb(f"Bip01_{pre}Thigh", f"Bip01_{pre}Calf", f"Bip01_{pre}Foot", foot_t, Rlean @ (fwd * 1.0 + up * 0.7 + side * sgn * 0.25), True, Rlean_m)
        limb(f"Bip01_{pre}UpperArm", f"Bip01_{pre}Forearm", f"Bip01_{pre}Hand", grip - prop_off, Rlean @ (-fwd * 0.3 + side * sgn * 0.6 - up * 0.6), False, Rlean_m)
    for (h, pr), rel in prop_rel.items():
        # the held model hangs off Bip01_Prop1: it stays at the saddle handle however far the right arm goes out
        at_prop = Mi @ at(tri.GRIP) if pr == "Bip01_Prop1" else (pb[h].matrix @ rel).translation
        pb[pr].matrix = Matrix.Translation(at_prop) @ (idle_hand[h] @ rel.to_3x3()).to_4x4()
    bpy.context.view_layer.update()
    local = {}
    for n in order:
        parent = pb[n].parent
        local[n] = (parent.matrix.inverted() @ pb[n].matrix) if parent else pb[n].matrix.copy()
    return local

CYCLE = {"": 24, "Run": 16}                       # frames per pedal turn: the run clip pedals faster
# target speeds in tiles/s: the pogo measured ~1.45 tiles/s per (Translation_Data travel / clip seconds), bare walking is ~1.0; the unicycle is slower still
SPEED = {"": 0.4, "Run": 0.6}
TILES_PER_TRAVEL_SECOND = 1.45
TIERS = {"": 1.0, "T1": 0.6, "T2": 0.3}           # same meaning as the pogo's: loose ground, tiredness
import clipio
write_clip, blend = clipio.make(order, OUT_X.parent)
for kind, frames in CYCLE.items():
    samples = {f: pose(f / frames) for f in range(frames + 1)}
    for tier, tf in TIERS.items():
        write_clip(f"Bob_UniRide{kind}{tier}", samples, frames, SPEED[kind] * (frames / FPS) / TILES_PER_TRAVEL_SECOND * tf)
idle = pose(0.0)
write_clip("Bob_UniIdle", {0: idle, 12: idle}, 12, 0)
# mount: stand -> on the saddle with the right hand on the handle -> the arm goes out; dismount is the reverse (the loop starts at pose(0.0))
MOUNT_FRAMES = 32
stand = idle_local
seated, out = pose(0.0, 1.0), pose(0.0, 0.0)
write_clip("Bob_UniMount", {0: stand, 8: blend(stand, seated, 0.5), 16: seated, 32: out}, MOUNT_FRAMES, 0)
write_clip("Bob_UniDismount", {0: out, 16: seated, 24: blend(seated, stand, 0.5), 32: stand}, MOUNT_FRAMES, 0)
# wobble (the stall): the rider rocks wildly and flails an arm while the wheel goes nowhere, zero travel; the Lua plays it for a second or two
SWAY, WAVE = 0.09 * s, 0.22 * s
write_clip("Bob_UniSlip", {f: pose(2 * f / 24) for f in range(25)}, 24, 0)

# --- preview: read the ride clip back with the game-format reader, place the unicycle, render frames
bpy.ops.wm.read_factory_settings(use_empty=True)
arm, meshes, rl, _ = zx.import_body(GAME / "models_X/Skinned/MaleBody.x")
act, last = zx.import_animation(OUT_X, arm, rl, "Bob_UniRide", fps=FPS)
body_mat = bpy.data.materials.new("Survivor"); body_mat.diffuse_color = (0.35, 0.45, 0.6, 1)
for m in meshes: m.data.materials.append(body_mat)
unicycle = tri.build()
M = Matrix(((-side.x, fwd.x, up.x), (-side.y, fwd.y, up.y), (-side.z, fwd.z, up.z))).to_4x4()      # columns: model x -> -side, y -> fwd, z -> up
unicycle.matrix_world = M @ Matrix.Scale(s, 4)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x = sc.render.resolution_y = 520
sc.display.shading.color_type = "MATERIAL"; sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.85, 0.85, 0.9)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 1.5
look = Vector((0, 0, 0.5))
for view in ("side", "front"):
    cam.location = (fwd.cross(up) * 6 if view == "side" else fwd * 6) + look
    cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
    for name, fr in (("a", 1), ("b", 7), ("c", 13), ("d", 19)):
        sc.frame_set(fr); sc.render.filepath = str(PREVIEW / f"uni_{view}_{name}.png"); bpy.ops.render.render(write_still=True)
