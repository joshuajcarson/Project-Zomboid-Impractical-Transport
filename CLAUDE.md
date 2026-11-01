# Working agreement for Claude in this repo

- Read `CONTRIBUTING.md` first (branch, checks, PR flow) and `docs/dev/journal.md` for the history and decisions. How the mod works: `docs/dev/architecture.md`.
- Tasks, bugs and ideas live in **GitHub issues** (`gh issue list`), not in the README. When you start one, comment or reference it in commits (`refs #n`); close it from the PR (`Closes #n`). New ideas found while working become issues with a label (`transport`, `design`, `tooling`, `needs-human-test`).
- A human test is an issue labelled `needs-human-test` (or a row in `docs/human-testing-queue.md`); do not mark it done yourself.
- Before every push: `python scripts/smoke_test.py static` (the pre-push hook runs it). If `Contents/` changed, run the full smoke test (`python scripts/smoke_test.py play`, needs the user's PC; run `python <RL repo>/scripts/cleanup.py` first) and paste its output in the PR.
- Never edit generated `.X` files, regenerate them from `tools/blender/`. Never commit `previews/` or anything copied from the game install.
- Never leave resume state only in your head: put it in `docs/dev/journal.md` before stopping.
