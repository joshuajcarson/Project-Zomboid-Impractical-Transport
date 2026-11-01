"""Build the child's tricycle from primitives and write models_X/ImpracticalTransport/Tricycle.X, its palette texture and an inventory icon.
  blender -b -P tools/blender/tricycle.py
Blender metres, x sideways, y forward, z up; the origin is on the ground under the middle of the rear axle. The model is deliberately too small for an
adult: the saddle is 0.44 m up and the pedals hang off the front wheel, so the rider sits with knees up around the handlebar."""
import bpy, math, pathlib, sys
from mathutils import Vector, Quaternion
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import pogo_stick as ps

ROOT = ps.ROOT
MEDIA = ps.MEDIA
XFILE = MEDIA / "models_X/ImpracticalTransport/Tricycle.X"
TEXTURE = MEDIA / "textures/ImpracticalTransport/Tricycle_texture.png"
ICON = MEDIA / "textures/Item_Tricycle.png"

# key points the ride clip and the attachment depend on (metres, model frame)
HUB = (0.0, 0.40, 0.20)             # front wheel hub: the pedal cranks turn about it
CRANK = 0.075                        # pedal circle radius
PEDAL_X = 0.115                      # pedals sit this far to each side of the hub
SEAT = (0.0, -0.12, 0.44)            # top of the saddle
GRIP = (0.24, 0.30, 0.70)            # right handlebar grip (the left one mirrors it)


def build():
    before = set(bpy.data.objects.keys())
    RED, CHROME, RUBBER = ps.mat("Red", (0.75, 0.08, 0.08)), ps.mat("Chrome", (0.7, 0.7, 0.75)), ps.mat("Rubber", (0.05, 0.05, 0.05))
    YELLOW, WHITE = ps.mat("Yellow", (0.95, 0.8, 0.1)), ps.mat("White", (0.9, 0.9, 0.9))

    def add(op, m, name, **kw):
        op(**kw); o = bpy.context.active_object; o.name = name; o.data.materials.append(m); return o

    def rod(a, b, r, m, name):
        a, b = Vector(a), Vector(b); d = b - a
        o = add(bpy.ops.mesh.primitive_cylinder_add, m, name, radius=r, depth=d.length, location=(a + b) / 2, vertices=8)
        o.rotation_mode = "QUATERNION"; o.rotation_quaternion = d.to_track_quat("Z", "Y"); return o

    def box(loc, size, m, name):
        o = add(bpy.ops.mesh.primitive_cube_add, m, name, location=loc, size=1); o.scale = size; return o

    def wheel(centre, radius, tyre, name):
        # tyre: a torus whose axis is x (turned by 90 degrees about y); hub cap on top
        o = add(bpy.ops.mesh.primitive_torus_add, RUBBER, name, major_radius=radius - tyre, minor_radius=tyre, location=centre, major_segments=16, minor_segments=6)
        o.rotation_euler = (0, math.pi / 2, 0)
        add(bpy.ops.mesh.primitive_cylinder_add, CHROME, name + "Hub", radius=0.025, depth=0.07, location=centre, vertices=8).rotation_euler = (0, math.pi / 2, 0)

    wheel(HUB, 0.20, 0.035, "FrontWheel")
    for s in (-1, 1):
        wheel((s * 0.24, -0.22, 0.11), 0.11, 0.03, "RearWheel")
        rod((s * 0.055, HUB[1], HUB[2]), (s * 0.055, 0.34, 0.60), 0.011, CHROME, "Fork")                   # fork legs
        rod((s * 0.0, -0.22, 0.11), (s * 0.24, -0.22, 0.11), 0.011, CHROME, "RearAxle")
        rod((s * 0.24, 0.30, 0.70), (0.0, 0.30, 0.70), 0.011, CHROME, "Bar")                          # handlebar halves
        rod((s * 0.24, 0.30, 0.70), (s * 0.30, 0.30, 0.70), 0.020, YELLOW if s > 0 else WHITE, "Grip")
    rod((0, 0.34, 0.60), (0, 0.30, 0.70), 0.013, RED, "Stem")
    rod((0, 0.33, 0.56), (0, -0.12, 0.30), 0.016, RED, "Frame")                                             # down tube to the seat post
    rod((0, -0.12, 0.30), (0, -0.22, 0.11), 0.016, RED, "Rear")
    rod((0, -0.12, 0.30), (0, -0.12, 0.42), 0.014, RED, "SeatPost")
    box((0, -0.12, 0.43), (0.22, 0.24, 0.035), YELLOW, "Seat")

    bpy.ops.object.select_all(action="DESELECT")
    for o in bpy.data.objects:
        o.select_set(o.name not in before)
    bpy.context.view_layer.objects.active = bpy.data.objects["FrontWheel"]
    bpy.ops.object.join()
    bpy.context.active_object.name = "Tricycle"
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
    cam.data.type = "ORTHO"; cam.data.ortho_scale = 1.3
    ps.PREVIEW.mkdir(exist_ok=True)
    for name, rot, loc in (("front", (math.pi / 2, 0, 0), (0, -3, 0.4)), ("side", (math.pi / 2, 0, math.pi / 2), (3, 0, 0.4)),
                           ("three_quarter", (math.radians(70), 0, math.radians(35)), (1.8, -2.2, 1.4))):
        cam.rotation_euler, cam.location = rot, loc
        sc.render.filepath = str(ps.PREVIEW / f"tricycle_{name}.png"); bpy.ops.render.render(write_still=True)
    # inventory icon: the same transparent diagonal-free render as the other items, three-quarter view
    sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = 64
    sc.render.image_settings.color_mode = "RGBA"; cam.data.ortho_scale = 1.15
    look = Vector((0, 0.1, 0.3)); cam.location = look + Vector((1.8, -2.2, 1.4)).normalized() * 6
    cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
    sc.render.filepath = str(ICON); bpy.ops.render.render(write_still=True)
    print("exported", XFILE)


if __name__ == "__main__":
    main()
