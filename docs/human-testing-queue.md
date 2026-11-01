# Human testing queue

Work down the list. Each item says what to do, what a pass looks like, and what to tell me if it fails. Tick the box and add a note in the Result column; I read this file when you say you are done.
Setup for all of them: boot with `python scripts/smoke_test.py play --keep` (the tester `Smoke1` ends up in the open field with god mode, clean needs, noon, dry weather), or use your own save with `/additem "<you>" ImpracticalTransport.<Item>` as admin. To face the camera press S; to face right press D.

Items: `PogoStick`, `Tricycle`, `Unicycle`.

What I already checked in game (2026-11-01, screenshots, so you can skip the obvious): the unicycle with the rider facing the screen has a vertical wheel and fork and an upright rider (A1 looks fixed), both arms out (A4), legs beside the tyre without pedals (A3), the mount goes stand, hand on the seat, then settles on the saddle (A5, the final arm looked bent up from behind: check it from the front), the dismount shows the unicycle swinging in the hand while it is put away (A6). The pedal direction (A2) is clockwise by the clip's maths but I could not read it from 10 fps frames, so it is yours to confirm. The smoke test passes for all three transports. The game is left running with the unicycle equipped.

## A. Looks (stand still, then walk in each direction; face the screen with S)

| # | Item | What to check | Pass looks like | Result |
|---|------|---------------|-----------------|--------|
| A1 | Unicycle | Upright when facing the screen (S) | Wheel and saddle straight up and down, rider not leaning to one side (fix: attachment `rotate 102 180 0`) | [ ] |
| A2 | Unicycle | Pedal direction going right (D) | Legs turn clockwise seen from the screen's side: the top of the circle moves forward | [ ] |
| A3 | Unicycle | Legs against the wheel | Feet ride close beside the tyre, no pedals or cranks | [ ] |
| A4 | Unicycle | Arms | Both arms out for balance while riding | [ ] |
| A5 | Unicycle | Mount (equip it) | Stand, right hand on the seat, then the arm goes out, about 1 s | [ ] |
| A6 | Unicycle | Dismount (put it away) | Arm back to the seat, then step off | [ ] |
| A7 | Tricycle | Upright facing the screen | Not leaning sideways (it still uses `rotate 90 180 0`, likely needs the same 102 correction) | [ ] |
| A8 | Tricycle | Pedal direction going right | Clockwise as seen from the right; probably backwards now | [ ] |
| A9 | Tricycle | Rider on the seat | Seat under the rider, hands on the grips, knees up | [ ] |
| A10 | Pogo | Stick fit in four facings and a wide circle | Hands on the grips, foot on the pads, stick upright, no floating | [ ] |
| A11 | Pogo | Mount and dismount | The hop on and off looks right, about 0.8 s | [ ] |
| A12 | All | Inventory icons | A recognisable icon for each item in the inventory list | [ ] |

## B. Feel (play for a few minutes)

| # | Item | What to check | Pass looks like | Result |
|---|------|---------------|-----------------|--------|
| B1 | All | Slower than walking | Each is clearly worse than walking, never better (pogo about 60 percent, tricycle about 35 percent, unicycle about 25 percent of walking) | [ ] |
| B2 | Tricycle | Pedal slip | Now and then the feet spin and it stands still for 1 to 2 s; not annoying more than every minute or so | [ ] |
| B3 | Tricycle | Falls | Rare; falls backwards off the seat, never sideways | [ ] |
| B4 | Unicycle | Wobble and falls | Wobbles often (feet and arms flail, stands still 1 s), falls more often than the tricycle | [ ] |
| B5 | Pogo | Falls | Trips about once every 80 s walking, more when running or winded | [ ] |
| B6 | All | Run (hold Left Shift) | Faster than walking pace of the same transport, trips more | [ ] |
| B7 | All | Sprint (Left Alt) | Does it enter the sprint state? (known problem: the key registers but the engine stays in run) | [ ] |
| B8 | All | Winded | Hold a long run: pace drops in steps (tiers) and endurance falls faster than walking | [ ] |
| B9 | All | Aim and swing | Blocked while riding | [ ] |

## C. World (needs a place with the right ground)

| # | Item | What to check | Pass looks like | Result |
|---|------|---------------|-----------------|--------|
| C1 | All | Mud, sand, shallow water | Much slower and more falls than on grass or dirt | [ ] |
| C2 | All | Through bushes | Many more trips | [ ] |
| C3 | All | With a heavy pack or injured legs | Slower on top of the transport's own speed | [ ] |
| C4 | All | Light rain or snow | Anything strange? (not implemented, just report) | [ ] |

## D. Decisions I need from you

| # | Question | Options | Answer |
|---|----------|---------|--------|
| D1 | Roller skates: worn or held? | A: a real worn Shoes item with wheels (faithful, much more work). B: a held item with a glide gait (cheap, consistent; I recommend B first) | |
| D2 | Which transport next after skates? | Stilts, inflatable ball with handles | |
| D3 | Should the tricycle get the same 102 tilt and clockwise pedals as the unicycle without waiting for A7 and A8? | Yes, do it now / wait for your result | |

## What to send back
For any failure: which item, which facing or action, and one sentence of what you saw. A screenshot helps. For speed items: how it felt (too slow, too fast, about right).
