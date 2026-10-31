"""Survivor riding the pogo stick, hopping. Renders previews/pogo_rider.mp4 (+ a still).
  blender -b -P tools/blender/pogo_rider.py            side view
  VIEW=front blender -b -P tools/blender/pogo_rider.py front view
Legs and arms are posed with a small two-bone solver (hip/shoulder -> knee/elbow -> ankle/wrist) at each key pose, so the
stick model can change without re-posing by hand. Preview only: reads the game's own body model from the install."""
import bpy, sys, math, os, pathlib
from mathutils import Vector, Matrix
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import zomboid_x as zx
import pogo_stick

GAME = pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media")
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "previews"; OUT.mkdir(exist_ok=True)
FPS, PERIOD = 24, 24
VIEW = os.environ.get("VIEW", "side")

bpy.ops.wm.read_factory_settings(use_empty=True)
arm, meshes, _, _ = zx.import_body(GAME / "models_X/Skinned/MaleBody.x")
bpy.context.view_layer.update()
body_mat = bpy.data.materials.new("Survivor"); body_mat.diffuse_color = (0.35, 0.45, 0.6, 1)
for m in meshes: m.data.materials.append(body_mat)

bones = arm.data.bones
rest = {b.name: b.matrix_local.copy() for b in bones}              # armature-space rest matrices
rest_world_head = lambda n: arm.matrix_world @ rest[n].translation
H = (rest_world_head("Bip01_Head").z) * 1.12                       # character height in scene units
s = H / 1.8 * 1.3                                                  # the stick is modelled for a child: 1.3x for an adult rider (pads ~0.4 m, grips at chest height)
ankle = rest_world_head("Bip01_L_Foot").z                          # ankle height above the sole at rest
fwd = rest_world_head("Bip01_L_Toe0") - rest_world_head("Bip01_L_Foot"); fwd.z = 0; fwd.normalize()
side = Vector((0, 0, 1)).cross(fwd)
if (rest_world_head("Bip01_L_Hand") - rest_world_head("Bip01_R_Hand")).dot(side) < 0: side = -side   # side = rider's left

pogo = pogo_stick.build(); pogo.scale = (s, s, s)
rider = bpy.data.objects.new("Rider", None); bpy.context.scene.collection.objects.link(rider); pogo.parent = rider

# visible aim points for hand editing in Blender: where each hand/foot should end up (they ride with the stick)
for pre, sgn in (("L", 1), ("R", -1)):
    for nm, off in ((f"Aim_{pre}_Foot", side * sgn * 0.13 * s + Vector((0, 0, 0.3 * s + ankle))), (f"Aim_{pre}_Hand", side * sgn * 0.15 * s + Vector((0, 0, 1.07 * s)))):
        e = bpy.data.objects.new(nm, None); e.empty_display_type = "SPHERE"; e.empty_display_size = 0.02; e.location = off
        bpy.context.scene.collection.objects.link(e); e.parent = rider

# --- two-bone solver, in armature space
pb = arm.pose.bones
for p in pb: p.rotation_mode = "QUATERNION"
last_q = {}

def aim(name, new_dir, head):
    """Pose bone `name` so its Y axis points along new_dir with its head at `head` (armature space); returns the swing rotation."""
    rm = rest[name].to_3x3()
    q = (rm @ Vector((0, 1, 0))).rotation_difference(new_dir)
    pb[name].matrix = Matrix.Translation(head) @ (q.to_matrix() @ rm).to_4x4()
    bpy.context.view_layer.update()
    return q

def limb(root, mid, end, target_world, pole_world, foot):
    Mi = arm.matrix_world.inverted()
    T, pole = Mi @ target_world, Mi.to_3x3() @ pole_world
    Hp, Mp, Ep = rest[root].translation, rest[mid].translation, rest[end].translation
    L1, L2 = (Mp - Hp).length, (Ep - Mp).length
    d = min(max((T - Hp).length, 0.05), (L1 + L2) * 0.995)
    u = (T - Hp).normalized(); T = Hp + u * d
    a = (L1 * L1 - L2 * L2 + d * d) / (2 * d); h = math.sqrt(max(L1 * L1 - a * a, 0))
    pp = (pole - pole.dot(u) * u).normalized()
    E = Hp + u * a + pp * h
    aim(root, (E - Hp).normalized(), Hp)
    q2 = aim(mid, (T - E).normalized(), E)
    rm = rest[end].to_3x3()
    pb[end].matrix = Matrix.Translation(T) @ ((rm if foot else q2.to_matrix() @ rm)).to_4x4()   # foot stays flat, wrist follows the forearm
    bpy.context.view_layer.update()

def key(names, frame):
    for n in names:
        q = pb[n].rotation_quaternion
        if n in last_q and q.dot(last_q[n]) < 0: pb[n].rotation_quaternion = -q      # keep the shortest path between key poses
        last_q[n] = pb[n].rotation_quaternion.copy()
        pb[n].keyframe_insert("rotation_quaternion", frame=frame); pb[n].keyframe_insert("location", frame=frame)

LIMBS = [("Thigh", "Calf", "Foot", True), ("UpperArm", "Forearm", "Hand", False)]
h_hop, crouch = 0.2 * H, 0.12 * H
keys = [(1, 0, 0), (5, 0, -crouch), (9, 0, 0), (16, h_hop, 0), (21, 0.02, 0), (25, 0, 0)]    # (frame, stick lift, body drop)
for f, rz, bz in keys:
    rider.location.z = rz; rider.keyframe_insert("location", index=2, frame=f)
    arm.location.z = rz + bz; arm.keyframe_insert("location", index=2, frame=f)
    bpy.context.view_layer.update()
    for pre, sgn in (("L_", 1), ("R_", -1)):
        foot_t = rider.location + side * sgn * 0.13 * s + Vector((0, 0, 0.3 * s + ankle))
        hand_t = rider.location + side * sgn * 0.15 * s + Vector((0, 0, 1.07 * s))
        limb(f"Bip01_{pre}Thigh", f"Bip01_{pre}Calf", f"Bip01_{pre}Foot", foot_t, fwd + side * sgn * 0.15, True)
        limb(f"Bip01_{pre}UpperArm", f"Bip01_{pre}Forearm", f"Bip01_{pre}Hand", hand_t, -fwd * 0.4 + side * sgn * 0.9 + Vector((0, 0, -0.3)), False)
        key([f"Bip01_{pre}{n}" for grp in LIMBS for n in grp[:3]], f)

# --- render
sc = bpy.context.scene
sc.frame_start, sc.frame_end, sc.render.fps = 1, PERIOD, FPS
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x = sc.render.resolution_y = 600
sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.85, 0.85, 0.9)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = H * 1.6
look = Vector((0, 0, H * 0.55))
cam.location = (fwd * 6 if VIEW == "front" else side.cross(Vector((0, 0, 1))) * -6 if False else fwd.cross(Vector((0, 0, 1))) * 6) + look
cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
for name, fr in (("crouch", 5), ("apex", 16)):
    sc.frame_set(fr); sc.render.filepath = str(OUT / f"pogo_rider_{VIEW}_{name}.png"); bpy.ops.render.render(write_still=True)
if VIEW == "side":
    sc.render.image_settings.file_format = "FFMPEG"; sc.render.ffmpeg.format = "MPEG4"; sc.render.ffmpeg.codec = "H264"
    sc.render.filepath = str(OUT / "pogo_rider.mp4"); bpy.ops.render.render(animation=True)

bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "pogo_rider.blend"))

# --- editable version: IK constraints aimed at the Aim_* empties (move an empty and the hand/foot follows) ---------------
arm.animation_data_clear()
for p in pb:
    p.rotation_quaternion, p.location = (1, 0, 0, 0), (0, 0, 0)
for f, rz, bz in keys:
    arm.location.z = rz + bz; arm.keyframe_insert("location", index=2, frame=f)
bpy.context.view_layer.update()
sc.frame_set(1)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE")
for pre, sgn in (("L", 1), ("R", -1)):
    for part, mid, root, pole_dir in (("Foot", "Calf", "Thigh", fwd + side * sgn * 0.15),
                                      ("Hand", "Forearm", "UpperArm", -fwd * 0.4 + side * sgn * 0.9 + Vector((0, 0, -0.3)))):
        bone = f"Bip01_{pre}_{part}"
        con = pb[bone].constraints.new("IK"); con.target = bpy.data.objects[f"Aim_{pre}_{part}"]; con.chain_count = 3
        pole = bpy.data.objects.new(f"Pole_{pre}_{part}", None); pole.empty_display_type = "CUBE"; pole.empty_display_size = 0.015
        bpy.context.scene.collection.objects.link(pole); pole.parent = rider
        pole.location = rest_world_head(f"Bip01_{pre}_{mid}") + pole_dir * 0.5
        con.pole_target = pole
        best = None
        for deg in range(-180, 180, 15):
            con.pole_angle = math.radians(deg); bpy.context.view_layer.update()
            score = ((arm.matrix_world @ pb[f"Bip01_{pre}_{mid}"].head) - (arm.matrix_world @ pb[f"Bip01_{pre}_{root}"].head)).dot(pole_dir)
            if best is None or score > best[0]: best = (score, deg)
        con.pole_angle = math.radians(best[1])
bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "pogo_rider_ik.blend"))
