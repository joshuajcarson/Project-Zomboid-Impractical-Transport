# Getting the items (loot)

No recipes: the pogo stick, tricycle, unicycle and roller skates are plain loot. `media/lua/server/ImpracticalTransportLoot.lua` appends them to vanilla `ProceduralDistributions.list[...]` entries in `Events.OnPreDistributionMerge`. It is server-side code, so it works in singleplayer and on a dedicated server (containers are filled by the server when a chunk first loads; clients need nothing). Only containers generated after the mod is enabled get the items; already-looted chunks of an old save will not.

Weights (vanilla scale: higher = more often; vanilla junk is about 2 to 20, rare finds 0.01 to 0.5). The table lives at the top of the Lua file.

| Where | Skates | Pogo | Tricycle | Unicycle |
|---|---|---|---|---|
| BedroomDresserChild (kids' dressers) | 3 | 2 | 1 | |
| WardrobeChild | 2 | 1.5 | 0.7 | |
| CrateToys | 3 | 4 | 3 | |
| GiftStoreToys, GigamartToys | 3 | 4 | 2 | 0.3 |
| ClosetSportsEquipment | 4 | 3 | | 0.5 |
| SchoolGymSportsGear | 3 | 2 | | 0.5 |
| CrateSports | 3 | | | 0.5 |
| SportStoreSneakers | 4 | | | |
| ClosetShelfGeneric (home closets) | 1 | 1 | 0.5 | |
| CrateRandomJunk | 0.5 | 0.5 | 0.5 | 0.1 |

Intent: skates and pogo are the common ones (kids' rooms, toy and sport places), the tricycle shows up in toy places and kids' rooms but less, the unicycle only in sport/toy stock and rarely. Tune by editing the numbers.

The list names were checked against the Build 42 install; `scripts/loot_list_names.txt` is our own copy of the names we use, and `scripts/check_repo.py` fails if the Lua uses a list not in it or an item not in `ImpracticalTransport_items.txt`. A name that does not exist in the game only prints `[ImpracticalTransport] loot list not found` in the log.

## Testing (needs a game run)
Bot command `smokeloot|<ListName>|<n>` (in `scripts/smoke_bot.lua`) rolls the list n times into fresh containers and logs `LOOT <list> n=.. PogoStick=.. ...`, the number of containers that held each item. Not run yet. Example: `smokeloot|CrateToys|1000`, then compare with the weights; also check the log for "loot list not found". A real walk-through (find one in a kids' bedroom in a fresh save) is a human test.
