"""Build the pogo stick from primitives, export FBX, render preview PNGs.
  blender -b -P tools/blender/pogo_stick.py
Meters, Z up, base of the stick at z=0. Flat-colour materials only, so no texture files are needed yet."""
import bpy, math, pathlib

ROOT = pathlib.Path(bpy.data.filepath or __file__).resolve()
ROOT = pathlib.Path(__file__).resolve().parents[2]
FBX = ROOT / "Contents/mods/ImpracticalTransport/42/media/models_X/ImpracticalTransport/PogoStick.fbx"
PREVIEW = ROOT / "previews"

bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, rgb):
    m = bpy.data.materials.new(name); m.diffuse_color = (*rgb, 1); return m

RED, STEEL, RUBBER, YELLOW = mat("Red", (0.75, 0.1, 0.1)), mat("Steel", (0.6, 0.6, 0.65)), mat("Rubber", (0.05, 0.05, 0.05)), mat("Yellow", (0.9, 0.75, 0.1))

def add(op, m, name, **kw):
    op(**kw); o = bpy.context.active_object; o.name = name; o.data.materials.append(m); return o

add(bpy.ops.mesh.primitive_cylinder_add, RUBBER, "Foot", radius=0.04, depth=0.04, location=(0, 0, 0.02), vertices=12)
add(bpy.ops.mesh.primitive_cylinder_add, STEEL, "InnerShaft", radius=0.012, depth=0.45, location=(0, 0, 0.265), vertices=10)
# spring: stacked rings stand in for a coil (low poly)
for i in range(8):
    r = add(bpy.ops.mesh.primitive_torus_add, YELLOW, f"Coil{i}", major_radius=0.03, minor_radius=0.006, location=(0, 0, 0.12 + i * 0.045),
            major_segments=12, minor_segments=5)
add(bpy.ops.mesh.primitive_cylinder_add, RED, "OuterTube", radius=0.025, depth=0.55, location=(0, 0, 0.78), vertices=12)
add(bpy.ops.mesh.primitive_cube_add, RED, "FootPegL", location=(-0.09, 0, 0.45), size=1).scale = (0.07, 0.03, 0.015)
add(bpy.ops.mesh.primitive_cube_add, RED, "FootPegR", location=(0.09, 0, 0.45), size=1).scale = (0.07, 0.03, 0.015)
add(bpy.ops.mesh.primitive_cylinder_add, STEEL, "Handle", radius=0.012, depth=0.5, location=(0, 0, 1.08), rotation=(0, math.pi / 2, 0), vertices=8)
for s in (-1, 1):
    add(bpy.ops.mesh.primitive_cylinder_add, RUBBER, "Grip", radius=0.018, depth=0.1, location=(s * 0.2, 0, 1.08), rotation=(0, math.pi / 2, 0), vertices=8)

bpy.ops.object.select_all(action="DESELECT")
for o in bpy.data.objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects["OuterTube"]
bpy.ops.object.join()
bpy.context.active_object.name = "PogoStick"

FBX.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.fbx(filepath=str(FBX), use_selection=True, apply_unit_scale=True, axis_forward="-Z", axis_up="Y")

# previews: three angles, solid shading via the workbench engine (fast, no lighting setup)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x = sc.render.resolution_y = 480
sc.display.shading.color_type = "MATERIAL"; sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.85, 0.85, 0.9)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 1.5
PREVIEW.mkdir(exist_ok=True)
for name, rot, loc in (("front", (math.pi / 2, 0, 0), (0, -3, 0.6)), ("side", (math.pi / 2, 0, math.pi / 2), (3, 0, 0.6)),
                       ("three_quarter", (math.radians(75), 0, math.radians(40)), (2, -2.4, 1.2))):
    cam.rotation_euler, cam.location = rot, loc
    sc.render.filepath = str(PREVIEW / f"pogo_{name}.png"); bpy.ops.render.render(write_still=True)
print("exported", FBX)
