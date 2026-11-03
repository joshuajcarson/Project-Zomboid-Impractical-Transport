"""Builds the stilts as a SKINNED clothing model (the same layout as skates_model.py): for each leg a wooden pole that hangs RAISE below a foot rest, a strut up the
outside of the lower leg and two straps round the calf. Foot rest, pole and lower strut are weighted to the foot bone, the upper strut and straps to the calf bone.
Writes media/models_X/ImpracticalTransport/Stilts.X, its palette texture and the inventory icon.
  blender -b -P tools/blender/stilts_model.py
The geometry is placed from the survivor's own foot and calf vertices (MaleBody.x, mesh space: x sideways, y up, z forward). RAISE must equal RAISE in
tools/blender/stilts_gait.py: the clips lift the whole rider by it, and the engine does not change the character's real height."""
import bpy, math, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import zomboid_x as zx
import pogo_stick as ps

GAME = pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media")
ROOT = pathlib.Path(__file__).resolve().parents[2]
MEDIA = ROOT / "Contents/mods/ImpracticalTransport/42/media"
XFILE = MEDIA / "models_X/ImpracticalTransport/Stilts.X"
TEXTURE = MEDIA / "textures/ImpracticalTransport/Stilts_texture.png"
ICON = MEDIA / "textures/Item_Stilts.png"
RAISE = 0.35                                    # how far the pole tips hang below the sole (mesh units; 1 unit is about 2 m): the clips lift the rider by this much
COLOURS = [(0.55, 0.33, 0.14), (0.80, 0.10, 0.12), (0.05, 0.05, 0.05), (0.60, 0.60, 0.65)]   # wood, strap, rubber tip, metal bolt
BONES = ("Bip01_L_Foot", "Bip01_R_Foot", "Bip01_L_Calf", "Bip01_R_Calf")

root = zx.parse_x(GAME / "models_X/Skinned/MaleBody.x")
frames, meshes = zx.collect_frames(root)
body = meshes[0][1]
nv = int(body.nums[0]); V = [tuple(body.nums[1 + 3 * i:4 + 3 * i]) for i in range(nv)]
part = {}
for sw in body.find("SkinWeights"):
    if sw.strs[0] in BONES:
        n = int(sw.nums[0]); idx = [int(i) for i in sw.nums[1:1 + n]]; w = sw.nums[1 + n:1 + 2 * n]
        pts = [V[i] for i, wt in zip(idx, w) if wt > 0.5]
        part[sw.strs[0]] = dict(box=[(min(p[a] for p in pts), max(p[a] for p in pts)) for a in range(3)], offset=sw.nums[1 + 2 * n:1 + 2 * n + 16])

def box(lo, hi, m):
    x0, y0, z0 = lo; x1, y1, z1 = hi
    c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (3, 7, 6, 2), (0, 4, 7, 3), (1, 2, 6, 5)]      # outward facing (the winding the game's static export uses)
    return [([c[a], c[b], c[d]], m) for q in quads for a, b, d in ((q[0], q[1], q[2]), (q[0], q[2], q[3]))]

def stilt(side):
    """Triangles per bone for one leg; side is 'L' or 'R'."""
    (fx0, fx1), (fy0, fy1), (fz0, fz1) = part[f"Bip01_{side}_Foot"]["box"]
    (cx0, cx1), (cy0, cy1), (cz0, cz1) = part[f"Bip01_{side}_Calf"]["box"]
    cx = (fx0 + fx1) / 2; cz = (fz0 + fz1) / 2
    outer = 1 if cx > 0 else -1                                            # which way is away from the body's midline
    ox = (cx1 + 0.010) if outer > 0 else (cx0 - 0.010)                      # x of the strut's centre line, just outside the calf
    sz = (cz0 + cz1) / 2
    foot, calf = [], []
    foot += box((fx0 - 0.010, fy0 - 0.014, fz0 - 0.010), (fx1 + 0.010, fy0 + 0.002, fz1 + 0.010), 0)      # foot rest plate under the shoe
    foot += box((cx - 0.016, fy0 - RAISE, cz - 0.016), (cx + 0.016, fy0 - 0.014, cz + 0.016), 0)           # the pole
    foot += box((cx - 0.020, fy0 - RAISE, cz - 0.020), (cx + 0.020, fy0 - RAISE + 0.035, cz + 0.020), 2)  # rubber tip
    foot += box((min(ox, cx) - 0.008, fy0 - 0.014, sz - 0.008), (max(ox, cx) + 0.008, fy0 - 0.002, sz + 0.008), 0)   # arm joining the plate to the strut
    foot += box((ox - 0.008, fy0 - 0.014, sz - 0.008), (ox + 0.008, cy0, sz + 0.008), 0)                   # lower strut, up to the calf
    calf += box((ox - 0.008, cy0, sz - 0.008), (ox + 0.008, cy1 - 0.01, sz + 0.008), 0)                    # upper strut
    for t in (0.25, 0.75):                                                                                 # two straps round the calf
        y = cy0 + (cy1 - cy0) * t
        calf += box((cx0 - 0.010, y - 0.012, cz0 - 0.010), (cx1 + 0.010, y + 0.012, cz1 + 0.010), 1)
    return {f"Bip01_{side}_Foot": foot, f"Bip01_{side}_Calf": calf}

meshes_out = {}
for side in ("L", "R"): meshes_out.update(stilt(side))
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
skin = f"XSkinMeshHeader {{\n1;\n3;\n{len(BONES)};\n}}\n"
for bone in BONES:
    idx = [i for i, b in enumerate(bone_of) if b == bone]
    skin += f'SkinWeights {{\n"{bone}";\n{len(idx)};\n{",".join(map(str, idx))};\n{",".join("1.000000" for _ in idx)};\n{fmt(part[bone]["offset"])};;\n}}\n'
mesh = ("Mesh Stilts {\n" + f"{len(verts)};\n" + vec(verts) + f"{ntri};\n" + tri_text +
        "MeshNormals {\n" + f"{len(norms)};\n" + vec(norms) + f"{ntri};\n" + tri_text + "}\n" +
        "MeshTextureCoords {\n" + f"{len(uvs)};\n" + "".join(f"{u:.6f};{v:.6f};{end(i, len(uvs))}\n" for i, (u, v) in enumerate(uvs)) + "}\n" +
        f"MeshMaterialList {{\n1;\n{ntri};\n" + ",".join("0" for _ in range(ntri)) + ";;\n{ StiltsMaterial }\n}\n" + skin + "}\n")

kids = {}
for fname, fparent, flocal in frames: kids.setdefault(fparent, []).append((fname, flocal))
root_name = kids[None][0][0]
def frame_text(name, local, depth=0):
    pad = " " * depth
    m = local.transposed()
    flat = ",".join(f"{m[r][c]:.6f}" for r in range(4) for c in range(4))
    inner = "".join(frame_text(n, l, depth + 1) for n, l in kids.get(name, [])) + (mesh if name == root_name else "")
    return f"{pad}Frame {name} {{\n{pad} FrameTransformMatrix {{\n{pad}  {flat};;\n{pad} }}\n{inner}{pad}}}\n"
material = 'Material StiltsMaterial {\n1.0;1.0;1.0;1.0;;\n0.0;\n0.0;0.0;0.0;;\n0.0;0.0;0.0;;\nTextureFilename { "Stilts_texture.png"; }\n}\n'
XFILE.parent.mkdir(parents=True, exist_ok=True)
XFILE.write_text(TEMPLATES + material + "".join(frame_text(n, l) for n, l in kids[None]), encoding="latin-1", newline="\n")
ps.write_palette(COLOURS, path=TEXTURE)

# inventory icon: 64x64, two tall poles with foot rests and straps, drawn pixel by pixel (the model is skinned to the survivor, so it cannot be rendered alone)
W = 64
px = [[0.0, 0.0, 0.0, 0.0] for _ in range(W * W)]
lin = lambda c: [v ** (1 / 2.2) for v in c] + [1.0]
def rect(x0, y0, x1, y1, c):      # y counts up from the bottom
    for y in range(y0, y1):
        for x in range(x0, x1): px[y * W + x] = lin(c)
for x0 in (16, 38):
    rect(x0 + 5, 4, x0 + 9, 54, COLOURS[0])          # pole
    rect(x0 + 5, 4, x0 + 9, 9, COLOURS[2])           # rubber tip
    rect(x0 - 1, 22, x0 + 17, 26, COLOURS[0])        # foot rest
    rect(x0 + 3, 44, x0 + 11, 48, COLOURS[1])        # strap
    rect(x0 + 3, 34, x0 + 11, 38, COLOURS[1])
img = bpy.data.images.new("StiltsIcon", W, W, alpha=True)
img.pixels = [v for p in px for v in p]
img.filepath_raw = str(ICON); img.file_format = "PNG"; img.save()
print("exported", XFILE, "triangles", ntri, {k: [tuple(round(x, 3) for x in r) for r in v["box"]] for k, v in part.items()})
