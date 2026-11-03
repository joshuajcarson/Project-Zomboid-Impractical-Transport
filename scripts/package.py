"""Builds dist/ImpracticalTransport (git-ignored), the folder the in-game Workshop uploader takes, and prints what would be uploaded:
  python scripts/package.py
Layout: workshop.txt, preview.png (256x256) and Contents/mods/ImpracticalTransport/{42,common}, copied from git-tracked files only. It never talks to Steam;
the upload is manual, see docs/dev/release.md. Fails (and builds nothing) if the asset check fails, preview.png is not 256x256, or a poster is missing."""
import pathlib, shutil, subprocess, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import check_assets
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "dist" / "ImpracticalTransport"
MOD = "Contents/mods/ImpracticalTransport"

problems = check_assets.repo_problems()
Image.open(ROOT / "preview.png").size == (256, 256) or problems.append("preview.png must be 256x256")
(ROOT / MOD / "42/poster.png").is_file() or problems.append("42/poster.png missing (mod.info poster=)")
if problems:
    sys.exit("not packaging:\n" + "\n".join(problems))

tracked = subprocess.run(["git", "ls-files", "workshop.txt", "preview.png", MOD], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
shutil.rmtree(OUT, ignore_errors=True)
for f in tracked:
    (OUT / f).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / f, OUT / f)
total = sum((OUT / f).stat().st_size for f in tracked)
for f in tracked: print(f"{(OUT / f).stat().st_size:>9}  {f}")
print(f"{len(tracked)} files, {total / 1e6:.2f} MB -> {OUT}\nnext: docs/dev/release.md (manual upload from the game's Workshop menu)")
