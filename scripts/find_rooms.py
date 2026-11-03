"""List rooms by name substring from the game's .lotheader files: find_rooms.py <map folder> <substring>..."""
import pathlib, re, struct, sys

def rooms(path):
    d = path.read_bytes()
    assert d[:4] == b"LOTH", path
    p = 4
    ver, n = struct.unpack_from("<ii", d, p); p += 8
    for _ in range(n):
        p = d.index(b"\n", p) + 1
    p += 12  # chunk size 8, 8, 0
    lv, cnt = struct.unpack_from("<ii", d, p); p += 8
    for _ in range(cnt):
        e = d.index(b"\n", p); name = d[p:e].decode(); p = e + 1
        lvl, rc = struct.unpack_from("<ii", d, p); p += 8
        rs = [struct.unpack_from("<iiii", d, p + 16 * i) for i in range(rc)]; p += 16 * rc
        oc, = struct.unpack_from("<i", d, p); p += 4 + 12 * oc
        yield name, lvl, rs

if __name__ == "__main__":
    folder, *subs = sys.argv[1:]
    for f in sorted(pathlib.Path(folder).glob("*.lotheader")):
        cx, cy = map(int, re.findall(r"\d+", f.stem))
        for name, lvl, rs in rooms(f):
            if any(s in name.lower() for s in subs):
                x, y, w, h = rs[0]
                print(f"{name:24} z{lvl} x={cx*256+x} y={cy*256+y} {w}x{h} ({len(rs)} rects) {f.name}")
