"""Builds the roller skates as a SKINNED clothing model: quad skates (a boot shell, a plate and four wheels) for each foot, weighted 100 percent to that foot's bone,
and writes media/models_X/ImpracticalTransport/RollerSkates.X (the survivor's skeleton frames plus one top-level Mesh with SkinWeights, the layout the game's
own clothing models use), its palette texture and the clothing item's inventory icon.
  blender -b -P tools/blender/skates_model.py
The geometry is placed from the survivor's own foot vertices (bounding boxes of the vertices weighted to each foot bone in MaleBody.x, mesh space: x sideways,
y up, z forward). The wheels hang RAISE below the sole, so the skating clips lift the rider by RAISE (tools/blender/skates_glide.py)."""
import bpy, math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import zomboid_x as zx
import pogo_stick as ps

GAME = pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media")
ROOT = pathlib.Path(__file__).resolve().parents[2]
MEDIA = ROOT / "Contents/mods/ImpracticalTransport/42/media"
XFILE = MEDIA / "models_X/ImpracticalTransport/RollerSkates.X"
TEXTURE = MEDIA / "textures/ImpracticalTransport/RollerSkates_texture.png"
ICON = MEDIA / "textures/Item_RollerSkates.png"
RAISE = 0.034                                   # how far the wheels hang below the sole (mesh units): the clips lift the rider by this much
COLOURS = [(0.80, 0.10, 0.12), (0.18, 0.18, 0.22), (0.95, 0.80, 0.10), (0.92, 0.92, 0.92), (0.05, 0.05, 0.05)]   # boot, plate, wheel, lace and toe, tyre

root = zx.parse_x(GAME / "models_X/Skinned/MaleBody.x")
frames, meshes = zx.collect_frames(root)
body = meshes[0][1]
nv = int(body.nums[0]); V = [tuple(body.nums[1 + 3 * i:4 + 3 * i]) for i in range(nv)]
foot = {}
for sw in body.find("SkinWeights"):
    if sw.strs[0] in ("Bip01_L_Foot", "Bip01_R_Foot"):
        n = int(sw.nums[0]); idx = [int(i) for i in sw.nums[1:1 + n]]; w = sw.nums[1 + n:1 + 2 * n]
        pts = [V[i] for i, wt in zip(idx, w) if wt > 0.5]
        foot[sw.strs[0]] = dict(box=[(min(p[a] for p in pts), max(p[a] for p in pts)) for a in range(3)], offset=sw.nums[1 + 2 * n:1 + 2 * n + 16])

# --- geometry: lists of (triangle vertices, material index); built per foot so each foot's vertices can be weighted to its bone
def box(lo, hi, m):
    x0, y0, z0 = lo; x1, y1, z1 = hi
    c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (3, 7, 6, 2), (0, 4, 7, 3), (1, 2, 6, 5)]      # outward facing (the winding the game's static export uses)
    return [([c[a], c[b], c[d]], m) for q in quads for a, b, d in ((q[0], q[1], q[2]), (q[0], q[2], q[3]))]

def wheel(cx, cy, cz, r, width, m, segments=10):
    """A cylinder whose axis is x."""
    tris = []
    ring = lambda x: [(x, cy + r * math.cos(2 * math.pi * k / segments), cz + r * math.sin(2 * math.pi * k / segments)) for k in range(segments)]
    a, b = ring(cx - width / 2), ring(cx + width / 2)
    for k in range(segments):
        k2 = (k + 1) % segments
        tris += [([a[k], b[k], b[k2]], m), ([a[k], b[k2], a[k2]], m)]
        tris += [([(cx - width / 2, cy, cz), a[k2], a[k]], m), ([(cx + width / 2, cy, cz), b[k], b[k2]], m)]
    return tris

def skate(box_):
    (x0, x1), (y0, y1), (z0, z1) = box_
    cx = (x0 + x1) / 2
    tris = []
    pad = 0.008
    tris += box((x0 - pad, y0 + 0.004, z0 - pad), (x1 + pad, y1 + 0.016, z1 + pad), 0)                 # boot shell around the shoe
    tris += box((x0 - pad, y0 + 0.004, z1 - 0.014), (x1 + pad, y0 + 0.030, z1 + pad + 0.004), 3)       # toe cap
    tris += box((cx - 0.030, y0 - RAISE * 0.45, z0 - 0.002), (cx + 0.030, y0 + 0.004, z1 + 0.004), 1)  # plate under the sole
    for z in (z0 + 0.030, z1 - 0.022):                                                                  # two axles, two wheels each (quad skates)
        for dx in (-0.019, 0.019):
            tris += wheel(cx + dx, y0 - RAISE * 0.45 + 0.002, z, RAISE * 0.55, 0.014, 2)
    return tris

meshes_out = {}
for bone in ("Bip01_L_Foot", "Bip01_R_Foot"):
    meshes_out[bone] = skate(foot[bone]["box"])
verts, norms, uvs, bone_of = [], [], [], []
for bone, tris in meshes_out.items():
    for tri, m in tris:
        a, b, c = tri
        n = ((b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1]), (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2]), (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))
        ln = math.sqrt(sum(x * x for x in n)) or 1.0
        for v in tri:
            verts.append(v); norms.append(tuple(x / ln for x in n)); uvs.append(((m + 0.5) / len(COLOURS), 0.5)); bone_of.append(bone)
ntri = len(verts) // 3
fmt = lambda vals: ",".join(f"{v:.6f}" for v in vals)
end = lambda i, n: "," if i < n - 1 else ";"
vec = lambda rows: "".join(f"{x:.6f};{y:.6f};{z:.6f};{end(i, len(rows))}\n" for i, (x, y, z) in enumerate(rows))
tri_text = "".join(f"3;{3 * i},{3 * i + 1},{3 * i + 2};{end(i, ntri)}\n" for i in range(ntri))

TEMPLATES = ps.X_TEMPLATES + """template Frame { <3d82ab46-62da-11cf-ab39-0020af71e433> [...] }
template Matrix4x4 { <f6f23f45-7686-11cf-8f52-0040333594a3> array FLOAT matrix[16]; }
template FrameTransformMatrix { <f6f23f41-7686-11cf-8f52-0040333594a3> Matrix4x4 frameMatrix; }
template XSkinMeshHeader { <3cf169ce-ff7c-44ab-93c0-f78f62d172e2> WORD nMaxSkinWeightsPerVertex; WORD nMaxSkinWeightsPerFace; WORD nBones; }
template SkinWeights { <6f0d123b-bad2-4167-a0d0-80224f25fabb> STRING transformNodeName; DWORD nWeights; array DWORD vertexIndices[nWeights]; array FLOAT weights[nWeights]; Matrix4x4 matrixOffset; }
"""
skin = "XSkinMeshHeader {\n1;\n3;\n2;\n}\n"
for bone in ("Bip01_L_Foot", "Bip01_R_Foot"):
    idx = [i for i, b in enumerate(bone_of) if b == bone]
    skin += f'SkinWeights {{\n"{bone}";\n{len(idx)};\n{",".join(map(str, idx))};\n{",".join("1.000000" for _ in idx)};\n{fmt(foot[bone]["offset"])};;\n}}\n'
mesh = ("Mesh RollerSkates {\n" + f"{len(verts)};\n" + vec(verts) + f"{ntri};\n" + tri_text +
        "MeshNormals {\n" + f"{len(norms)};\n" + vec(norms) + f"{ntri};\n" + tri_text + "}\n" +
        "MeshTextureCoords {\n" + f"{len(uvs)};\n" + "".join(f"{u:.6f};{v:.6f};{end(i, len(uvs))}\n" for i, (u, v) in enumerate(uvs)) + "}\n" +
        f"MeshMaterialList {{\n1;\n{ntri};\n" + ",".join("0" for _ in range(ntri)) + ";;\n{ RollerSkatesMaterial }\n}\n" + skin + "}\n")

kids = {}
for fname, fparent, flocal in frames: kids.setdefault(fparent, []).append((fname, flocal))
root_name = kids[None][0][0]
def frame_text(name, local, depth=0):
    pad = " " * depth
    m = local.transposed()
    flat = ",".join(f"{m[r][c]:.6f}" for r in range(4) for c in range(4))
    inner = "".join(frame_text(n, l, depth + 1) for n, l in kids.get(name, [])) + (mesh if name == root_name else "")
    return f"{pad}Frame {name} {{\n{pad} FrameTransformMatrix {{\n{pad}  {flat};;\n{pad} }}\n{inner}{pad}}}\n"
material = 'Material RollerSkatesMaterial {\n1.0;1.0;1.0;1.0;;\n0.0;\n0.0;0.0;0.0;;\n0.0;0.0;0.0;;\nTextureFilename { "RollerSkates_texture.png"; }\n}\n'
XFILE.parent.mkdir(parents=True, exist_ok=True)
XFILE.write_text(TEMPLATES + material + "".join(frame_text(n, l) for n, l in kids[None]), encoding="latin-1", newline="\n")
ps.write_palette(COLOURS, path=TEXTURE)
print("exported", XFILE, "triangles", ntri, "feet", {k: [tuple(round(x, 3) for x in r) for r in v["box"]] for k, v in foot.items()})
