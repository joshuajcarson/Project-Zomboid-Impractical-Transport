"""Writes survivor animation clips as text DirectX .X files the game loads (shared by the transport clip scripts).
  write_clip, blend = clipio.make(order, out_dir)      order = the skeleton's bone names, parents before children
  write_clip(name, samples, nframes, travel)           samples = {frame: {bone: bone-local Matrix}}; travel = Translation_Data distance per clip, or a list of (frame, distance) keys
The clip carries the whole skeleton (a Frame tree), a one-triangle mesh naming every skinned bone, and keys for every bone: the game builds its
skeleton from those (see tools/blender/pogo_hop.py history for why)."""
import pathlib, sys
from mathutils import Matrix
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import zomboid_x as zx
import pogo_stick

GAME = pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media")
FPS = 30
TPS = 4800                      # ticks per second the game's clips use


def make(order, out_dir):
    # --- write the .X clip
    def fmt(vals): return ",".join(f"{v:.6f}" for v in vals)

    def key_block(kind, rows):
        lines = [f"  AnimationKey {kind} {{", f"   {'1' if kind == 'S' else '0' if kind == 'R' else '2'};", f"   {len(rows)};"]
        for i, (tick, vals) in enumerate(rows):
            lines.append(f"   {tick};{len(vals)};{fmt(vals)};;{',' if i < len(rows) - 1 else ';'}")
        lines.append("  }")
        return "\n".join(lines)

    tick = lambda fr: int(fr / FPS * TPS)
    def clip_body(samples, nframes, travel):
      end_tick = tick(nframes)
      body = []
      for n in order:
        if n == "Translation_Data":
            # forward travel along its local axis (same rotation key and direction as the game's Bob_Walk clip)
            # travel: one distance (linear) or a list of (frame, distance) keys (a clip that speeds up or slows down)
            keys = travel if isinstance(travel, (list, tuple)) else [(0, 0.0), (nframes, travel)]
            rot, trans = [(0, [-0.5, -0.5, 0.5, 0.5]), (end_tick, [-0.5, -0.5, 0.5, 0.5])], [(tick(fr), [0.0, 0.0, -d]) for fr, d in keys]
        else:
            frames = sorted(samples)
            rot, trans = [], []
            prev = None
            for fr in frames:
                m = samples[fr][n]
                q = m.to_quaternion()
                if prev is not None and q.dot(prev) < 0: q.negate()        # stay in one hemisphere so keys interpolate the short way
                prev = q.copy()
                rot.append((tick(fr), [q.w, -q.x, -q.y, -q.z]))        # .X rotation keys are conjugated relative to Blender's
                trans.append((tick(fr), list(m.translation)))
        body.append(f" Animation {{\n  {{ {n} }}\n{key_block('S', [(0, [1, 1, 1]), (end_tick, [1, 1, 1])])}\n{key_block('R', rot)}\n{key_block('T', trans)}\n }}")
      return body

    TEMPLATES = pogo_stick.X_TEMPLATES + """template Animation { <3d82ab4f-62da-11cf-ab39-0020af71e433> [...] }
template AnimationSet { <3d82ab50-62da-11cf-ab39-0020af71e433> [Animation <3d82ab4f-62da-11cf-ab39-0020af71e433>] }
template FloatKeys { <10dd46a9-775b-11cf-8f52-0040333594a3> DWORD nValues; array FLOAT values[nValues]; }
template TimedFloatKeys { <f406b180-7b3b-11cf-8f52-0040333594a3> DWORD time; FloatKeys tfkeys; }
template AnimationKey { <10dd46a8-775b-11cf-8f52-0040333594a3> DWORD keyType; DWORD nKeys; array TimedFloatKeys keys[nKeys]; }
template AnimTicksPerSecond { <9e415a43-7ba6-4a73-8743-b73d47e88476> DWORD AnimTicksPerSecond; }
template Frame { <3d82ab46-62da-11cf-ab39-0020af71e433> [...] }
template Matrix4x4 { <f6f23f45-7686-11cf-8f52-0040333594a3> array FLOAT matrix[16]; }
template FrameTransformMatrix { <f6f23f41-7686-11cf-8f52-0040333594a3> Matrix4x4 frameMatrix; }
template XSkinMeshHeader { <3cf169ce-ff7c-44ab-93c0-f78f62d172e2> WORD nMaxSkinWeightsPerVertex; WORD nMaxSkinWeightsPerFace; WORD nBones; }
template SkinWeights { <6f0d123b-bad2-4167-a0d0-80224f25fabb> STRING transformNodeName; DWORD nWeights; array DWORD vertexIndices[nWeights]; array FLOAT weights[nWeights]; Matrix4x4 matrixOffset; }
"""

    # The game loads clips with Assimp, which needs the skeleton (a Frame tree) in the file: the animation channels bind to frames by name.
    src_frames, _ = zx.collect_frames(zx.parse_x(GAME / "models_X/Skinned/MaleBody.x"))
    kids = {}
    for fname, fparent, flocal in src_frames: kids.setdefault(fparent, []).append((fname, flocal))

    # Assimp wants a mesh with a material, and the game builds the clip's skeleton from the mesh's SkinWeights blocks (without them
    # ProcessedAiScene.applyToAnimation hits a null skeleton and the server aborts). Vanilla clips carry the whole body; this one carries
    # a single triangle that names every skinned bone with the same bind offsets as the body, so no vertex data is copied.
    MATERIAL = "Material Pogo {\n1.0;1.0;1.0;1.0;;\n0.0;\n0.0;0.0;0.0;;\n0.0;0.0;0.0;;\n}\n"
    skin_blocks = []
    for _name, _mesh in [(n, m) for n, m in zx.collect_frames(zx.parse_x(GAME / "models_X/Skinned/MaleBody.x"))[1]]:
        for _sw in _mesh.find("SkinWeights"):
            _n = int(_sw.nums[0])
            if _n > 0:
                _offset = ",".join(f"{v:.6f}" for v in _sw.nums[1 + 2 * _n:1 + 2 * _n + 16])
                skin_blocks.append((_sw.strs[0], _offset))
    SKIN = ("XSkinMeshHeader {\n4;\n12;\n" + str(len(skin_blocks)) + ";\n}\n" + "".join(
        f'SkinWeights {{\n"{b}";\n1;\n{i % 3};\n1.000000;\n{off};;\n}}\n' for i, (b, off) in enumerate(skin_blocks)))
    BODY_MESH = ("Mesh Body {\n3;\n0.0;0.0;0.0;,\n0.01;0.0;0.0;,\n0.0;0.01;0.0;;\n1;\n3;0,1,2;;\n"
                 "MeshMaterialList {\n1;\n1;\n0;;\n{ Pogo }\n}\n" + SKIN + "}\n")

    def frame_text(name, local, depth=0):
        pad = " " * depth
        m = local.transposed()                                   # .X is row-vector: translation in the last row
        flat = ",".join(f"{m[r][c]:.6f}" for r in range(4) for c in range(4))
        inner = "".join(frame_text(n, l, depth + 1) for n, l in kids.get(name, [])) + (BODY_MESH if name == "Body" else "")
        return (f"{pad}Frame {name} {{\n{pad} FrameTransformMatrix {{\n{pad}  {flat};;\n{pad} }}\n"
                f"{inner}{pad}}}\n")

    SKELETON = "".join(frame_text(n, l) for n, l in kids.get(None, []))
    TICKS = "AnimTicksPerSecond {\n 4800;\n}\n"
    out_dir.mkdir(parents=True, exist_ok=True)
    def write_clip(name, samples, nframes, travel):
        out = out_dir / f"{name}.X"
        out.write_text(TEMPLATES + MATERIAL + SKELETON + TICKS + f"AnimationSet {name} {{\n" + "\n".join(clip_body(samples, nframes, travel)) + "\n}\n", encoding="latin-1", newline="\n")
        print("wrote", out, "bones", len(order), "keys", len(samples))

    def blend(a, b, w):
        out = {}
        for n in order:
            q = a[n].to_quaternion().slerp(b[n].to_quaternion(), w)
            out[n] = Matrix.Translation(a[n].translation.lerp(b[n].translation, w)) @ q.to_matrix().to_4x4()
        return out

    return write_clip, blend
