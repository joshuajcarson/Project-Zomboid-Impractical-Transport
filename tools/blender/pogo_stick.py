"""Build the pogo stick from primitives, export a game-ready .X model, render preview PNGs.
  blender -b -P tools/blender/pogo_stick.py
Meters, Z up, foot of the stick at z=0. Flat-colour materials only (the game gets a one-colour texture for now).
Layout (twin-rail pogo): rubber foot + steel tip, foot pads at the bottom of two side rails, a coil spring around a
centre rod, rails that flare in and then out to two grips."""
import bpy, math, pathlib
from mathutils import Vector

ROOT = pathlib.Path(__file__).resolve().parents[2]
XFILE = ROOT / "Contents/mods/ImpracticalTransport/42/media/models_X/ImpracticalTransport/PogoStick.X"
PREVIEW = ROOT / "previews"
GAME_UNITS_PER_METRE = 0.5   # the survivor is ~0.9 game units tall for a 1.8 m person (vanilla bat: 0.49 units for a 0.9 m bat)


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


X_TEMPLATES = """xof 0303txt 0032
template ColorRGBA { <35ff44e0-6c7c-11cf-8f52-0040333594a3> FLOAT red; FLOAT green; FLOAT blue; FLOAT alpha; }
template ColorRGB { <d3e16e81-7835-11cf-8f52-0040333594a3> FLOAT red; FLOAT green; FLOAT blue; }
template Material { <3d82ab4d-62da-11cf-ab39-0020af71e433> ColorRGBA faceColor; FLOAT power; ColorRGB specularColor; ColorRGB emissiveColor; [...] }
template TextureFilename { <a42790e1-7810-11cf-8f52-0040333594a3> STRING filename; }
template Vector { <3d82ab5e-62da-11cf-ab39-0020af71e433> FLOAT x; FLOAT y; FLOAT z; }
template MeshFace { <3d82ab5f-62da-11cf-ab39-0020af71e433> DWORD nFaceVertexIndices; array DWORD faceVertexIndices[nFaceVertexIndices]; }
template Mesh { <3d82ab44-62da-11cf-ab39-0020af71e433> DWORD nVertices; array Vector vertices[nVertices]; DWORD nFaces; array MeshFace faces[nFaces]; [...] }
template MeshNormals { <f6f23f43-7686-11cf-8f52-0040333594a3> DWORD nNormals; array Vector normals[nNormals]; DWORD nFaceNormals; array MeshFace faceNormals[nFaceNormals]; }
template MeshMaterialList { <f6f23f42-7686-11cf-8f52-0040333594a3> DWORD nMaterials; DWORD nFaceIndexes; array DWORD faceIndexes[nFaceIndexes]; [Material <3d82ab4d-62da-11cf-ab39-0020af71e433>] }
template Coords2d { <f6f23f44-7686-11cf-8f52-0040333594a3> FLOAT u; FLOAT v; }
template MeshTextureCoords { <f6f23f40-7686-11cf-8f52-0040333594a3> DWORD nTextureCoords; array Coords2d textureCoords[nTextureCoords]; }
"""


def export_x(obj, path, scale=GAME_UNITS_PER_METRE):
    """Static mesh as a text DirectX .X file in the game's units, Y up (the format vanilla item models use).
    Blender (x, y, z up) -> game (x, z, y): swapping two axes flips handedness, which is what DirectX expects."""
    import bmesh
    bm = bmesh.new(); bm.from_mesh(obj.data); bmesh.ops.triangulate(bm, faces=bm.faces[:])
    uv = bm.loops.layers.uv.active
    verts, uvs, norms = [], [], []
    for f in bm.faces:
        n = f.normal
        for l in f.loops:
            c = l.vert.co
            verts.append((c.x * scale, c.z * scale, c.y * scale))
            norms.append((n.x, n.z, n.y))
            uvs.append((l[uv].uv.x, 1 - l[uv].uv.y) if uv else (0.5, 0.5))
    nt = len(verts) // 3
    end = lambda i, n: "," if i < n - 1 else ";"
    tri = "".join(f"3;{3 * i},{3 * i + 1},{3 * i + 2};{end(i, nt)}\n" for i in range(nt))
    vec = lambda rows: "".join(f"{x:.6f};{y:.6f};{z:.6f};{end(i, len(rows))}\n" for i, (x, y, z) in enumerate(rows))
    out = [X_TEMPLATES, "Mesh PogoStick {\n", f"{len(verts)};\n", vec(verts), f"{nt};\n", tri,
           "MeshNormals {\n", f"{len(norms)};\n", vec(norms), f"{nt};\n", tri, "}\n",
           "MeshTextureCoords {\n", f"{len(uvs)};\n",
           "".join(f"{u:.6f};{v:.6f};{end(i, len(uvs))}\n" for i, (u, v) in enumerate(uvs)), "}\n",
           "MeshMaterialList {\n1;\n", f"{nt};\n", ",".join("0" for _ in range(nt)), ";;\n",
           "Material Pogo {\n1.0;1.0;1.0;1.0;;\n0.0;\n0.0;0.0;0.0;;\n0.0;0.0;0.0;;\n",
           'TextureFilename { "PogoStick_texture.png"; }\n}\n}\n}\n']
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(path).write_text("".join(out), encoding="latin-1", newline="\n")
    bm.free()


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    export_x(build(), XFILE)

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
    print("exported", XFILE)


if __name__ == "__main__":
    main()
