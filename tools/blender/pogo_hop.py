"""Build the pogo hop animation for the game's survivor and write it as a text DirectX .X clip.
  blender -b -P tools/blender/pogo_hop.py            writes media/anims_X/Bob/Bob_PogoHop.X and previews/pogo_hop_*.png
The clip keys every bone of the player skeleton: pelvis lift for the bounce, knees and elbows from a two-bone solver so the
feet stay on the pads and the hands on the grips. Translation_Data carries the forward travel per hop, which is what moves the
character in game (speed = DISTANCE / DURATION x the anim node's speed scale). Preview only reads the game's own body model."""
import bpy, sys, math, os, pathlib
from mathutils import Vector, Matrix
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import zomboid_x as zx
import pogo_stick

GAME = pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media")
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_X = ROOT / "Contents/mods/ImpracticalTransport/42/media/anims_X/Bob/Bob_PogoHop.X"
PREVIEW = ROOT / "previews"; PREVIEW.mkdir(exist_ok=True)

FPS, FRAMES = 30, 24            # one hop = 0.8 s
TPS = 4800                      # ticks per second the game's clips use
DISTANCE = 0.44                 # Translation_Data travel per hop. Measured in game: 0.64 gave 1.17 tiles/s (79% of walking), so 0.44 aims for ~0.8 tiles/s
s = pogo_stick.GAME_UNITS_PER_METRE   # stick scale, so grips and pads land where the model puts them

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
grip_z, pad_z = 0.92 * s, 0.3 * s
STAND_LIFT = float(os.environ.get("STAND_LIFT", 0.0))     # pelvis lift for the rest pose: 0 = the survivor's own standing height
base_lift = (grip_z + 0.8 * Larm - sh_off) - hip_z     # hands hang 0.8 of an arm length below the shoulders at the grips (nearly straight arms, knees moderately bent)

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

# (frame, stick lift, body sink relative to the stick): crouch, push off, airborne, descend, land
KEYS = [(0, 0.0, 0.01), (4, 0.0, 0.045), (8, 0.012, -0.012), (12, 0.075, 0.0), (18, 0.02, 0.01), (21, 0.0, 0.03), (24, 0.0, 0.01)]

# Aiming is blocked while riding, so there is no backwards hop: the whole rider + stick leans forward about the stick's tip
LEAN = math.radians(float(os.environ.get("LEAN_DEG", 12)))
R = Matrix.Rotation(LEAN, 3, up.cross(fwd))                 # (up x fwd) x up = fwd, so a positive turn tips the top forward (`side` may be flipped, do not use it)
Rm = Mi.to_3x3() @ R @ arm.matrix_world.to_3x3()            # the same turn in armature space

def pose(stick_lift, sink, standing=False):
    """standing: both feet on the ground astride the stick and no lean, hands on the grips (the rest pose); otherwise feet on the pads and the forward lean (the hop)."""
    R_, Rm_ = (Matrix.Identity(3), Mi.to_3x3() @ arm.matrix_world.to_3x3()) if standing else (R, Rm)
    for p in pb: p.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    lift = (STAND_LIFT if standing else base_lift) + stick_lift - sink
    P = up * stick_lift                                     # pivot: the tip of the stick
    tilt = lambda v: P + R_ @ (v - P)
    pelvis = tilt(arm.matrix_world @ rest["Bip01"].translation + up * lift)
    pb["Bip01"].matrix = Matrix.Translation(Mi @ pelvis) @ (Rm_ @ rest["Bip01"].to_3x3()).to_4x4()
    bpy.context.view_layer.update()
    for pre, sgn in (("L_", 1), ("R_", -1)):
        foot_t = tilt(side * sgn * (0.12 if standing else 0.17) * s + up * ((0 if standing else pad_z) + ankle + stick_lift))
        # the model hangs off Bip01_Prop1/2, which sit a little off the hand bone: put THAT bone on the grip, so the hand goes where it must for the prop to land there
        hand = f"Bip01_{pre}Hand"
        prop_off = arm.matrix_world.to_3x3() @ (Rm_ @ idle_hand[hand]) @ next(r for (h, _), r in prop_rel.items() if h == hand).translation
        hand_t = tilt(side * sgn * 0.14 * s + up * (grip_z + stick_lift)) - prop_off
        limb(f"Bip01_{pre}Thigh", f"Bip01_{pre}Calf", f"Bip01_{pre}Foot", foot_t, R_ @ (fwd + side * sgn * 0.15), True, Rm_)
        limb(f"Bip01_{pre}UpperArm", f"Bip01_{pre}Forearm", f"Bip01_{pre}Hand", hand_t, R_ @ (-fwd * 0.5 + side * sgn * 0.3 - up * 0.8), False, Rm_)
    for (h, pr), rel in prop_rel.items():
        # position follows the leaned hand, orientation stays the Bob_Idle one: in game the stick's lean is set by the item's attachment rotate (see
        # ImpracticalTransport_models.txt), because a lean carried by this bone showed up sideways
        pb[pr].matrix = Matrix.Translation((pb[h].matrix @ rel).translation) @ (idle_hand[h] @ rel.to_3x3()).to_4x4()
    bpy.context.view_layer.update()
    local = {}
    for n in order:
        parent = pb[n].parent
        local[n] = (parent.matrix.inverted() @ pb[n].matrix) if parent else pb[n].matrix.copy()
    return local

samples = {fr: pose(lift, sink) for fr, lift, sink in KEYS}
stand = pose(0.0, 0.0, standing=True)

# --- write the .X clips (shared writer)
import clipio
write_clip, blend = clipio.make(order, OUT_X.parent)

# The nodes' m_SpeedScale variables do not change how fast the rider moves (measured 2026-10-31); the travel per hop baked into a clip does. So speed comes
# from separate clips: three gaits x three tiers (tier 0 normal, 1 and 2 slowed by terrain, tiredness or engine slowdown; the Lua picks the tier each tick).
GAITS = {"": 1.0, "Run": 1.7, "Sprint": 2.2}      # clip name suffix -> travel factor (walk 0.8 tiles/s, run measured 1.55x in game)
TIERS = {"": 1.0, "T1": 0.6, "T2": 0.3}
for gait, gf in GAITS.items():
    for tier, tf in TIERS.items():
        write_clip(f"Bob_PogoHop{gait}{tier}", samples, FRAMES, DISTANCE * gf * tf)
MOUNT_FRAMES = 24     # 0.8 s from standing with the stick in hand to the first crouch of a hop; the dismount is the same motion backwards
write_clip("Bob_PogoIdle", {0: stand, 12: stand}, 12, 0)      # the rest pose: standing, both hands on the grips, the stick upright in front
write_clip("Bob_PogoMount", {0: stand, MOUNT_FRAMES // 2: blend(stand, samples[0], 0.5), MOUNT_FRAMES: samples[0]}, MOUNT_FRAMES, 0)
write_clip("Bob_PogoDismount", {0: samples[FRAMES], MOUNT_FRAMES // 2: blend(samples[FRAMES], stand, 0.5), MOUNT_FRAMES: stand}, MOUNT_FRAMES, 0)

# --- round-trip: read the clip back with the game-format reader and render frames to check the motion
bpy.ops.wm.read_factory_settings(use_empty=True)
arm, meshes, rl, _ = zx.import_body(GAME / "models_X/Skinned/MaleBody.x")
act, last = zx.import_animation(OUT_X, arm, rl, "Bob_PogoHop", fps=FPS)
body_mat = bpy.data.materials.new("Survivor"); body_mat.diffuse_color = (0.35, 0.45, 0.6, 1)
for m in meshes: m.data.materials.append(body_mat)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x = sc.render.resolution_y = 520
sc.display.shading.color_type = "MATERIAL"; sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.85, 0.85, 0.9)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 1.5
look = Vector((0, 0, 0.55))
import os
cam.location = (fwd * 6 if os.environ.get('VIEW') == 'front' else fwd.cross(up) * 6) + look
cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
for name, fr in (("crouch", 5), ("apex", 13), ("land", 22)):
    sc.frame_set(fr); sc.render.filepath = str(PREVIEW / f"pogo_hop_{os.environ.get('VIEW', 'side')}_{name}.png"); bpy.ops.render.render(write_still=True)
