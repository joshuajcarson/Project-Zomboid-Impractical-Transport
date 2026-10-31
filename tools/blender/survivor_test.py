"""Import the survivor and one Bob animation, render a few frames. blender -b -P tools/blender/survivor_test.py -- <AnimName>"""
import bpy, sys, math, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import zomboid_x as zx
GAME = pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media")
OUT = pathlib.Path(__file__).resolve().parents[2] / "previews"; OUT.mkdir(exist_ok=True)
anim = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else None
bpy.ops.wm.read_factory_settings(use_empty=True)
arm, meshes, rest_local, rest_world = zx.import_body(GAME / "models_X/Skinned/MaleBody.x")
print("bones", len(arm.data.bones), "meshes", [m.name for m in meshes], "verts", [len(m.data.vertices) for m in meshes])
if anim:
    act, n = zx.import_animation(GAME / f"anims_X/Bob/{anim}.X", arm, rest_local)
    print("anim frames", n)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x = sc.render.resolution_y = 480
sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.85, 0.85, 0.9)
import os; sc.frame_set(int(os.environ.get("F", "1")))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 2.4
for name, rot, loc in (("front", (math.pi / 2, 0, 0), (0, -5, 0.9)), ("side", (math.pi / 2, 0, math.pi / 2), (5, 0, 0.9))):
    cam.rotation_euler, cam.location = rot, loc
    sc.render.filepath = str(OUT / f"survivor_{anim or 'rest'}_{name}.png"); bpy.ops.render.render(write_still=True)
