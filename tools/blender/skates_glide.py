"""Build the roller skating gait for the game's survivor: feet that push out and glide, a crouch, arms swinging, and write the clips.
  blender -b -P tools/blender/skates_glide.py        writes media/anims_X/Bob/Bob_Skate{Idle,Glide,GlideRun}{,T1,T2}.X and previews/skate_*.png
Travel per stride is baked into each clip (the engine's speed controls do not change the rider's speed; see the README)."""
import bpy, sys, math, os, pathlib
from mathutils import Vector, Matrix
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import zomboid_x as zx
import pogo_stick

GAME = pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media")
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_X = ROOT / "Contents/mods/ImpracticalTransport/42/media/anims_X/Bob/Bob_SkateGlide.X"
PREVIEW = ROOT / "previews"; PREVIEW.mkdir(exist_ok=True)
FPS = 30
s = pogo_stick.GAME_UNITS_PER_METRE
LEAN = math.radians(float(os.environ.get("SKATE_LEAN_DEG", 12)))      # torso leans forward over bent knees

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



# --- the skating pose
STRIDE = 0.22 * s         # how far a foot slides forward and back of the hips
CROUCH = 0.06 * s         # the hips drop with bent knees
RAISE = 0.034             # the wheels hang this far below the sole (tools/blender/skates_model.py): the whole rider is lifted by it
ARM = 0.16 * s            # arm swing, opposite to the legs
Rlean = Matrix.Rotation(LEAN, 3, up.cross(fwd))   # a positive turn tips the top forward
Rlean_m = Mi.to_3x3() @ Rlean @ arm.matrix_world.to_3x3()

def pose(phase, stride=1.0, sway=0.0):
    """phase: stride angle in turns (0..1): the left foot is farthest back at 0 and the right foot is half a turn behind it. stride 0 = standing still."""
    for p in pb: p.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    pelvis = arm.matrix_world @ rest["Bip01"].translation + up * (RAISE - CROUCH) + fwd * (0.03 * s) + side * (sway * s)
    pb["Bip01"].matrix = Matrix.Translation(Mi @ pelvis) @ (Rlean_m @ rest["Bip01"].to_3x3()).to_4x4()
    bpy.context.view_layer.update()
    for pre, sgn in (("L_", 1), ("R_", -1)):         # sgn: +1 = rider's left (side), -1 = right
        ph = 2 * math.pi * (phase + (0.0 if sgn > 0 else 0.5))
        c = -math.cos(ph)                            # -1 .. 1: back to forward
        push = max(0.0, math.sin(ph))                # the foot is pushing out and back during half the turn
        foot_t = fwd * (STRIDE * stride * c) + side * sgn * (0.09 + 0.07 * push * stride) * s + up * (ankle + RAISE + 0.035 * s * max(0.0, -math.sin(ph)) * stride)
        limb(f"Bip01_{pre}Thigh", f"Bip01_{pre}Calf", f"Bip01_{pre}Foot", foot_t, Rlean @ (fwd * 1.0 + up * 0.7 + side * sgn * 0.25), True, Rlean_m)
        shoulder = arm.matrix_world @ pb[f"Bip01_{pre}UpperArm"].matrix.translation
        swing = -c * ARM * stride                    # the arm opposite the forward foot swings forward
        hand_t = shoulder + side * sgn * 0.16 * s + fwd * (0.10 * s + swing) + up * (-0.46 * s)
        hand = f"Bip01_{pre}Hand"
        prop_off = arm.matrix_world.to_3x3() @ (Rlean_m @ idle_hand[hand]) @ next(r for (h, _), r in prop_rel.items() if h == hand).translation
        limb(f"Bip01_{pre}UpperArm", f"Bip01_{pre}Forearm", f"Bip01_{pre}Hand", hand_t, Rlean @ (-fwd * 0.3 + side * sgn * 0.6 - up * 0.6), False, Rlean_m)
    for (h, pr), rel in prop_rel.items():
        pb[pr].matrix = Matrix.Translation((pb[h].matrix @ rel).translation) @ (idle_hand[h] @ rel.to_3x3()).to_4x4()
    bpy.context.view_layer.update()
    local = {}
    for n in order:
        parent = pb[n].parent
        local[n] = (parent.matrix.inverted() @ pb[n].matrix) if parent else pb[n].matrix.copy()
    return local

CYCLE = {"": 36, "Run": 24}                       # frames per stride cycle (both feet): the run gait strides faster
# target speeds in tiles/s: worse than walking (about 1.45 tiles/s bare), like every transport in the mod
SPEED = {"": 0.7, "Run": 1.0}
TILES_PER_TRAVEL_SECOND = 1.45
TIERS = {"": 1.0, "T1": 0.6, "T2": 0.3}
import clipio
write_clip, blend = clipio.make(order, OUT_X.parent)
for kind, frames in CYCLE.items():
    samples = {f: pose(f / frames) for f in range(frames + 1)}
    for tier, tf in TIERS.items():
        write_clip(f"Bob_SkateGlide{kind}{tier}", samples, frames, SPEED[kind] * (frames / FPS) / TILES_PER_TRAVEL_SECOND * tf)
# at rest: feet side by side, knees bent, a slow sway so the rider never stands quite still
write_clip("Bob_SkateIdle", {f: pose(0.0, stride=0.0, sway=0.012 * math.sin(2 * math.pi * f / 60)) for f in range(61)}, 60, 0)

# coast: after the keys are released the rider keeps gliding and slows to a stop. The glide STARTS at the speed the rider was going (the same speed as the
# stride clip of that gait and tier: walk, run, and the slower tiers for rough ground or tiredness) and eases out linearly to zero over the clip, so the last
# stretch is never faster than the skating pace. The Lua plays the clip for exactly its length (profile.coast in ImpracticalTransport.lua).
COAST_SECONDS = {"": 0.6, "Run": 1.2}
coast_pose = pose(0.5, stride=0.6)
for kind, seconds in COAST_SECONDS.items():
    frames = int(seconds * FPS)
    for tier, tf in TIERS.items():
        v0 = SPEED[kind] * tf / TILES_PER_TRAVEL_SECOND          # travel units per second at the start
        travel = [(f, v0 * (f / FPS - (f / FPS) ** 2 / (2 * seconds))) for f in range(0, frames + 1, 2)]
        write_clip(f"Bob_SkateCoast{kind}{tier}", {0: coast_pose, frames: coast_pose}, frames, travel)

# --- preview: the stride read back with the game-format reader, side and front views
bpy.ops.wm.read_factory_settings(use_empty=True)
arm, meshes, rl, _ = zx.import_body(GAME / "models_X/Skinned/MaleBody.x")
act, last = zx.import_animation(OUT_X, arm, rl, "Bob_SkateGlide", fps=FPS)
body_mat = bpy.data.materials.new("Survivor"); body_mat.diffuse_color = (0.35, 0.45, 0.6, 1)
for m in meshes: m.data.materials.append(body_mat)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x = sc.render.resolution_y = 520
sc.display.shading.color_type = "MATERIAL"; sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.85, 0.85, 0.9)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 1.5
look = Vector((0, 0, 0.5))
for view in ("side", "front"):
    cam.location = (fwd.cross(up) * 6 if view == "side" else fwd * 6) + look
    cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
    for name, fr in (("a", 1), ("b", 10), ("c", 19), ("d", 28)):
        sc.frame_set(fr); sc.render.filepath = str(PREVIEW / f"skate_{view}_{name}.png"); bpy.ops.render.render(write_still=True)
