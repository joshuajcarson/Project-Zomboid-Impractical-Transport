"""Makes a frozen game window repaint (identical screenshots mean it stopped): minimise 2 s, restore, Alt tap, foreground, mouse over it. Run before shoot.py after UI or view commands."""
import ctypes, time
from ctypes import wintypes
u = ctypes.windll.user32
u.FindWindowW.restype = ctypes.c_void_p
h = ctypes.c_void_p(u.FindWindowW(None, "Project Zomboid"))
u.ShowWindow(h, 6); time.sleep(2); u.ShowWindow(h, 9); time.sleep(1)
u.keybd_event(0x12, 0, 0, 0); u.keybd_event(0x12, 0, 2, 0); u.SetForegroundWindow(h); time.sleep(3)
pt = wintypes.POINT(0, 0); u.ClientToScreen(h, ctypes.byref(pt)); u.SetCursorPos(pt.x + 320, pt.y + 200); time.sleep(1)
