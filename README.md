# Impractical Transport (Project Zomboid, Build 42)

Layout follows the B42 workshop format: `Contents/mods/<id>/{common,42}`. Build-specific files live in `42/`; if a patch breaks something, copy `42/` to `42.x/` and fix only there.

## Design (maintenance-first)
- **Lua + item scripts only. No Java patches, no true BaseVehicle.** Vehicles are engine-heavy and break on patches; a held/ridden item is cheap to maintain.
- Each transport = one item script + one entry in `RIDEABLE` (`media/lua/client/ImpracticalTransport.lua`). Adding stilts/skates = new entry + model + anim set.
- No saved state: riding is derived from the equipped item every tick.

## Status
Scaffold only, **untested in-game**. Done: mod.info, placeholder pogo item, riding flag (`ImpracticalRiding` anim variable).
Next: (1) load in B42 and confirm item spawns; (2) movement: hop cadence + speed cap (find a supported speed hook, vanilla Lua only exposes `getRunSpeedModifier`); (3) AnimSets under `media/AnimSets/player/` keyed on `ImpracticalRiding`; (4) fall/injury on zombie bump via `OnPlayerGetDamage`; (5) 3D model (.fbx) + icon; tricycle second.
