"""Fails when a tracked file looks like a Project Zomboid game asset (run by check_repo.py, so by CI and the pre-push hook):
  python scripts/check_assets.py
How: every tracked .X .png .ogg .wav .jpg .tga .fbx file, and every .txt under Contents/, must match a glob in scripts/asset_allowlist.txt, which lists only
files we generate or hand-write (each with the tools/ script that makes it). A new asset therefore fails until a human adds a line and says where it came
from. If the game install is present (not on CI) two more checks run: a tracked file whose bytes are identical to a game file fails even if allowlisted,
and a non-allowlisted file with the same name as a game file is reported as a probable copy. Exit 0 = pass.
shortcut: the allowlist is trusted, a human can list a copied file; the hash check catches it only on a PC that has the game installed."""
import fnmatch, hashlib, os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GAME = pathlib.Path(os.environ.get("PZ_DIR", r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid"))
EXTS = {".x", ".png", ".ogg", ".wav", ".jpg", ".tga", ".fbx"}

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def check(tracked, allow, game=GAME):
    """tracked: repo-relative posix paths. Returns a list of problem strings."""
    problems = []
    allowed = lambda f: any(fnmatch.fnmatch(f, g) for g in allow)
    risky = [f for f in tracked if pathlib.PurePosixPath(f).suffix.lower() in EXTS or (f.startswith("Contents/") and f.lower().endswith(".txt"))]
    for f in risky:
        allowed(f) or problems.append(f"{f}: asset-shaped file not in scripts/asset_allowlist.txt (if we made it, add it with the tools/ script that generates it; if it came from the game, delete it)")
    if game.is_dir() and risky:
        sizes = {}
        for f in risky: sizes.setdefault((ROOT / f).stat().st_size, []).append(f)
        names = {pathlib.PurePosixPath(f).name.lower(): f for f in risky}
        for dirpath, _, files in os.walk(game):
            for n in files:
                gp = pathlib.Path(dirpath, n)
                if n.lower() in names and not allowed(names[n.lower()]): problems.append(f"{names[n.lower()]}: same name as game file {gp}")
                try: size = gp.stat().st_size
                except OSError: continue
                for f in sizes.get(size, []):
                    sha(gp) == sha(ROOT / f) and problems.append(f"{f}: identical to game file {gp}")
    return problems

def repo_problems():
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    allow = [l.strip() for l in (ROOT / "scripts/asset_allowlist.txt").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
    return check([f for f in tracked if (ROOT / f).is_file()], allow)

def main():
    problems = repo_problems()
    print("\n".join(problems) if problems else "asset checks ok")
    return 1 if problems else 0

if __name__ == "__main__":
    sys.exit(main())
