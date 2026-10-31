"""Build the pogo hop animation for the game's survivor and write it as a text DirectX .X clip.
  blender -b -P tools/blender/pogo_hop.py            writes media/anims_X/Bob/Bob_PogoHop.X and previews/pogo_hop_*.png
The clip keys every bone of the player skeleton: pelvis lift for the bounce, knees and elbows from a two-bone solver so the
feet stay on the pads and the hands on the grips. Translation_Data carries the forward travel per hop, which is what moves the
character in game (speed = DISTANCE / DURATION x the anim node's speed scale). Preview only reads the game's own body model."""
import bpy, sys, math, pathlib
from mathutils import Vector, Matrix
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import zomboid_x as zx
import pogo_stick

GAME = pathlib.Path(r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media")
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT_X = ROOT / "Contents/mods/ImpracticalTransport/42/media/anims_X/Bob/Bob_PogoHop.X"
PREVIEW = ROOT / "previews"; PREVIEW.mkdir(exist_ok=True)

FPS, FRAMES = 30, 24            # one hop = 0.8 s
TPS = 4800                      # ticks per second the game's clips use
DISTANCE = 0.44                 # Translation_Data travel per hop. Measured in game: 0.64 gave 1.17 tiles/s (79% of walking), so 0.44 aims for ~0.8 tiles/s
s = pogo_stick.GAME_UNITS_PER_METRE   # stick scale, so grips and pads land where the model puts them

bpy.ops.wm.read_factory_settings(use_empty=True)
arm, meshes, _, _ = zx.import_body(GAME / "models_X/Skinned/MaleBody.x")
bpy.context.view_layer.update()
pb = arm.pose.bones
for p in pb: p.rotation_mode = "QUATERNION"
rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
order = [b.name for b in arm.data.bones]          # parents come before children
Mi = arm.matrix_world.inverted()
wrest = lambda n: arm.matrix_world @ rest[n].translation
up = Vector((0, 0, 1))
fwd = wrest("Bip01_L_Toe0") - wrest("Bip01_L_Foot"); fwd.z = 0; fwd.normalize()
side = up.cross(fwd)
if (wrest("Bip01_L_Hand") - wrest("Bip01_R_Hand")).dot(side) < 0: side = -side     # side = rider's left
dist = lambda a, b: (rest[a].translation - rest[b].translation).length
Larm = dist("Bip01_L_UpperArm", "Bip01_L_Forearm") + dist("Bip01_L_Forearm", "Bip01_L_Hand")
hip_z = wrest("Bip01_L_Thigh").z
sh_off = wrest("Bip01_L_UpperArm").z - hip_z
ankle = wrest("Bip01_L_Foot").z
grip_z, pad_z = 0.92 * s, 0.3 * s
base_lift = (grip_z + 0.8 * Larm - sh_off) - hip_z     # hands hang 0.8 of an arm length below the shoulders at the grips (nearly straight arms, knees moderately bent)

# --- two-bone solver (armature space), same method as pogo_rider.py
def aim(name, child, new_dir, head):
    """Pose bone `name` so the direction to its child bone becomes new_dir, head at `head` (armature space); returns the swing.
    Bone axes in this skeleton are arbitrary (the limb is not along Y), so the limb direction is read from the bind pose."""
    rm = rest[name].to_3x3()
    along = (rm.inverted() @ (rest[child].translation - rest[name].translation)).normalized()
    q = (rm @ along).rotation_difference(new_dir)
    pb[name].matrix = Matrix.Translation(head) @ (q.to_matrix() @ rm).to_4x4()
    bpy.context.view_layer.update()
    return q

def limb(root, mid, end, target_world, pole_world, foot):
    T, pole = Mi @ target_world, Mi.to_3x3() @ pole_world
    Mp, Ep = rest[mid].translation, rest[end].translation
    Hp = pb[root].matrix.translation        # the hip/shoulder after the pelvis lift
    L1, L2 = (Mp - rest[root].translation).length, (Ep - Mp).length
    d = min(max((T - Hp).length, 0.05), (L1 + L2) * 0.995)
    u = (T - Hp).normalized(); T = Hp + u * d
    a = (L1 * L1 - L2 * L2 + d * d) / (2 * d); h = math.sqrt(max(L1 * L1 - a * a, 0))
    pp = (pole - pole.dot(u) * u).normalized()
    E = Hp + u * a + pp * h
    aim(root, mid, (E - Hp).normalized(), Hp)
    q2 = aim(mid, end, (T - E).normalized(), E)
    rm = rest[end].to_3x3()
    pb[end].matrix = Matrix.Translation(T) @ ((rm if foot else q2.to_matrix() @ rm)).to_4x4()
    bpy.context.view_layer.update()

# (frame, stick lift, body sink relative to the stick): crouch, push off, airborne, descend, land
KEYS = [(0, 0.0, 0.01), (4, 0.0, 0.045), (8, 0.012, -0.012), (12, 0.075, 0.0), (18, 0.02, 0.01), (21, 0.0, 0.03), (24, 0.0, 0.01)]

def pose(stick_lift, sink):
    for p in pb: p.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    lift = base_lift + stick_lift - sink
    pb["Bip01"].matrix = Matrix.Translation(Mi.to_3x3() @ (up * lift)) @ rest["Bip01"]
    bpy.context.view_layer.update()
    for pre, sgn in (("L_", 1), ("R_", -1)):
        foot_t = side * sgn * 0.17 * s + up * (pad_z + ankle + stick_lift)
        hand_t = side * sgn * 0.14 * s + up * (grip_z + stick_lift) + fwd * 0.0
        limb(f"Bip01_{pre}Thigh", f"Bip01_{pre}Calf", f"Bip01_{pre}Foot", foot_t, fwd + side * sgn * 0.15, True)
        limb(f"Bip01_{pre}UpperArm", f"Bip01_{pre}Forearm", f"Bip01_{pre}Hand", hand_t, -fwd * 0.5 + side * sgn * 0.3 - up * 0.8, False)
    local = {}
    for n in order:
        parent = pb[n].parent
        local[n] = (parent.matrix.inverted() @ pb[n].matrix) if parent else pb[n].matrix.copy()
    return local

samples = {fr: pose(lift, sink) for fr, lift, sink in KEYS}

# --- write the .X clip
def fmt(vals): return ",".join(f"{v:.6f}" for v in vals)

def key_block(kind, rows):
    lines = [f"  AnimationKey {kind} {{", f"   {'1' if kind == 'S' else '0' if kind == 'R' else '2'};", f"   {len(rows)};"]
    for i, (tick, vals) in enumerate(rows):
        lines.append(f"   {tick};{len(vals)};{fmt(vals)};;{',' if i < len(rows) - 1 else ';'}")
    lines.append("  }")
    return "\n".join(lines)

end_tick = int(FRAMES / FPS * TPS)
tick = lambda fr: int(fr / FPS * TPS)
body = []
for n in order:
    if n == "Translation_Data":
        # forward travel along its local axis (same rotation key and direction as the game's Bob_Walk clip)
        rot, trans = [(0, [-0.5, -0.5, 0.5, 0.5]), (end_tick, [-0.5, -0.5, 0.5, 0.5])], [(0, [0.0, 0.0, 0.0]), (end_tick, [0.0, 0.0, -DISTANCE])]
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
OUT_X.parent.mkdir(parents=True, exist_ok=True)
OUT_X.write_text(TEMPLATES + MATERIAL + SKELETON + TICKS + "AnimationSet Bob_PogoHop {\n" + "\n".join(body) + "\n}\n", encoding="latin-1", newline="\n")
print("wrote", OUT_X, "bones", len(order), "keys", len(KEYS))

# --- round-trip: read the clip back with the game-format reader and render frames to check the motion
bpy.ops.wm.read_factory_settings(use_empty=True)
arm, meshes, rl, _ = zx.import_body(GAME / "models_X/Skinned/MaleBody.x")
act, last = zx.import_animation(OUT_X, arm, rl, "Bob_PogoHop", fps=FPS)
body_mat = bpy.data.materials.new("Survivor"); body_mat.diffuse_color = (0.35, 0.45, 0.6, 1)
for m in meshes: m.data.materials.append(body_mat)
sc = bpy.context.scene
sc.render.engine = "BLENDER_WORKBENCH"; sc.render.resolution_x = sc.render.resolution_y = 520
sc.display.shading.color_type = "MATERIAL"; sc.world = bpy.data.worlds.new("w"); sc.world.color = (0.85, 0.85, 0.9)
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 1.5
look = Vector((0, 0, 0.55))
import os
cam.location = (fwd * 6 if os.environ.get('VIEW') == 'front' else fwd.cross(up) * 6) + look
cam.rotation_euler = (look - cam.location).to_track_quat("-Z", "Y").to_euler()
for name, fr in (("crouch", 5), ("apex", 13), ("land", 22)):
    sc.frame_set(fr); sc.render.filepath = str(PREVIEW / f"pogo_hop_{os.environ.get('VIEW', 'side')}_{name}.png"); bpy.ops.render.render(write_still=True)
