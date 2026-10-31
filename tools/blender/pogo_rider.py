"""Survivor riding the pogo stick, hopping. Renders previews/pogo_rider.mp4 (+ a still).
  blender -b -P tools/blender/pogo_rider.py
Arms and legs are posed with IK to targets on the stick, so the stick model can change without re-posing by hand.
Preview only: reads the game's own body model from the install, writes nothing into the mod."""
import bpy, sys, math, pathlib
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import zomboid_x as zx

GAME = pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media")
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "previews"; OUT.mkdir(exist_ok=True)
FPS, PERIOD = 24, 24

bpy.ops.wm.read_factory_settings(use_empty=True)
arm, meshes, rest_local, rest_world = zx.import_body(GAME / "models_X/Skinned/MaleBody.x")
bpy.context.view_layer.update()
head_z = (arm.matrix_world @ arm.data.bones["Bip01_Head"].head_local).z
H = head_z * 1.12                       # character height in scene units
s = H / 1.8                             # the pogo stick is modelled for a 1.8 m rider

import bpy as _b
body_mat = _b.data.materials.new('Survivor'); body_mat.diffuse_color = (0.35, 0.45, 0.6, 1)
for m in meshes: m.data.materials.append(body_mat)

# --- pogo stick, scaled to the rider
import pogo_stick
pogo = pogo_stick.build()
pogo.scale = (s, s, s)

def empty(name, loc):
    e = bpy.data.objects.new(name, None); e.location = loc; bpy.context.scene.collection.objects.link(e); return e

# rider faces +Y after the Z-up fix? find out from the feet: toe is ahead of the foot
def wpos(b, tail=False):
    bone = arm.data.bones[b]; return arm.matrix_world @ (bone.tail_local if tail else bone.head_local)
fwd = (wpos("Bip01_L_Toe0") - wpos("Bip01_L_Foot")); fwd.z = 0; fwd.normalize()
side = Vector((0, 0, 1)).cross(fwd)     # rider's left is +side? checked below by the left hand position
if (wpos("Bip01_L_Hand") - wpos("Bip01_R_Hand")).dot(side) < 0: side = -side
# rider's left = +side now
rider = empty("Rider", (0, 0, 0))       # moves with the hop; stick and IK targets are children
pogo.parent = rider
targets = {      # pad tops and grip centres of the stick (see tools/blender/pogo_stick.py), plus the ankle height above the sole
    "Bip01_L_Foot": side * 0.13 * s + Vector((0, 0, 0.3 * s + 0.03)),
    "Bip01_R_Foot": -side * 0.13 * s + Vector((0, 0, 0.3 * s + 0.03)),
    "Bip01_L_Hand": side * 0.15 * s + Vector((0, 0, 1.06 * s)),
    "Bip01_R_Hand": -side * 0.15 * s + Vector((0, 0, 1.06 * s)),
}
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE")
for bone, loc in targets.items():
    t = empty("T_" + bone, loc); t.parent = rider
    c = arm.pose.bones[bone].constraints.new("IK"); c.target = t; c.chain_count = 3
    knee = "calf" if "Foot" in bone else "forearm"
    pole_dir = fwd * 0.6 if "Foot" in bone else (-fwd * 0.3 + (side if "L_" in bone else -side) * 0.4)
    base = wpos(bone.replace("Foot", "Calf").replace("Hand", "Forearm"))
    pole = empty("P_" + bone, base + pole_dir); pole.parent = rider
    c.pole_target = pole; c.pole_angle = 0
bpy.ops.object.mode_set(mode="OBJECT")

# pick each pole angle so knees point forward and elbows point back/out (the bone axes are arbitrary, so search for it)
def tune(bone, mid, root, desired):
    c = arm.pose.bones[bone].constraints[0]
    best = None
    for deg in range(-180, 180, 15):
        c.pole_angle = math.radians(deg)
        bpy.context.view_layer.update()
        mid_pos = arm.matrix_world @ arm.pose.bones[mid].head
        line = (arm.matrix_world @ arm.pose.bones[root].head + c.target.matrix_world.translation) / 2
        score = (mid_pos - line).dot(desired)
        if best is None or score > best[0]: best = (score, deg)
    c.pole_angle = math.radians(best[1])
    print("tuned", bone, best)

sc0 = bpy.context.scene; sc0.frame_set(1)
for sgn, pre in ((1, "L_"), (-1, "R_")):
    tune(f"Bip01_{pre}Foot", f"Bip01_{pre}Calf", f"Bip01_{pre}Thigh", fwd)
    tune(f"Bip01_{pre}Hand", f"Bip01_{pre}Forearm", f"Bip01_{pre}UpperArm", -fwd * 0.5 + side * sgn * 0.8)

# --- hop: rider lifts, body drops during the push-off compression
body_z0 = arm.location.z
h, c = 0.18 * H, 0.14 * H
keys = [(1, 0, 0), (5, 0, -c), (9, 0, 0), (16, h, 0), (21, 0.02, 0), (25, 0, 0)]
for f, rz, bz in keys:
    rider.location.z = rz; rider.keyframe_insert("location", index=2, frame=f)
    arm.location.z = body_z0 + rz + bz + 0.0; arm.keyframe_insert("location", index=2, frame=f)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, PERIOD
# the rider's pelvis starts at standing height; lift it so the legs reach the pegs (feet target at 0.37 s)
print("H", H, "fwd", fwd, "side", side)

# --- render
sc.render.fps = FPS
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x = sc.render.resolution_y = 600
sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.85, 0.85, 0.9)
bpy.ops.mesh.primitive_plane_add(size=6); bpy.context.active_object.name = "Ground"
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = H * 1.35
import os
cam.location = (fwd * 6 if os.environ.get('VIEW') == 'front' else fwd.cross(Vector((0, 0, 1))) * 6) + Vector((0, 0, H * 0.5))
cam.rotation_euler = ((Vector((0, 0, 0)) - cam.location + Vector((0, 0, H * 0.5))).to_track_quat("-Z", "Y")).to_euler()
sc.render.filepath = str(OUT / "pogo_rider_still.png"); sc.frame_set(9); bpy.ops.render.render(write_still=True)
sc.render.image_settings.file_format = "FFMPEG"; sc.render.ffmpeg.format = "MPEG4"; sc.render.ffmpeg.codec = "H264"
sc.render.filepath = str(OUT / "pogo_rider.mp4"); bpy.ops.render.render(animation=True)

if "--debug" in sys.argv:
    sc.frame_set(9); bpy.context.view_layer.update()
    print("DBG pogo dims", tuple(pogo.dimensions), "scale", tuple(pogo.scale))
    for b in ("Bip01_L_Foot", "Bip01_L_Hand", "Bip01_Pelvis", "Bip01_Spine1", "Bip01_Head", "Bip01_L_Calf", "Bip01_L_Thigh"):
        pb = arm.pose.bones[b]; print("DBG", b, tuple(arm.matrix_world @ pb.head), [ (c.type, c.influence, c.mute) for c in pb.constraints])
    for n in ("T_Bip01_L_Foot", "T_Bip01_L_Hand"):
        print("DBG", n, tuple(bpy.data.objects[n].matrix_world.translation))

if "--debug" in sys.argv:
    dg = bpy.context.evaluated_depsgraph_get()
    for ob in meshes:
        ev = ob.evaluated_get(dg); me = ev.to_mesh()
        zs = [(ev.matrix_world @ v.co).z for v in me.vertices]
        print("DBG mesh z range", min(zs), max(zs), "scale", tuple(ob.scale), tuple(ob.matrix_world.to_scale()))
    print("DBG arm scale", tuple(arm.scale), tuple(arm.matrix_world.to_scale()), "loc", tuple(arm.location))
    print("DBG bone scales", [(pb.name, tuple(round(x,2) for x in pb.scale)) for pb in arm.pose.bones if abs(pb.scale.z-1)>0.01][:6])

if "--debug" in sys.argv:
    sc.frame_set(9); bpy.context.view_layer.update()
    for b in ("Bip01_L_UpperArm", "Bip01_L_Forearm", "Bip01_L_Hand", "Bip01_R_Hand"):
        pb = arm.pose.bones[b]; print("DBG2", b, "head", tuple(round(x, 3) for x in (arm.matrix_world @ pb.head)), "tail", tuple(round(x, 3) for x in (arm.matrix_world @ pb.tail)), "len", round(pb.length, 3))
    print("DBG2 targets", [(n, tuple(round(x, 3) for x in bpy.data.objects[n].matrix_world.translation)) for n in ("T_Bip01_L_Hand", "T_Bip01_R_Hand")])
    print("DBG2 clavicle", [(b, tuple(round(x,3) for x in (arm.matrix_world @ arm.pose.bones[b].head))) for b in ("Bip01_L_Clavicle","Bip01_Spine1")])

if "--debug" in sys.argv:
    sc.frame_set(9); bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get(); ev = meshes[0].evaluated_get(dg); me = ev.to_mesh()
    xs = [(ev.matrix_world @ v.co).x for v in me.vertices]; print("DBG3 x range", min(xs), max(xs))
    ob = meshes[0]; names = [vg.name for vg in ob.vertex_groups]; print("DBG3 groups", len(names), [n for n in names if "Arm" in n or "Hand" in n or "Clav" in n])
    print("DBG3 mods", [(m.name, m.object.name if m.object else None) for m in ob.modifiers], "parent", ob.parent.name if ob.parent else None, "armdata", ob.parent.data.pose_position)
