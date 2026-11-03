# Releasing to the Steam Workshop (manual)

## Before
1. Re-read the Indie Stone [Terms](https://projectzomboid.com/blog/support/terms-conditions/) and [Modding Policy](https://projectzomboid.com/blog/modding-policy/) (NOTICE.md records the dates last checked: Terms 2022-10-06, Policy 2022-04-10). If either date changed, re-check NOTICE.md and `workshop.txt`'s credit line.
2. `python scripts/smoke_test.py static` and, since `Contents/` is what ships, the full `python scripts/smoke_test.py play` (see CONTRIBUTING.md). All `needs-human-test` issues for the release are closed by the human.
3. If the art changed: `python tools/make_preview.py` (writes `preview.png` and `42/poster.png`).

## Build the folder
`python scripts/package.py` builds `dist/ImpracticalTransport` (git-ignored) from tracked files only and lists what it contains: `workshop.txt`, `preview.png` (256x256), `Contents/mods/ImpracticalTransport/{42,common}`. It refuses to build if `scripts/check_assets.py` finds a game-asset-shaped file that is not in `scripts/asset_allowlist.txt`.

## Upload (by hand, once per release)
1. Copy `dist/ImpracticalTransport` into `%USERPROFILE%\Zomboid\Workshop\` (so `...\Workshop\ImpracticalTransport\workshop.txt` exists). Do not edit it in place; rebuild instead.
2. Start the game (Steam running, logged in), Main Menu > Workshop > Create/Update Item, pick `ImpracticalTransport`, check the preview and description, accept the Steam Workshop legal agreement (first upload only), Upload.
3. `workshop.txt` is `visibility=private` so the first upload is only visible to you. On the item's Steam page set it to Friends-only for testers, then Public when ready (or change `visibility=` to `friendsOnly` / `public` and re-upload). The first upload writes an `id=` line into the copy of `workshop.txt` under `Zomboid\Workshop`; copy that line into the repo's `workshop.txt` so later uploads update the same item instead of creating a new one.
4. Subscribe from another Steam account or a clean profile and start a game to confirm the mod loads.

## A later GitHub Action
Only a sketch, nothing is set up. The upload needs SteamCMD (`workshop_build_item`) with a Steam account, and the game's own uploader cannot run on a runner. That means Steam credentials (and a Steam Guard bypass or a dedicated account without 2FA) stored as repository secrets. Risk: a leaked or abused secret lets anyone publish to the Workshop item and possibly lock the account. If done: a dedicated Steam account that owns nothing else, secrets only in a protected `release` environment with required reviewer, triggered by a tag, running `package.py` first. Until then, upload by hand.
