# Impractical Transport

A Project Zomboid **Build 42** mod of ridiculous ways to get around, every one of them worse than walking. They look silly, move slowly, tire you out, trip you, and punish you on rough ground.

> Work in progress. Not on the Steam Workshop yet.

## Transports

| Transport | How you use it | The catch |
|-----------|----------------|-----------|
| Pogo stick | hold it (two hands) | about 60% of walking speed, trips every minute or so, terrible on mud and sand |
| Tricycle | hold it, ride it seated | about 35% of walking speed, the pedals slip, sometimes tips you over backwards |
| Unicycle | hold it, ride it | about 25% of walking speed, constant wobbling, falls |
| Roller skates | wear them in the shoes slot | glides on after you stop, falls when stopping, slower than walking for now |
| Inflatable ball with handles, stilts | planned | |

Running and sprinting work for all of them (faster, but you trip more), tiredness and heavy loads slow you further, and whatever slows normal walking (brush, injuries) applies on top.

## Install (development builds)
Copy or symlink `Contents/mods/ImpracticalTransport` into your Project Zomboid `mods` folder and enable **Impractical Transport** in the mods list. Items for testing: as admin, `/additem "<your name>" ImpracticalTransport.PogoStick` (also `Tricycle`, `Unicycle`, `RollerSkates`). Held transports are equipped like a weapon; skates are worn like shoes.

## For developers
- How it works, the asset pipeline and the test harness: [docs/dev/architecture.md](docs/dev/architecture.md)
- How to contribute (branches, checks, the pull request flow): [CONTRIBUTING.md](CONTRIBUTING.md)
- Open work and ideas: [GitHub issues](https://github.com/joshuajcarson/Project-Zomboid-Impractical-Transport/issues)
- Development journal (decisions, test results): [docs/dev/journal.md](docs/dev/journal.md)
- Human test queue: [docs/human-testing-queue.md](docs/human-testing-queue.md)

Licence: see [LICENSE](LICENSE). The mod ships no game assets; generated models and animations are built from scripts in `tools/` and read the game's own files from your install only to build previews.
