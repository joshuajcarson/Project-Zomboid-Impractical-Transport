"""Render every frame of the hop clip (survivor + pogo stick, side and front) into previews/demo/ for a GIF.
  blender -b -P tools/blender/pogo_hop_demo.py      then: python tools/blender/make_gif.py"""
import bpy, sys, math, os, pathlib
from mathutils import Vector
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import zomboid_x as zx
import pogo_stick

GAME = pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media")
ROOT = pathlib.Path(__file__).resolve().parents[2]
import os
NAME = os.environ.get("CLIP", "Bob_PogoHop")     # Bob_PogoMount / Bob_PogoDismount render the body only (the stick is placed by hand here, not by its attachment)
CLIP = ROOT / f"Contents/mods/ImpracticalTransport/42/media/anims_X/Bob/{NAME}.X"
OUT = ROOT / "previews" / "demo"; OUT.mkdir(parents=True, exist_ok=True)
LIFT = [(0, 0.01), (4, 0.045), (8, -0.012), (12, 0), (18, 0.01), (21, 0.03), (24, 0.01)]   # stick height per frame: the stick_lift column of KEYS in pogo_hop.py (sink is the body's)
KEYS = [(0, 0, 0.01), (4, 0, 0.045), (8, 0.012, -0.012), (12, 0.075, 0), (18, 0.02, 0.01), (21, 0, 0.03), (24, 0, 0.01)]

bpy.ops.wm.read_factory_settings(use_empty=True)
arm, meshes, rl, _ = zx.import_body(GAME / "models_X/Skinned/MaleBody.x")
zx.import_animation(CLIP, arm, rl, NAME, fps=30)
body_mat = bpy.data.materials.new("Survivor"); body_mat.diffuse_color = (0.35, 0.45, 0.6, 1)
for m in meshes: m.data.materials.append(body_mat)
stick = pogo_stick.build(); stick.scale = [pogo_stick.GAME_UNITS_PER_METRE] * 3; stick.hide_render = NAME != "Bob_PogoHop"
fwd = None
sc = bpy.context.scene
bpy.context.view_layer.update()
wr = lambda n: arm.matrix_world @ arm.data.bones[n].matrix_local.translation
fwd = wr("Bip01_L_Toe0") - wr("Bip01_L_Foot"); fwd.z = 0; fwd.normalize()
up = Vector((0, 0, 1)); sideaxis = fwd.cross(up)
ankle = wr("Bip01_L_Foot").z
def stick_z(fr):
    for (a, la), (b, lb) in zip(KEYS, KEYS[1:]):
        if a <= fr <= b: return la + (lb - la) * (fr - a) / (b - a)
KEYS = [(f, l) for f, l, _ in KEYS]
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x = sc.render.resolution_y = 400
sc.display.shading.color_type = "MATERIAL"; sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.85, 0.85, 0.9)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 1.5
look = Vector((0, 0, 0.55))
for view, d in (("side", sideaxis), ("front", fwd)):
    cam.location = d * 6 + look; cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
    for fr in range(0, 24):
        sc.frame_set(fr)
        stick.location = (0, 0, stick_z(fr))
        stick.rotation_mode = 'AXIS_ANGLE'; stick.rotation_axis_angle = (math.radians(float(os.environ.get('LEAN_DEG', 12))), *up.cross(fwd))
        sc.render.filepath = str(OUT / f"{NAME}_{view}_{fr:02d}.png"); bpy.ops.render.render(write_still=True)
print("rendered")
