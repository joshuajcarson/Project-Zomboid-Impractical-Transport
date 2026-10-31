"""Minimal reader for Project Zomboid's text DirectX .X files (player body + Bob animations), plus a Blender importer.
Used for local previews only: it reads the game's own files from the install, nothing from the game is committed.
Run inside Blender (needs bpy/mathutils); parse_x() alone is plain Python."""
import math
import re

TOKEN = re.compile(r'"[^"]*"|[{}]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?|[A-Za-z_][\w.]*')


def _retype(text):
    toks = []
    for t in TOKEN.findall(re.sub(r"//[^\n]*|#[^\n]*", "", text)):
        if t[0] == '"':
            toks.append(("s", t[1:-1]))
        elif t in "{}":
            toks.append((t, t))
        elif t[0].isalpha() or t[0] == "_":
            toks.append(("i", t))
        else:
            toks.append(("n", float(t)))
    return toks


class Block:
    def __init__(self, kind, name):
        self.kind, self.name, self.nums, self.strs, self.kids = kind, name, [], [], []

    def find(self, kind):
        return [k for k in self.kids if k.kind == kind]


def _parse_block(toks, i):
    idents = []
    while toks[i][0] == "i":
        idents.append(toks[i][1]); i += 1
    assert toks[i][0] == "{", f"expected {{ near token {i}: {toks[i-3:i+2]}"
    i += 1
    b = Block(idents[0] if idents else None, idents[1] if len(idents) > 1 else None)
    while toks[i][0] != "}":
        k, v = toks[i]
        if k == "n":
            b.nums.append(v); i += 1
        elif k == "s":
            b.strs.append(v); i += 1
        elif k == "{":                       # reference such as { Bip01 }
            j = i + 1
            ref = Block("ref", None)
            while toks[j][0] != "}":
                ref.strs.append(toks[j][1]); j += 1
            b.kids.append(ref); i = j + 1
        else:
            kid, i = _parse_block(toks, i)
            b.kids.append(kid)
    return b, i + 1


def parse_x(path):
    toks = _retype(open(path, encoding="latin-1").read())
    root, i = Block("root", None), 0
    while i < len(toks):
        if toks[i][0] != "i":
            i += 1; continue
        # skip "xof 0303txt 0032"-style header words and template definitions up to the next block
        if toks[i][1] == "template":
            depth, i = 0, i + 1
            while not (toks[i][0] == "{"): i += 1
            while True:
                if toks[i][0] == "{": depth += 1
                if toks[i][0] == "}":
                    depth -= 1
                    if depth == 0: i += 1; break
                i += 1
            continue
        if toks[i][1] == "xof" or (i + 1 < len(toks) and toks[i + 1][0] == "n" and toks[i][1] == "xof"):
            i += 1; continue
        j = i
        while j < len(toks) and toks[j][0] == "i": j += 1
        if j < len(toks) and toks[j][0] == "{":
            kid, i = _parse_block(toks, i)
            root.kids.append(kid)
        else:
            i = j + 1 if j == i else j
    return root


# ---------------------------------------------------------------- Blender side
def _mat(nums):
    from mathutils import Matrix
    return Matrix([nums[0:4], nums[4:8], nums[8:12], nums[12:16]]).transposed()   # .X is row-vector, Blender column-vector


def collect_frames(root):
    """-> list of (name, parent_name, local_matrix) in file order, and the Mesh blocks with their frame name."""
    frames, meshes = [], []

    def walk(f, parent):
        tm = f.find("FrameTransformMatrix")
        from mathutils import Matrix
        frames.append((f.name, parent, _mat(tm[0].nums) if tm else Matrix.Identity(4)))
        for m in f.find("Mesh"):
            meshes.append((f.name, m))
        for c in f.find("Frame"):
            walk(c, f.name)

    for f in root.find("Frame"):
        walk(f, None)
    return frames, meshes


def import_body(path, collection=None):
    """Import a skinned .X body: returns (armature object, mesh object(s), {bone: rest_local})."""
    import bpy
    from mathutils import Matrix, Vector
    root = parse_x(path)
    frames, meshes = collect_frames(root)
    mesh_frames = {n for n, _ in meshes}
    by_name = {n: (p, m) for n, p, m in frames}
    world = {}

    def w(n):
        if n not in world:
            p, m = by_name[n]
            world[n] = m if p is None else w(p) @ m
        return world[n]

    arm_data = bpy.data.armatures.new("Survivor")
    arm = bpy.data.objects.new("Survivor", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    bones = [n for n, _, _ in frames if n not in mesh_frames]
    for n in bones:
        mw = w(n)
        eb = arm_data.edit_bones.new(n)
        eb.head = mw.translation
        eb.tail = mw.translation + mw.to_quaternion().to_matrix() @ Vector((0, 0.04, 0))
        eb.matrix = Matrix.Translation(mw.translation) @ mw.to_quaternion().to_matrix().to_4x4()
        eb.length = 0.04
    for n in bones:
        p = by_name[n][0]
        if p is not None and p in arm_data.edit_bones:
            arm_data.edit_bones[n].parent = arm_data.edit_bones[p]
    # bones point along their local Y toward their first child: give them the real segment length (IK needs it)
    for n in bones:
        kids = [k for k in bones if by_name[k][0] == n]
        if kids:
            d = (arm_data.edit_bones[kids[0]].head - arm_data.edit_bones[n].head).length
            if d > 1e-4: arm_data.edit_bones[n].length = d
    bpy.ops.object.mode_set(mode="OBJECT")

    mesh_objs = []
    for fname, mb in meshes:
        nv = int(mb.nums[0]); p = 1 + nv * 3
        verts = [tuple(mb.nums[1 + 3 * k:4 + 3 * k]) for k in range(nv)]
        nf = int(mb.nums[p]); p += 1
        faces = []
        for _ in range(nf):
            c = int(mb.nums[p]); faces.append(tuple(int(x) for x in mb.nums[p + 1:p + 1 + c])); p += 1 + c
        mesh = bpy.data.meshes.new(mb.name or "Body")
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        uvb = mb.find("MeshTextureCoords")
        if uvb:
            u = uvb[0].nums; uv = mesh.uv_layers.new(name="UV")
            for poly in mesh.polygons:
                for li, vi in zip(poly.loop_indices, poly.vertices):
                    uv.data[li].uv = (u[1 + 2 * vi], 1 - u[2 + 2 * vi])
        ob = bpy.data.objects.new(mb.name or "Body", mesh)
        bpy.context.scene.collection.objects.link(ob)
        for sw in mb.find("SkinWeights"):
            bone, n = sw.strs[0], int(sw.nums[0])
            if bone not in arm_data.bones: continue
            vg = ob.vertex_groups.new(name=bone)
            for k in range(n):
                vg.add([int(sw.nums[1 + k])], sw.nums[1 + n + k], "REPLACE")
        mod = ob.modifiers.new("Armature", "ARMATURE"); mod.object = arm
        ob.parent = arm
        mesh_objs.append(ob)
    arm.rotation_euler = (math.pi / 2, 0, 0)       # the game's skeleton is Y-up; Blender scenes are Z-up
    rest_local = {n: (w(by_name[n][0]).inverted() @ w(n) if by_name[n][0] else w(n)) for n in bones}
    return arm, mesh_objs, rest_local, {n: w(n) for n in bones}


def import_animation(path, arm, rest_local, name=None, fps=30):
    """Key the first AnimationSet of a Bob_*.X onto the armature. Returns (action, frame_count)."""
    import bpy
    from mathutils import Matrix, Quaternion, Vector
    root = parse_x(path)
    tps = 4800.0
    for b in root.kids:
        if b.kind == "AnimTicksPerSecond" and b.nums: tps = b.nums[0]
    aset = root.find("AnimationSet")[0]
    act = bpy.data.actions.new(name or aset.name)
    arm.animation_data_create(); arm.animation_data.action = act
    last = 0
    for an in aset.find("Animation"):
        ref = an.find("ref")
        if not ref or ref[0].strs[0] not in arm.pose.bones: continue
        bone = ref[0].strs[0]
        tracks = {}
        for key in an.find("AnimationKey"):
            t, nk, p = int(key.nums[0]), int(key.nums[1]), 2
            lst = []
            for _ in range(nk):
                tm, nvals = key.nums[p], int(key.nums[p + 1])
                lst.append((tm, key.nums[p + 2:p + 2 + nvals])); p += 2 + nvals
            tracks[t] = lst
        times = sorted({tm for lst in tracks.values() for tm, _ in lst})
        rl = rest_local[bone].inverted()

        def at(lst, tm, default, blend):
            if not lst: return default
            prev = max((k for k in lst if k[0] <= tm), key=lambda k: k[0], default=lst[0])
            nxt = min((k for k in lst if k[0] >= tm), key=lambda k: k[0], default=lst[-1])
            if nxt[0] == prev[0]: return prev[1]
            f = (tm - prev[0]) / (nxt[0] - prev[0])
            return blend(prev[1], nxt[1], f)

        pb = arm.pose.bones[bone]
        pb.rotation_mode = "QUATERNION"
        for tm in times:
            if 4 in tracks:
                local = _mat(at(tracks[4], tm, [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1], lambda a, b, f: [x + (y - x) * f for x, y in zip(a, b)]))
            else:
                q = at(tracks.get(0), tm, (1, 0, 0, 0), lambda a, b, f: tuple(Quaternion(a).slerp(Quaternion(b), f))) if 0 in tracks else (1, 0, 0, 0)
                tr = at(tracks.get(2), tm, None, lambda a, b, f: [x + (y - x) * f for x, y in zip(a, b)]) if 2 in tracks else None
                # .X rotation keys are conjugated relative to Blender's convention
                qq = Quaternion((q[0], -q[1], -q[2], -q[3]))
                local = qq.to_matrix().to_4x4()
                local.translation = Vector(tr) if tr else rest_local[bone].translation
            basis = rl @ local
            loc, rot, sc = basis.decompose()
            fr = 1 + tm / tps * fps
            pb.location, pb.rotation_quaternion = loc, rot
            pb.keyframe_insert("location", frame=fr); pb.keyframe_insert("rotation_quaternion", frame=fr)
            last = max(last, fr)
    return act, int(last)
