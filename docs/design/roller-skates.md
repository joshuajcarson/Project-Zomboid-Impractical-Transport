# Roller skates: design notes and backlog

Status 2026-11-01: worn shoes-slot item works (`RollerSkates`, `worn = true` profile), skating gait clips and nodes exist, smoke test passes (0.71 tiles/s against 0.70 expected). No model on the feet yet.

## Direction from the user (2026-11-01)
Skates may eventually be faster and more efficient than walking on streets, but must be extremely bad everywhere else, and must interfere with other actions (driving, climbing or vaulting fences, using the other impractical transports). So the skates are a trade, not a flat penalty, unlike the held transports which are strictly worse than walking.

## Backlog: other ways skates can be a net negative (only where it makes physical sense)
Each item says how it could be done; none is built yet.
1. **Surface table (extends the ground table already in the Lua).** Hard smooth ground (asphalt, concrete, tile, wood floors): faster than walking (a speed above 1, clip tier faster than the walk clip). Everything else: much worse than walking (grass, dirt, sand, gravel, mud, snow, shallow water: slow tier plus a high trip chance). Needs faster skating clips (an extra tier above T0) and a classification of "smooth" labels (the Lua already prints unclassified ground labels once).
2. **Wet and bad pavement.** Rain, cracks, debris: more slips. Dry road is the only good case.
3. **Stairs, ramps, curbs, door thresholds.** Stairs: refuse to climb or always fall; curbs and thresholds: a trip chance when crossing between ground types or through doorways.
4. **Fences, windows, climbing, vaulting.** Block the action with a message ("take your skates off") or make it a guaranteed fall; hook the vanilla climb/vault timed actions the same way the unequip wrapper hooks `ISUnequipAction`.
5. **Driving and other transports.** Entering a vehicle with skates on: slow or a stumble; driving: harder (hook the vehicle enter action, maybe a steering or braking penalty through vehicle variables); the held transports (pogo, tricycle, unicycle) cannot be used with skates on (equip refused or an immediate fall).
6. **Noise.** Rolling on pavement is loud: add a sound (`addSound`) while moving so zombies are drawn in; no sneaking, no stealth.
7. **Fighting.** Melee and shoving while on skates cause a stumble; being hit knocks the rider over more easily; no kicking or stomping.
8. **Load.** Heavy packs or injured legs raise the fall chance sharply (the encumbrance check already exists in the harness).
9. **Feet.** No shoe protection while the skates are on (glass, bites to the feet if the game models it); skates are heavy to carry.
10. **Turning.** A wide turning circle (limit how fast the facing can change) and falls on sharp turns.
11. **Items on the ground and corpses.** Rolling over loot piles, corpses or small objects trips the rider.
Open design questions for later: how much faster than walking on streets (a small edge, say 1.2x walking, keeps the joke), whether there is any way to turn the skates "off" without taking them off.

## Stopping is hard (user request)
Goal: a rider moving at speed does not stop when the keys are released; they coast and slide, and stopping at speed often ends in a fall.
- **Vehicle inspiration.** Vehicles keep their velocity because the engine integrates a velocity; the character controller has no inertia (the player stops the instant the input stops). We cannot add a velocity to the player directly, so the plan uses animation travel.
- **Plan A (animation travel, cheapest).** When the rider goes from moving to not moving, the Lua sets `SkatesCoast` for a short time (about 0.8 s walking, 1.4 s running, shorter on rough ground). A `coast_skates` node in the idle state plays `Bob_SkateCoast`, a gliding pose whose `Translation_Data` carries the rider forward with decreasing speed. This needs clipio's `write_clip` to take a list of (frame, distance) keys instead of one linear travel, and an experiment to prove that an idle-state clip's deferred travel really moves the player (the mount clips use zero travel, so this is untested). Moving again ends the coast at once.
- **Plan B (script-driven slide).** If idle clips do not move the player, nudge the player's position each tick during the coast with a decaying speed (client side `setX/setY` or a path/teleport request; riskier in multiplayer).
- **Falls on stopping.** A stumble chance at the stop moment: small when walking (about 5 percent), large when running (about 25 percent), higher when winded or on bad ground, plus a smaller chance on a sudden direction reversal. These reuse `ImpracticalTransport.stumble` and the `calm` switch for tests.
- **Test plan.** Harness: ride, release the keys, log the distance travelled after the input stopped (expected: 0.3 to 0.8 tiles), count falls over many stops with `smokecalm` off, plus a smoke check that the coast node plays.
