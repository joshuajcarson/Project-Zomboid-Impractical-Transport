# Human testing queue

Work down the list. Each item says what to do, what a pass looks like, and what to tell me if it fails. Tick the box and add a note in the Result column; I read this file when you say you are done.
Setup for all of them: boot with `python scripts/smoke_test.py play --keep` (the tester `Smoke1` ends up in the open field with god mode, clean needs, noon, dry weather), or use your own save with `/additem "<you>" ImpracticalTransport.<Item>` as admin. To face the camera press S (the character faces world southeast); to face right press D (northeast), left A, away W. Pure south or east shows a 3/4 view.

Items: `PogoStick`, `Tricycle`, `Unicycle`.

What I already checked in game (2026-11-01, screenshots, so you can skip the obvious): the unicycle with the rider facing the screen has a vertical wheel and fork and an upright rider (A1 looks fixed), both arms out (A4), legs beside the tyre without pedals (A3), the mount goes stand, hand on the seat, then settles on the saddle (A5, the final arm looked bent up from behind: check it from the front), the dismount shows the unicycle swinging in the hand while it is put away (A6). The pedal direction (A2) is clockwise by the clip's maths but I could not read it from 10 fps frames, so it is yours to confirm. The smoke test passes for all three transports. The game is left running with the unicycle equipped.

## A. Looks (stand still, then walk in each direction; face the screen with S)

| # | Item | What to check | Pass looks like | Result |
|---|------|---------------|-----------------|--------|
| A1 | Unicycle | Upright when facing the screen (S) | Wheel and saddle straight up and down, rider not leaning to one side (fix: attachment `rotate 102 180 0`) | [FAIL - wheel to seat at impossible angle, left foot inside wheel, right foot floating, seat is overly blocky and wide and should be thiner] |
| A2 | Unicycle | Pedal direction going right (D) | Legs turn clockwise seen from the screen's side: the top of the circle moves forward | [PASS - feet rotate in correct direction] |
| A3 | Unicycle | Legs against the wheel | Feet ride close beside the tyre, no pedals or cranks | [FAIL - Reuse A1 image. Feet look to be where they should be, but whole unicycle at wrong angle. ] |
| A4 | Unicycle | Arms | Both arms out for balance while riding | [FAIL - A1 image for rest, no gif available for animation. At rest the arms are wide which is fine. In motion, the right arm elbow appears to have a tick where it pops back for no reason. Some sort of gentle non-jerky motion in the arms would be good instead of perfectly still] |
| A5 | Unicycle | Mount (equip it) | Stand, right hand on the seat, then the arm goes out, about 1 s | [PASS] |
| A6 | Unicycle | Dismount (put it away) | Arm back to the seat, then step off | [FAIL - Picks up the whole unicycle like a standard item during the animation. Would be better to step off, it stays on ground, then final step would be to put away. It picks it up and holds it up for too long while moving it around before the toss to back.] |
| A7 | Tricycle | Upright facing the screen | Not leaning sideways (it still uses `rotate 90 180 0`, likely needs the same 102 correction) | [FAIL - Right hand on handle, whole tricycle seems tilted in the same wrong way as unicycle, left back tire up in sky, no tire appears touching the ground] |
| A8 | Tricycle | Pedal direction going right | Clockwise as seen from the right; probably backwards now | [FAIL - Feet rotate wrong direction] |
| A9 | Tricycle | Rider on the seat | Seat under the rider, hands on the grips, knees up | [FAIL - Part of rider on seat, but most of seat is floating away. Seat itself should be even lower, forcing characters upper body to be always leaning a bit back. Should feel like adult riding children's toy. Keeping feet mostly where they are and lowering the hips while keeping torso struggling to stay vertical is the desired look] |
| A10 | Pogo | Stick fit in four facings and a wide circle | Hands on the grips, foot on the pads, stick upright, no floating | [FAIL - Right hand stays on handle, whole pogo goes into the characters body at rest. From bottom to top appears to have the same wrong tilt that unicycle and tricycle have. Feet appear where feet should be; pogo just isn't there] |
| A11 | Pogo | Mount and dismount | The hop on and off looks right, about 0.8 s | [PASS] |
| A12 | All | Inventory icons | A recognisable icon for each item in the inventory list | [FAIL - POGO good, unicycle verticle when should be tilter, wich more of a side profile to make the one wheel easier to see. Unicycle fine] |

## B. Feel (play for a few minutes)

| # | Item | What to check | Pass looks like | Result |
|---|------|---------------|-----------------|--------|
| B1 | All | Slower than walking | Each is clearly worse than walking, never better (pogo about 60 percent, tricycle about 35 percent, unicycle about 25 percent of walking) | [PASS] |
| B2 | Tricycle | Pedal slip | Now and then the feet spin and it stands still for 1 to 2 s; not annoying more than every minute or so | [PARTIAL FAIL - The slow down happened as expected and caused an animation, but it wasn't clear why. Need the upper body to also almost tilt back and recover itself. If possible, the whole tricycle should almost rotate backwards a tiny bit and have the front tire off the ground] |
| B3 | Tricycle | Falls | Rare; falls backwards off the seat, never sideways | [FAIL - Never fell off] |
| B4 | Unicycle | Wobble and falls | Wobbles often (feet and arms flail, stands still 1 s), falls more often than the tricycle | [FAIL - I can see the tricycle failure mode, but a unicycle would just fall over, not spin extra. Should be closer to how pogo sticks should fall as their failure mode] |
| B5 | Pogo | Falls | Trips about once every 80 s walking, more when running or winded | [FAIL - The speed up from run and sprint both worked and were noticable, but I never failed when using pogo] |
| B6 | All | Run (hold Left Shift) | Faster than walking pace of the same transport, trips more | [PASS] |
| B7 | All | Sprint (Left Alt) | Does it enter the sprint state? (known problem: the key registers but the engine stays in run) | [UNKNOWN - I tested left alt by itself with no items to confirm it is sprint and that worked. With items, I couldn't tell if it was another form of run or slightly faster sprint] |
| B8 | All | Winded | Hold a long run: pace drops in steps (tiers) and endurance falls faster than walking | [PASS] |
| B9 | All | Aim and swing | Blocked while riding | [PASS] |

## C. World (needs a place with the right ground)

| # | Item | What to check | Pass looks like | Result |
|---|------|---------------|-----------------|--------|
| C1 | All | Mud, sand, shallow water | Much slower and more falls than on grass or dirt | [UNKNOWN - All testing in the dirt field] |
| C2 | All | Through bushes | Many more trips | [UNKNOWN - All testing in the dirt field] |
| C3 | All | With a heavy pack or injured legs | Slower on top of the transport's own speed | [UNKNOWN - All testing health at less than max weight] |
| C4 | All | Light rain or snow | Anything strange? (not implemented, just report) | [UNKNOWN - Always sunny] |

## D. Decisions I need from you

| # | Question | Options | Answer |
|---|----------|---------|--------|
| D1 | Roller skates: worn or held? | A: a real worn Shoes item with wheels (faithful, much more work). B: a held item with a glide gait (cheap, consistent; I recommend B first) | Try for worn. Glasses impact UI, running shoes vs work boots impact walking speed today, plus wearing roller skates while trying to drive should also make driving harder and therefore lead to hilarious experiences. Try multiple experiments to get worn to work before defaulting back to held|
| D2 | Which transport next after skates? | Stilts, inflatable ball with handles |Inflatable Ball then Stilts|
| D3 | Should the tricycle get the same 102 tilt and clockwise pedals as the unicycle without waiting for A7 and A8? | Yes, do it now / wait for your result |I am unsure. They all seemed tilted wrong in one direction. I listed which vehicle had the legs rotating in the correct way - anything pedal powered in the future should use that|

## What to send back
For any failure: which item, which facing or action, and one sentence of what you saw. A screenshot helps. For speed items: how it felt (too slow, too fast, about right). - Screenshots located in previews/human and file name has step first tested in. I also placed all items on ground to see how they looked -> they looked fine on the ground and I added that screenshot too
