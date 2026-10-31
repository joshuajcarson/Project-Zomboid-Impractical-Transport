"""Build the pogo stick from primitives, export FBX, render preview PNGs.
  blender -b -P tools/blender/pogo_stick.py
Meters, Z up, foot of the stick at z=0. Flat-colour materials only, so no texture files are needed yet.
Layout (twin-rail pogo): rubber foot + steel tip, foot pads at the bottom of two side rails, a coil spring around a
centre rod, rails that flare in and then out to two grips."""
import bpy, math, pathlib
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
FBX = ROOT / "Contents/mods/ImpracticalTransport/42/media/models_X/ImpracticalTransport/PogoStick.fbx"
PREVIEW = ROOT / "previews"


def mat(name, rgb):
    m = bpy.data.materials.new(name); m.diffuse_color = (*rgb, 1); return m


def build():
    before = set(bpy.data.objects.keys())     # only join the stick's own parts, not anything else in the scene
    TEAL, STEEL, RUBBER = mat("Teal", (0.0, 0.45, 0.5)), mat("Steel", (0.62, 0.62, 0.68)), mat("Rubber", (0.05, 0.05, 0.05))
    YELLOW, ORANGE, PURPLE = mat("Yellow", (0.95, 0.8, 0.1)), mat("Orange", (0.95, 0.4, 0.05)), mat("Purple", (0.45, 0.15, 0.6))

    def add(op, m, name, **kw):
        op(**kw); o = bpy.context.active_object; o.name = name; o.data.materials.append(m); return o

    def rod(a, b, r, m, name):
        a, b = Vector(a), Vector(b); d = b - a
        o = add(bpy.ops.mesh.primitive_cylinder_add, m, name, radius=r, depth=d.length, location=(a + b) / 2, vertices=8)
        o.rotation_mode = "QUATERNION"; o.rotation_quaternion = d.to_track_quat("Z", "Y"); return o

    def box(loc, size, m, name):
        o = add(bpy.ops.mesh.primitive_cube_add, m, name, location=loc, size=1); o.scale = size; return o

    add(bpy.ops.mesh.primitive_cylinder_add, RUBBER, "Foot", radius=0.035, depth=0.035, location=(0, 0, 0.0175), vertices=12)
    rod((0, 0, 0.035), (0, 0, 0.26), 0.012, STEEL, "Tip")
    box((0, 0, 0.27), (0.3, 0.07, 0.03), TEAL, "FootHub")
    box((-0.13, 0, 0.292), (0.11, 0.13, 0.014), ORANGE, "PadL")
    box((0.13, 0, 0.292), (0.11, 0.13, 0.014), PURPLE, "PadR")
    rod((0, 0, 0.26), (0, 0, 0.9), 0.011, STEEL, "CentreRod")
    for i in range(11):    # coils as stacked rings, low poly
        add(bpy.ops.mesh.primitive_torus_add, YELLOW, f"Coil{i}", major_radius=0.032, minor_radius=0.007,
            location=(0, 0, 0.32 + i * 0.034), major_segments=12, minor_segments=5)
    for s in (-1, 1):
        rod((s * 0.12, 0, 0.27), (s * 0.12, 0, 0.74), 0.011, TEAL, "RailLow")
        rod((s * 0.12, 0, 0.74), (s * 0.03, 0, 0.86), 0.011, TEAL, "RailIn")
        rod((s * 0.03, 0, 0.86), (s * 0.13, 0, 1.0), 0.011, TEAL, "RailOut")
        rod((s * 0.13, 0, 1.0), (s * 0.15, 0, 1.1), 0.021, ORANGE if s < 0 else PURPLE, "Grip")
    box((0, 0, 0.74), (0.26, 0.03, 0.025), TEAL, "Brace")

    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        o.select_set(o.name not in before)
    bpy.context.view_layer.objects.active = bpy.data.objects["Foot"]
    bpy.ops.object.join()
    bpy.context.active_object.name = "PogoStick"
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")   # scale and place the stick from its foot
    return bpy.context.active_object


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    build()
    FBX.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=str(FBX), use_selection=True, apply_unit_scale=True, axis_forward="-Z", axis_up="Y")

    # previews: three angles, solid shading via the workbench engine (fast, no lighting setup)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x = sc.render.resolution_y = 480
    sc.display.shading.color_type = "MATERIAL"; sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.85, 0.85, 0.9)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 1.5
    PREVIEW.mkdir(exist_ok=True)
    for name, rot, loc in (("front", (math.pi / 2, 0, 0), (0, -3, 0.55)), ("side", (math.pi / 2, 0, math.pi / 2), (3, 0, 0.55)),
                           ("three_quarter", (math.radians(75), 0, math.radians(40)), (2, -2.4, 1.0))):
        cam.rotation_euler, cam.location = rot, loc
        sc.render.filepath = str(PREVIEW / f"pogo_{name}.png"); bpy.ops.render.render(write_still=True)
    print("exported", FBX)


if __name__ == "__main__":
    main()
