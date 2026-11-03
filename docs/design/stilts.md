# Stilts: design notes (issue #7)

Status 2026-11-03: built, not yet seen in the game (the PC was not available). Needs the game checks at the bottom.

## Choice: worn, like the skates
Worn item in the shoes slot (`ImpracticalTransport.Stilts`, profile `worn = true`). Reasons: nothing is held (hands stay free for flapping balance arms and for the other held transports' rules), and the skates path already does everything needed (skinned clothing model, Lua profile, gait clips, anim nodes, smoke test). A held model could not show poles on the feet at all.
- Model (`tools/blender/stilts_model.py`): per leg a foot-rest plate, a wooden pole `RAISE` (0.35 units, about 0.7 m) long with a rubber tip, a strut up the outside of the shin and two straps. Foot rest, pole and lower strut are skinned to the foot bone, upper strut and straps to the calf bone. The icon is drawn pixel by pixel in the same script.
- Gait (`tools/blender/stilts_gait.py`): the whole rider is lifted by `RAISE`, legs almost straight, short high steps, wide stance, the body rocks 6 degrees side to side, arms out and flapping. Clips: `Bob_StiltsWalk`, `Bob_StiltsWalkRun`, each in tiers T1 and T2 (0.6x and 0.3x travel), and `Bob_StiltsIdle` (a slow sway). Travel is baked in: walk 0.55 tiles/s, run 0.8 (bare walking is about 1.45).
- Nodes: `tools/make_gait_nodes.py` entry `Stilts` (walk, run, sprint, idle), no coast.
- Lua profile: slower than walking, stumble 0.025 per second fresh (a fall every 40 s, more when winded, 3x running, 4x sprinting), higher endurance drain, and `groundPow = 2`: the ground table is squared for stilts, so grass is 0.81, dirt 0.72, gravel 0.49, sand 0.25, mud 0.12 for speed, and the fall chance is squared the same way (sand 6x, mud 9x). Paved ground is neutral. Bushes and trees still multiply the trip chance by 4.

## Limits, stated plainly
The character cannot become taller in the engine. The raise is an animation offset only (the pelvis and feet in the clip are lifted, the rest of the character keeps its real position):
- Collision, hit box and doorways: unchanged. The rider fits every door, and zombies and bullets treat them as normal height; there is no head clearance problem because there is no extra height.
- The raised body is drawn above its square, so it can overlap walls, roofs and the tile above while it walks next to them, and can be drawn through upper floor edges. Shadows stay on the ground.
- Climbing, vaulting fences and stairs: vanilla clips play without the raise, so the character visibly drops to the ground for them, and the stilt poles under the feet are then too short to reach the ground. Not blocked in this first version (skates have the same gap; see docs/design/roller-skates.md backlog).
- Camera: not moved. A 0.7 m raise is small against the isometric view, but the head goes up the screen by that much.
- Only a worn item: wearing other shoes at the same time is refused by the shoes slot.
- The walk sway is baked into the clip; the rider does not really lose balance, the falls come from the Lua stumble chance.

## Game checks needed (the lead, on a free PC)
1. `python <RL repo>/scripts/cleanup.py`, then `python scripts/smoke_test.py play --keep` (the new stilts block follows the skates block; it fails if stilts are not clearly slower than 70 percent of walking or the expected-speed log disagrees by more than 30 percent).
2. Screenshots at the four facings (S, W, D, A keys; see the memory notes on isometric facings) with `smokeview`: poles visible below the feet, straps on the shins, no mesh stretching at the knee, raise looks right with the pole tips on the ground (if the tips float or sink, change `RAISE` in both scripts and regenerate).
3. Speed: stilts about 0.55 tiles/s walking, 0.8 running (the log prints `expected=`), on dirt probably tier 1 (0.33).
4. Fall rate in a fresh run with `smokecalm 0`: about one fall per 40 s on grass, many more on sand and mud.
5. Idle: standing sway visible, arms out.
