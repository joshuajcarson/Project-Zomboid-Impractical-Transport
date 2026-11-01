# Working on this repo

Flow: branch from `main` (`claude/...` or `feature/...`), commit small verified steps, push, open a pull request into `main`, squash or merge it, delete the branch.

One-time setup per clone: `pip install -r requirements-dev.txt` (lupa, an embedded Lua 5.1, for the Lua syntax check) and `git config core.hooksPath .githooks` (a pre-push hook that runs the same checks as CI, so a failing push is stopped locally).

Before every push
1. `python scripts/smoke_test.py static` (it runs `scripts/check_repo.py` too; seconds; CI runs the same on the pull request, and the pre-push hook runs them automatically).
2. If anything under `Contents/` changed: `python <RL repo>/scripts/cleanup.py` then `python scripts/smoke_test.py play` (about 10 minutes, needs the game, the RL harness repo and a free PC). Paste its output in the PR.
3. After a merge, delete the branch and start the next one from the new `main` so history does not fork again.

Generated files: everything in `Contents/.../anims_X`, `models_X` and the palette textures comes from the scripts in `tools/blender/` (Blender 4.1, headless). Change the script and regenerate, never edit the `.X` files. They are marked generated in `.gitattributes` (collapsed diffs, conflicts take the regenerated copy). The repo is a few MB, so no Git LFS is used; revisit only if it passes ~100 MB.

Never commit: `previews/` (screenshots and bursts, git-ignored), game files, anything copied from the Project Zomboid install.
