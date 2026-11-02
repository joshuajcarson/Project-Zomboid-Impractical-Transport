# Existing Zomboid modding tools: research notes

Date: 2026-11-01. Method: web search and page fetches only (no game run). Repo files were not compared against these tools beyond the task brief.
Caveat: pzwiki.net returned HTTP 403 to our fetcher, so everything about pzwiki pages (Attachment Editor, Creating custom animations, Modeling, AnimZed, AnimSet, Debug mode) comes from search-result snippets only. Fetch them by hand in a browser before relying on them.
"Last updated" is mostly UNVERIFIED: GitHub pages fetched showed no commit dates.

## Summary: what is worth acting on (ranked)

1. **AnimForge** (in-game animation editor, B42). Closest thing to "tune held items and poses without a 10 min boot": the equipped item is attached to the hand while you pose bones live, it edits .X directly, and some edits hot-reload. Problems 1, 2, 5. Caveat: needs a prebuilt engine-class patch (3 loose class files overriding the jar, reinstalled after every game update), and it is aimed at Gunworks reload clips, so UNVERIFIED whether it works for our non-gun props and skates. Try on the user's PC.
2. **Game's own Attachment Editor + Animation Viewer (debug mode).** Per search snippets these are debug-menu tools; the API docs recommend the Attachment Editor for tuning `attachment` offset/rotate. UNVERIFIED how it handles a bone rolled in a custom pose, and whether it works on a model without a vanilla AnimSet (HorseMod needed a patch for a custom AnimSet).
3. **FBX hot reload (pzwiki Modeling page, snippet only).** pzwiki says .fbx is hot-reloaded in game when the file changes and calls DirectX .x "not recommended for modding". We author .X by hand. If .fbx reload is real, exporting our clips as .fbx could remove restarts for animation tuning. UNVERIFIED for B42 and our skeleton. AnimForge claims .x clips load "the same way vanilla clips do", so .x is not dead.
4. **SaintBaron io_directx_x** (Blender add-on). Imports AND exports .x incl. skeleton, skin weights, animation, 4800 ticks/s biped, text and binary; README says PZ character/animation .x "verified loading in-game". Could cross-check or replace our hand-written writer, and import vanilla .X to inspect Bip01_Prop1 roll offline. Needs Blender 4.2+ (we use 4.1). GPL-3.0.
5. **Paddlefruit Community Rig** (Blender 5.1+). Imports PZ vanilla and modded assets (via the DirectX importer), previews clothing/props on a Bob rig, exports animations as .glb at 30 FPS with `Bob_` naming. Useful for visual attachment/pose preview in Blender and as a reference pipeline. Needs Blender 5.1+. GPL-3.0 plus a no-commercial-use legal note.
6. **PZModReload** (Lua-only hot reload, MIT). Speeds client Lua iteration; does NOT reload models, animations or scripts.
7. **RedChili's Bicycle / Kick Scooter / Skateboard (B42)**: closest prior art, items held in hand that trigger custom animations to look like riding. Code not on GitHub as far as found; study the installed Workshop files.
8. Policy: nothing new beyond the Community Rig Legal note (see problem 6).

## Problem 1: attachment preview/tuning

### Attachment script reference (PZ-API-Docs)
- URL: https://pz-wiki-modding.github.io/PZ-API-Docs/scripts/attachment.html
- What: `attachment <id>` block inside `model`/`template`/`vehicle`: `bone`, `offset` (x y z), `rotate` (x y z, degrees), `scale`, `zoffset` (undocumented). Lists Bip01_Prop1 among standard points. Recommends the Attachment Editor over hand edits.
- Helps: 1, 3 (the site's XML section lists animNode, clothing, clothingItem, clothingDecals, fileGuidTable; my guessed path /xml/clothingItem.html returned 404, so browse from the site index).
- Maturity: community-maintained, update date UNVERIFIED. Docs are internally inconsistent (rotation described under "offset" text, example uses `rotate`).
- Use: syntax sanity check; Scripts reference covers model, animation, anim, clip.

### Attachment Editor (in-game, debug)
- URL: https://pzwiki.net/wiki/Attachment_Editor (403 on fetch; existence known from the API docs link and search snippets).
- What: debug-menu tool (snippet lists Animation Viewer, Attachment Editor, Chunk Debugger). Enable debug by holding LShift at boot on Windows or adding `-debug` to launch options (pzwiki Debug mode snippet).
- Helps: 1, 5. UNVERIFIED: whether values apply live and whether it saves to the script.
- HorseMod (https://pz-horseteam.github.io/HorseMod/guides/attachmentsModding.html): the editor did not work for the horse because it had no custom AnimSet; they ship an "Attachments Editor Patch" that "isn't perfect". Same risk for our custom AnimSet/held models.
- Use: open it once with the pogo/tricycle model equipped in the riding pose and read the values; see whether the roll problem shows there.

### HorseMod attachment guide (Lua attachment API)
- URL: https://pz-horseteam.github.io/HorseMod/guides/attachmentsModding.html
- What: `AttachmentsAPI.addNewModelAttachment(name, {bone, offset, rotate})`, `addNewSlot`, `addNewAttachment` (HorseMod's own helpers, not vanilla). Says vanilla provides the tools to add/modify attachment points on model scripts from Lua, and advises not overriding the model script. Does not say whether this works at runtime.
- Helps: 1, 5. A Lua route to change attachment values at runtime is UNVERIFIED; check the ModelAttachment class in the PZ JavaDocs.

### AnimForge
See problem 2; its held-item grip adjustment is the strongest match for problem 1.

## Problem 2: animation/model authoring tools

### SaintBaron io_directx_x
- URL: https://github.com/SaintBaron/io_directx_x ; extension page https://extensions.blender.org/add-ons/io-directx-x/
- What: DirectX .x import and export: Frame hierarchy to armature, SkinWeights, animation F-curves; text/binary/MSZIP, 32/64-bit floats, `AnimTicksPerSecond = 4800` biped files. Export writes Frame tree, SkinWeights from vertex groups, baked pose-bone keys (quaternion tracks default, or 4x4 matrices). README lists PZ character and animation .x as "verified loading in-game".
- Version 1.3.1 (extensions page); Blender 4.2+ (we are on 4.1, would need an upgrade); GPL-3.0 (using it as a tool does not affect our files; copying its code into our repo needs a licence check).
- Helps: 2 (cross-check our writer), 1 (import vanilla .X to read real bone roll and Prop1 axes), 3 (skinned clothing .x).
- Use: import a vanilla Bob clip and our Bob_SkateIdle.X side by side; diff Frame transforms and tick rates against our exporter. Whether it understands the `Translation_Data` convention: UNVERIFIED.
- Older alternatives: https://github.com/oguna/Blender-XFileImporter (import only, BSD-style), https://github.com/littleneo/directX_blender (old). Not PZ-specific.

### Paddlefruit ProjectZomboid_CommunityRig
- URL: https://github.com/Paddlefruit/ProjectZomboid_CommunityRig (wiki at .../wiki)
- What: v4.0.1 per README; Blender 5.1+ rig of the PZ human with IK, animation export, direct import of vanilla and modded assets (Parse All Assets; needs the DirectX importer, 1.3.1 confirmed), clothing/outfit application (body textures, skinned meshes, bone-attached static props), pose library, rendering.
- Export: `.glb` (not .X) via "Export GLBs for Project Zomboid"; batch exports actions whose name contains `Bob_`; Blender project must be 30 FPS. Wiki "Hot Reloading" page claims animation files reload in game without restarting (no details on formats or setup).
- Helps: 1 (preview a prop on the rig in the riding pose in Blender, if the model imports), 2 (reference pipeline), 3, 5.
- Licence: GPL-3.0; Legal page: no commercial use without permission, The Indie Stone owns original armature/models/textures, extensions must credit Paddlefruit and link the repo.
- UNVERIFIED: how .glb relates to the .X/.fbx B42 loads (the wiki defers to pzwiki); whether Modded Assets import handles our held models/clips (only hair, outfits, skin/texture replacements are confirmed to work).

### AnimForge (in-game animation editor)
- URL: https://github.com/AlexVDefi/AnimForge
- What: B42, Windows. Delete key opens it in game: force-hold any clip, rotate/move bones with gizmos, add keyframes, scrub/play; equipped weapon is attached to the hand so grips can be adjusted; clip browser with 3D thumbnails; retime Gunworks reload markers. Bundled Python tool `pz-anim-forge` edits `.x` animations in place and keeps them .x, and generates AnimSet XML and a Lua hook. `watch.bat` auto-bakes saved changes into the mod; reload-marker edits hot-reload; new reload names need one restart.
- Requirements: Python 3, optional JDK 21+. Three prebuilt game classes install as loose files overriding the jar and must be reinstalled after each game update.
- Licence: MIT for its code; the prebuilt engine classes are TIS-derived, "modding context only" (their statement).
- Maturity: 29 commits, dates UNVERIFIED.
- Helps: 1, 2, 5. Risk: modifying game classes; judge before installing. UNVERIFIED that it handles our hand-written .X (Frame tree plus SkinWeights stub) or a rolled Prop1 for non-gun items.

### pzwiki pages (snippets only)
- https://pzwiki.net/wiki/Creating_custom_animations : action names should start `Bob_`; export script has "Export All Animations" and "Animation Filter"; in B42 only subfolders set by the model's `animationsMesh` are scanned for animations.
- https://pzwiki.net/wiki/Modeling : .fbx most common for animations/models and hot-reloaded automatically on update; DirectX .x labelled not recommended.
- https://pzwiki.net/wiki/AnimZed , https://pzwiki.net/wiki/AnimSet , https://pzwiki.net/wiki/Mystery_rig : exist; content UNVERIFIED. AnimZed is worth checking by hand (do not assume what it is).
- Steam guide "How Create an Animation": https://steamcommunity.com/sharedfiles/filedetails/?id=3035712003 (fetch got 429, not read; probably B41 era).

### Not found
- No standalone maintained "PZ model viewer" for character models/animations found. FWolfe's guide (https://github.com/FWolfe/Zomboid-Modding-Guide, WIP, tools section is a placeholder) mentions old Blender scripts for the B40 model format only.

## Problem 3: worn clothing with custom skinned models

- Little found. No tutorial covering `fileGuidTable` / `m_MaleModel` / skinned export surfaced. UNVERIFIED for anything specific.
- Best leads: PZ-API-Docs XML section (clothing, clothingItem, fileGuidTable) at https://pz-wiki-modding.github.io/PZ-API-Docs/ (browse from the index).
- Community Rig treats clothing meshes as skinned meshes that deform with the rig, and can import modded clothing; useful as a viewer for a mesh weighted to Bob bones.
- Practical method: read an existing B42 clothing mod's files from the Workshop folder (clothing xml, fileGuidTable entry, model) as the working reference; check its licence before copying anything.
- io_directx_x is the only add-on found that exports skinned .x.

## Problem 4: prior art mods

(All second-hand from author descriptions and search snippets, not code.)
- RedChili [B42] Bicycle!: https://steamcommunity.com/sharedfiles/filedetails/changelog/3461415167 . An item, not a vehicle; when held it triggers custom animations to look like riding; speed boost via mod options; Shout rings a bell; B41 version exists; listed b42.15+. Same author's bundle includes a skateboard and kick scooter (aggregator listing https://catalogue.smods.ru/?p=424772, treat with care).
- [B42] Kick Scooter: https://steamcommunity.com/sharedfiles/filedetails/changelog/3453879909 (changelog fetch got 429; details from search snippets). "A weapon you hold that activates custom animations"; same movement system as the skateboard; faster movement at no stamina cost; a March 31 update refactored animsets for compatibility; fixed animation issues when off the scooter (sneak, aim, guns).
- Skateboard: stack traces cite `Skateboard.lua`; ridable, throws you at high speed or on collision. An older Dislaik skateboard was delisted (search result claim).
- Braven's Bicycles Redux (B41-era): https://steamcommunity.com/sharedfiles/filedetails/changelog/2988491347 .
- Roller skates, stilts, unicycle, pogo stick: no Workshop mod found by search (maybe a real gap, maybe unindexed). UNVERIFIED.
- Use: confirms the held-item plus AnimSet approach we use. For attachment/stop/coast handling, subscribe and read their `media/AnimSets`, `media/scripts` and Lua for ideas (Workshop content belongs to the authors; do not copy). Stop/coast handling is not documented anywhere found.

## Problem 5: live reloading and debugging

- **Debug mode** (`-debug` launch option, or LShift at boot): F11 "Experimental Mod Reload" (`reloadLuaFile`) reloads one Lua file at a time, picked in game; its path map is fixed at startup so it cannot load files created mid-session (from a search snippet, UNVERIFIED on B42). Title-screen "Reset Lua" resets the Lua state; a mod "Enable Reset Lua Button [B41/B42]" is listed at https://catalogue.smods.ru/archives/424205 .
- **PZModReload**: https://github.com/deckard93/PZModReload . MIT, B42 only (folder `42.0`). Watches `media/reload.trigger` about once a second and re-runs the Lua files in `media/reload.filelist` via loadstring, including new files. Works SP, MP client, dedicated server (server skips `media/lua/client/`). Client reload only fires while unpaused. Needs reload-safe event handlers (remove before re-adding). Does NOT reload textures/icons, item/recipe .txt scripts, models, animations, translations. Last update UNVERIFIED (5 commits).
- **Animation files**: Community Rig "Hot Reloading" and the pzwiki Modeling snippet say animation files reload when saved; AnimForge hot-reloads reload-marker edits. Whether our hand-written .X clips hot-reload: UNVERIFIED, worth a 2 minute test (edit a key, save, watch).
- **Model script / attachment values at runtime**: no documented command found. Leads: Lua access to ModelAttachment (HorseMod hint), and the in-game Attachment Editor. The official JavaDocs/LuaDocs are linked from the PZ-API-Docs site (exact URL not verified here).
- **Typings**: Umbrella https://github.com/asledgehammer/Umbrella (EmmyLua/LuaCATS PZ API typings), pz-zdoc https://github.com/cocolabs/pz-zdoc ; B42 coverage and dates UNVERIFIED.

## Problem 6: licensing and policy (new findings only)

- Community Rig: GPL-3.0 code; Legal page says no commercial use without permission, original armature/models/textures belong to The Indie Stone, extensions must credit Paddlefruit and link the repo. Do not bundle its rig assets or any game skeleton in this repo.
- AnimForge: MIT code, but its prebuilt engine classes are TIS-derived and "modding context only" by its own statement.
- io_directx_x: GPL-3.0; use as a tool is fine, do not copy its code into this repo without a licence check.
- Nothing found on redistributing skeleton data in mod .X clips beyond what was already checked.

## Suggested next steps

1. Try the in-game Attachment Editor/Animation Viewer in debug mode first; read AnimForge's install script (engine patch) before installing it.
2. Test whether editing an existing .X clip hot-reloads in game (cheap, decides the iteration plan).
3. If a Blender 4.2+ install is acceptable, use io_directx_x to import vanilla and our clips and compare Frame tree, ticks and bone roll; this also answers the Prop1 roll question offline.
4. Read the pzwiki pages above in a normal browser (403 for us).

STATUS: DONE 2026-11-01
