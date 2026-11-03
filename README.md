# Impractical Transport

A Project Zomboid **Build 42** mod of ridiculous ways to get around, every one of them worse than walking. They look silly, move slowly, tire you out, trip you, and punish you on rough ground.

> Work in progress. Not on the Steam Workshop yet.

## Transports

| Transport | How you use it | The catch |
|-----------|----------------|-----------|
| Pogo stick | hold it (two hands) | about 60% of walking speed, trips every minute or so, terrible on mud and sand |
| Tricycle | hold it, ride it seated | about 35% of walking speed, the pedals slip, sometimes tips you over backwards |
| Unicycle | hold it, ride it | about 25% of walking speed, constant wobbling, falls |
| Roller skates | wear them in the shoes slot | glides on after you stop, falls when stopping, about 30% faster than walking on pavement and slower on dirt |
| Stilts | wear them in the shoes slot | about 25% of walking speed, sinks into soft ground, falls |
| Inflatable ball with handles | planned for a later update | |

Running and sprinting work for all of them (faster, but you trip more), tiredness and heavy loads slow you further, and whatever slows normal walking (brush, injuries) applies on top.

Find them in toy stores, sports stores, kids' bedrooms and wardrobes, and now and then in garages and storage.

## Install (development builds)
Copy or symlink `Contents/mods/ImpracticalTransport` into your Project Zomboid `mods` folder and enable **Impractical Transport** in the mods list. Items for testing: as admin, `/additem "<your name>" ImpracticalTransport.PogoStick` (also `Tricycle`, `Unicycle`, `RollerSkates`). Held transports are equipped like a weapon; skates are worn like shoes.

## For developers
- How it works, the asset pipeline and the test harness: [docs/dev/architecture.md](docs/dev/architecture.md)
- How to contribute (branches, checks, the pull request flow): [CONTRIBUTING.md](CONTRIBUTING.md)
- Open work and ideas: [GitHub issues](https://github.com/joshuajcarson/Project-Zomboid-Impractical-Transport/issues)
- Development journal (decisions, test results): [docs/dev/journal.md](docs/dev/journal.md)
- Human test queue: [docs/human-testing-queue.md](docs/human-testing-queue.md)

## Licence and credit
Code and original models are MIT licensed ([LICENSE](LICENSE)). Animation clips and the skates model embed the survivor skeleton (bone names and bind offsets) taken from Project Zomboid, which remains The Indie Stone's; this is used under their [Terms](https://projectzomboid.com/blog/support/terms-conditions/) and [Modding Policy](https://projectzomboid.com/blog/modding-policy/). Details in [NOTICE.md](NOTICE.md). No game art, audio, textures or code are included.

> Thanks to The Indie Stone for creating Project Zomboid (https://projectzomboid.com/), which made this possible. This is an unofficial fan production for non-commercial purposes made under the Indie Stone Terms (https://projectzomboid.com/blog/support/terms-conditions/)
