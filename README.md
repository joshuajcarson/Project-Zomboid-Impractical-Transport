# Impractical Transport (Project Zomboid, Build 42)

Layout follows the B42 workshop format: `Contents/mods/<id>/{common,42}`. Build-specific files live in `42/`; if a patch breaks something, copy `42/` to `42.x/` and fix only there.

## Design (maintenance-first)
- **Two kinds of transport, no Java either way** (script-only vehicles are proven on the Workshop, e.g. TEHE-Studios/ExpandedHelicopterEvents `media/scripts/vehicles/*.txt`).
  - **Real vehicle** (tricycle, later unicycle/roller skates if they work as vehicles): `scripts/vehicles/*.txt` + `.fbx` + texture. Physics come from the game.
  - **Held item** (pogo stick, stilts): item script + Lua in `media/lua/client/ImpracticalTransport.lua`; riding derived from the equipped item each tick, no saved state.

## Status
Scaffold only, **untested in-game**. Tricycle vehicle script written (all numbers are guesses; mesh `vehicles/ImpracticalTransport/Vehicle_Tricycle.fbx` and texture do not exist yet, so the script will error until they do). Done: mod.info, placeholder pogo item, riding flag (`ImpracticalRiding` anim variable).
Open question for the tricycle: vehicles expect an engine to start; test whether omitting Engine/Battery parts lets it move, else add a hidden always-working engine part.
Next: (1) load in B42 and confirm item spawns; (2) movement: hop cadence + speed cap (find a supported speed hook, vanilla Lua only exposes `getRunSpeedModifier`); (3) AnimSets under `media/AnimSets/player/` keyed on `ImpracticalRiding`; (4) fall/injury on zombie bump via `OnPlayerGetDamage`; (5) 3D model (.fbx) + icon; tricycle second.
