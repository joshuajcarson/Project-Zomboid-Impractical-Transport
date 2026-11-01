"""Screenshots of the running game (left open by `smoke_test.py play --keep`), no human needed.
The game window paints white while other windows cover it, so this raises it to the front (topmost), grabs its client area, and drops it back.
  python scripts/shoot.py shot out.png              one picture
  python scripts/shoot.py burst out_dir N [fps]     N pictures, numbered; fps defaults to 8 (a gif: python scripts/shoot.py gif out_dir out.gif)
Needs Pillow. The window must be visible on a monitor (not minimised)."""
import ctypes, sys, time, pathlib
from ctypes import wintypes
from PIL import ImageGrab, Image

u = ctypes.windll.user32
u.FindWindowW.restype = wintypes.HWND
HWND_TOPMOST, HWND_NOTOPMOST, SWP_NOMOVE_NOSIZE = -1, -2, 3

def window():
    h = u.FindWindowW(None, "Project Zomboid")
    h or sys.exit("no 'Project Zomboid' window (is the game running?)")
    return h

def raise_window(h):
    if u.GetForegroundWindow() == h:      # already in front (an earlier call raised it): no need to wait for it to repaint
        u.SetWindowPos(h, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE_NOSIZE); return
    u.keybd_event(0x12, 0, 0, 0); u.keybd_event(0x12, 0, 2, 0)    # a tap of Alt lets SetForegroundWindow through
    u.ShowWindow(h, 9); u.SetWindowPos(h, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE_NOSIZE); u.SetForegroundWindow(h)
    time.sleep(1.5)

def client_box(h):
    r, pt = wintypes.RECT(), wintypes.POINT(0, 0)
    u.GetClientRect(h, ctypes.byref(r)); u.ClientToScreen(h, ctypes.byref(pt))
    return (pt.x, pt.y, pt.x + r.right, pt.y + r.bottom)

def grab(h):
    return ImageGrab.grab(bbox=client_box(h), all_screens=True)

def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "gif":
        files = sorted(pathlib.Path(sys.argv[2]).glob("*.png"))
        frames = [Image.open(f).convert("P", palette=Image.ADAPTIVE) for f in files]
        frames[0].save(sys.argv[3], save_all=True, append_images=frames[1:], duration=int(1000 / 8), loop=0); return
    h = window(); raise_window(h)
    try:
        if cmd == "shot": grab(h).save(sys.argv[2])
        elif cmd == "burst":
            out = pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
            n, fps = int(sys.argv[3]), float(sys.argv[4]) if len(sys.argv) > 4 else 8
            for i in range(n):
                t = time.time(); grab(h).save(out / f"{i:03d}.png"); time.sleep(max(0, 1 / fps - (time.time() - t)))
        else: print(__doc__)
    finally:
        u.SetWindowPos(h, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE_NOSIZE)    # leave the window as the user had it
main()
