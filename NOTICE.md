# Notice: Project Zomboid content

This is an unofficial fan mod. It is not made, endorsed or supported by The Indie Stone.

> Thanks to The Indie Stone for creating Project Zomboid (https://projectzomboid.com/), which made this possible. This is an unofficial fan production for non-commercial purposes made under the Indie Stone Terms (https://projectzomboid.com/blog/support/terms-conditions/)

What is ours and what is not
- **Ours (MIT, see LICENSE):** the Lua, the Blender and Python tools, the models built from primitives (pogo stick, tricycle, unicycle, roller skates), their palette textures and icons, and the animation poses we author.
- **Derived from Project Zomboid (not covered by our MIT licence; The Indie Stone's rights apply):** every generated animation clip (`anims_X/Bob/*.X`) and the roller skates model (`models_X/ImpracticalTransport/RollerSkates.X`) carries the survivor skeleton: the bone names, bone hierarchy and bind-pose offsets, copied by `tools/blender/clipio.py` and `tools/blender/skates_model.py` from the game's own `MaleBody.x`. The engine needs them to load the file. That is the only game data in the repository. No game art, textures, models, audio or code are included, and nothing from another mod.

Why this is allowed (checked 2026-11-01)
- Terms & Conditions section 2.1 licenses changing or distributing base files or contents provided the result does not make Project Zomboid itself available to play or download; section 2.2 allows using assets for non-commercial, related fan work if the credit text above accompanies them; section 2.6 permits mods that follow the Modding Policy ([terms](https://projectzomboid.com/blog/support/terms-conditions/), last updated 6 October 2022).
- Modding Policy (last updated 10 April 2022, [policy](https://projectzomboid.com/blog/modding-policy/)): you own your mod (3.1) and grant The Indie Stone a licence to use it (3.2); it may not be sold (2.4), may not exclude non-donors through donation-only content (2.3) and may not pose as official (2.2.3).
- So this mod is free, non-commercial, carries the credit above, and is not presented as official. Do not add paid access, and keep the credit text in the Workshop description. Re-read both documents before each public release, they can change. This is the maintainer's reading of public terms, not legal advice.
