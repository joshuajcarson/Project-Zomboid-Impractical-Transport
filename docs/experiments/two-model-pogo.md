# Experiment: two-model pogo stick (spring compression)

Question: can the stick show its spring compressing by splitting it into an upper part (handles and tube, primary hand, bone `Bip01_Prop1`) and a lower part (spring, pads, foot; a companion item in the secondary hand, bone `Bip01_Prop2`) and letting the hop clip move Prop2 relative to Prop1?

Fallback (the likely outcome): the single static model that exists today (`PogoStick`, rotate 102). This experiment must justify its extra complexity.

Written before any test ran. The experiment uses separate throw-away items (`PogoSplitUpper`, `PogoSplitLower`), so the real `PogoStick` is untouched until the verdict.

> Amended before any test ran (2026-10-31): the split is the foot and tip rod (secondary hand) versus everything else (primary hand), because on a real pogo stick the pads stay with the rider and the foot rod retracts. Criteria 7 and 8 originally measured handlebar-to-pads, which does not change in this design.

## Acceptance criteria (all must pass to keep two models)

**A. It works as an item pair (hard requirements)**
1. With the upper part equipped from the inventory by the normal equip action, the lower part ends up in the secondary hand without the player doing anything else, and both are visible in a screenshot at rest. Checked with the smoke harness (`smokehands`-style log of both hand slots) and `scripts/shoot.py`.
2. Unequipping (the real unequip action) leaves both hands empty and both items in the inventory, ten times in a row, with the client and server agreeing (no "hands full but nothing drawn" desync). No `ImpracticalTransport ... disabled` lines and no mod Lua errors in the client log.
3. If the lower part is missing (dropped, or removed by the player), the rider still rides with the upper part and the mod does not throw; the lower part is re-equipped on the next ride, or the ride falls back sensibly. Tested once by removing it by hand mid-ride.

**B. Nothing already working gets worse**
4. Hop speed on the dirt field is within 10% of the single-model stick (smoke test speed check), walk and run.
5. A forced stumble still runs and the rider recovers with both items intact.
6. Mount and dismount clips still play (log shows `riding=true`, then `riding=false`).

**C. The point of the experiment: the spring visibly compresses**
7. In a burst of at least 8 screenshots while hopping on the dirt field (`python scripts/shoot.py burst`), the distance from the foot tip to the pads varies by at least 20% of the fully extended tip-to-pad distance between the longest and shortest frame, judged on the contact sheet and by measuring the pixel distance between the tip and the pad colours in the frames.
8. The foot tip does not leave the ground in the compressed frames more than it does in the single-model stick, and the foot part never separates from the main part by a visible gap at rest.

**D. Cost is acceptable (judgement, written down with the verdict)**
9. Extra Lua stays under about 60 lines, with no new per-tick cost beyond the existing handler.
10. A second inventory item exists. It must be hideable or at least not confusing: its name reads as part of the pogo stick, and dropping the pair at once is possible. If the pair cannot be dropped or put away as one action, that is a fail.

## Verdict rule

- Keep two models only if 1 to 8 all pass and 9 and 10 are judged acceptable. Anything less: delete the experiment code, keep the single static model, and record why in this file.
- Either way, record the evidence (log excerpts, contact sheets under `previews/`, git-ignored) and the verdict at the bottom of this file.

## Verdict

**No-go: keep the single static model (2026-10-31).** Stopped after four rounds in game; the code is kept, unmerged, on the local branch `experiment/two-model-pogo` (delete it with `git branch -D experiment/two-model-pogo`).

| # | Criterion | Result |
|---|---|---|
| 1 | Pair equips, both visible at rest | Pass. The upper half goes in the primary hand and the foot piece is equipped into the secondary hand by a real action; at rest the pair looks the same as the single model. |
| 2 | Unequip clears both, ten times, no desync | Partly: one unequip cleared both hands and returned both items. Ten repeats not run. |
| 3 | Missing foot piece | Not tested. |
| 4 | Speed within 10% | Not measured. |
| 5 | Stumble, both items intact | Items stayed intact, but the foot rod flew off to the side during the fall (see below). |
| 6 | Mount and dismount | Not checked separately. |
| 7 | Foot-to-pad distance varies by 20% or more | **Fail / not measurable**: the foot rod hung about 0.18 game units below the pads in every hop frame, detached from the stick, so its motion says nothing about the spring. |
| 8 | No visible gap at rest or in the hop | **Fail**: gap in every hop frame. |
| 9 | Extra Lua under about 60 lines | Pass (about 25 lines). |
| 10 | Second inventory item is not confusing | Not settled: it adds an item the player can drop or lose, and the foot piece needs a server-side add in a real mod. |

Findings that matter if this is ever retried:
- With the clip putting `Bip01_Prop2` exactly on `Bip01_Prop1` and the same attachment on both models, the two models still did not coincide in game. So the engine does not apply a secondary-hand model the way a primary-hand one is applied (a mirror or a different frame for the left hand are the likeliest causes), and the placement convention is unknown. Getting it right needs more calibration rounds, each a full 5 to 6 minute boot.
- Any vanilla animation that does not key Bip01_Prop2 (stumble, fall, get up, every action animation) puts the foot rod at the left hand: in the stumble burst it flew away from the stick. Fixing that would mean hiding or re-keying the foot piece in every state.
- A second model per stick means every future transport needs the same pair, clip and companion logic.
- Mesh export bug found on the way: a part joined onto a rotated rod came out turned, because the exporter wrote object-local coordinates; it must use world coordinates (`obj.matrix_world`).
- Cost against benefit: the benefit is one visible spring compression; the single static model already shows the hop, and the rider's own crouch carries the impression of a spring.

Evidence (git-ignored, local): `previews/split_rest3.png` (rest, both pieces), `previews/split_hop3_sheet.png` (hop, detached rod), `previews/split_hop2_sheet.png` (stumble, rod flying off), `previews/diag_sheet.png` (diagnostic items).
