"""Build a unicycle from primitives and write models_X/ImpracticalTransport/Unicycle.X, its palette texture and an inventory icon.
  blender -b -P tools/blender/unicycle.py
Blender metres, x sideways, y forward, z up; the origin is on the ground under the wheel. One wheel, a fork, a saddle with a grab handle at the
front (the right hand holds it, the other arm is out for balance) and two cranks with pedals either side of the hub."""
import bpy, math, pathlib, sys
from mathutils import Vector, Quaternion
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import pogo_stick as ps

ROOT = ps.ROOT
MEDIA = ps.MEDIA
XFILE = MEDIA / "models_X/ImpracticalTransport/Unicycle.X"
TEXTURE = MEDIA / "textures/ImpracticalTransport/Unicycle_texture.png"
ICON = MEDIA / "textures/Item_Unicycle.png"

# key points the ride clip and the attachment depend on (metres, model frame)
HUB = (0.0, 0.0, 0.25)               # wheel hub: the pedal cranks turn about it
CRANK = 0.09                         # pedal circle radius
PEDAL_X = 0.10                       # pedals sit this far to each side of the hub
SEAT = (0.0, -0.02, 0.76)            # top of the saddle
GRIP = (0.0, 0.14, 0.80)             # the grab handle at the front of the saddle (the right hand holds it; x = 0 so the offset is the same for any x)


def build():
    before = set(bpy.data.objects.keys())
    BLUE, CHROME, RUBBER = ps.mat("Blue", (0.1, 0.25, 0.8)), ps.mat("Chrome", (0.7, 0.7, 0.75)), ps.mat("Rubber", (0.05, 0.05, 0.05))
    YELLOW, RED = ps.mat("Yellow", (0.95, 0.8, 0.1)), ps.mat("Red", (0.8, 0.1, 0.1))

    def add(op, m, name, **kw):
        op(**kw); o = bpy.context.active_object; o.name = name; o.data.materials.append(m); return o

    def rod(a, b, r, m, name):
        a, b = Vector(a), Vector(b); d = b - a
        o = add(bpy.ops.mesh.primitive_cylinder_add, m, name, radius=r, depth=d.length, location=(a + b) / 2, vertices=8)
        o.rotation_mode = "QUATERNION"; o.rotation_quaternion = d.to_track_quat("Z", "Y"); return o

    def box(loc, size, m, name):
        o = add(bpy.ops.mesh.primitive_cube_add, m, name, location=loc, size=1); o.scale = size; return o

    o = add(bpy.ops.mesh.primitive_torus_add, RUBBER, "Wheel", major_radius=HUB[2] - 0.035, minor_radius=0.035, location=HUB, major_segments=20, minor_segments=6)
    o.rotation_euler = (0, math.pi / 2, 0)
    add(bpy.ops.mesh.primitive_cylinder_add, CHROME, "Hub", radius=0.03, depth=0.16, location=HUB, vertices=8).rotation_euler = (0, math.pi / 2, 0)
    for s in (-1, 1):
        rod((s * 0.05, HUB[1], HUB[2]), (s * 0.05, 0.0, 0.66), 0.012, CHROME, "Fork")                     # fork legs up to the crown
        ang = math.pi / 2 if s > 0 else -math.pi / 2                                                          # cranks point opposite ways
        rod((s * 0.08, HUB[1], HUB[2]), (s * 0.08, HUB[1], HUB[2] + (CRANK if s > 0 else -CRANK)), 0.012, RED, "Crank")
        box((s * PEDAL_X, HUB[1], HUB[2] + (CRANK if s > 0 else -CRANK)), (0.05, 0.10, 0.015), YELLOW, "Pedal")
    rod((-0.05, 0.0, 0.66), (0.05, 0.0, 0.66), 0.012, CHROME, "Crown")
    rod((0, 0.0, 0.66), (0, -0.02, 0.74), 0.016, BLUE, "SeatPost")
    box((0, -0.02, 0.75), (0.16, 0.24, 0.035), BLUE, "Saddle")
    rod((0, 0.08, 0.77), (0, 0.14, 0.80), 0.014, CHROME, "HandleStem")
    box((0, 0.14, 0.80), (0.10, 0.03, 0.025), RED, "Handle")

    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        o.select_set(o.name not in before)
    bpy.context.view_layer.objects.active = bpy.data.objects["Wheel"]
    bpy.ops.object.join()
    bpy.context.active_object.name = "Unicycle"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)      # the join target (a turned tyre) must not leave its rotation in the exported mesh
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    return bpy.context.active_object


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = build()
    ps.export_x(obj, XFILE, texture=TEXTURE)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x = sc.render.resolution_y = 480
    sc.display.shading.color_type = "MATERIAL"; sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.85, 0.85, 0.9)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 1.1
    ps.PREVIEW.mkdir(exist_ok=True)
    for name, rot, loc in (("front", (math.pi / 2, 0, 0), (0, -3, 0.4)), ("side", (math.pi / 2, 0, math.pi / 2), (3, 0, 0.4)),
                           ("three_quarter", (math.radians(70), 0, math.radians(35)), (1.8, -2.2, 1.4))):
        cam.rotation_euler, cam.location = rot, loc
        sc.render.filepath = str(ps.PREVIEW / f"unicycle_{name}.png"); bpy.ops.render.render(write_still=True)
    # inventory icon: the same transparent diagonal-free render as the other items, three-quarter view
    sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = 64
    sc.render.image_settings.color_mode = "RGBA"; cam.data.ortho_scale = 1.15
    look = Vector((0, 0.0, 0.4)); cam.location = look + Vector((1.8, -2.2, 1.4)).normalized() * 6
    cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = str(ICON); bpy.ops.render.render(write_still=True)
    print("exported", XFILE)


if __name__ == "__main__":
    main()
