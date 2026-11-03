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


## Chances per container (measured with the game's own formula, 2026-11-03)
Vanilla procedural weights are percent per roll, not shares of a total: the admin LootZed spawn-rate tool computes `1 - (1 - weight * lootModifier / 100) ^ rolls` per container, and `lootModifier` is 0.6 for our items (confirmed by `smokeloot` in game). So vanilla dolls and bears (weight 20) turn up in about 40 percent of toy crates; our weights are set against that. Check any list in a running game with `python scripts/live.py bot smokeloot <List>` (it logs `LOOT list rolls=.. Item=pct%`); `scripts/loot_vanilla_report.py` prints the vanilla weights next to ours.

| list | rolls | item | weight | chance per container |
|---|---|---|---|---|
| BedroomDresserChild | 4 | RollerSkates | 3 | 7.0% |
| BedroomDresserChild | 4 | PogoStick | 3 | 7.0% |
| BedroomDresserChild | 4 | Tricycle | 1.5 | 3.6% |
| WardrobeChild | 4 | RollerSkates | 2.5 | 5.9% |
| WardrobeChild | 4 | PogoStick | 2 | 4.7% |
| WardrobeChild | 4 | Tricycle | 1 | 2.4% |
| CrateToys | 4 | PogoStick | 10 | 21.9% |
| CrateToys | 4 | Tricycle | 6 | 13.6% |
| CrateToys | 4 | RollerSkates | 6 | 13.6% |
| GiftStoreToys | 4 | PogoStick | 10 | 21.9% |
| GiftStoreToys | 4 | Tricycle | 6 | 13.6% |
| GiftStoreToys | 4 | RollerSkates | 5 | 11.5% |
| GiftStoreToys | 4 | Unicycle | 1 | 2.4% |
| GigamartToys | 4 | PogoStick | 10 | 21.9% |
| GigamartToys | 4 | Tricycle | 6 | 13.6% |
| GigamartToys | 4 | RollerSkates | 5 | 11.5% |
| GigamartToys | 4 | Unicycle | 1 | 2.4% |
| SportStoreSneakers | 4 | RollerSkates | 10 | 21.9% |
| SportStoreAccessories | 4 | RollerSkates | 8 | 17.9% |
| SportStoreAccessories | 4 | PogoStick | 4 | 9.3% |
| SportStoreAccessories | 4 | Unicycle | 1 | 2.4% |
| ClosetSportsEquipment | 2 | RollerSkates | 6 | 7.1% |
| ClosetSportsEquipment | 2 | PogoStick | 4 | 4.7% |
| ClosetSportsEquipment | 2 | Unicycle | 0.5 | 0.6% |
| SchoolGymSportsGear | 4 | RollerSkates | 6 | 13.6% |
| SchoolGymSportsGear | 4 | PogoStick | 4 | 9.3% |
| SchoolGymSportsGear | 4 | Unicycle | 0.5 | 1.2% |
| CrateSports | 4 | RollerSkates | 8 | 17.9% |
| CrateSports | 4 | PogoStick | 4 | 9.3% |
| CrateSports | 4 | Unicycle | 1 | 2.4% |
| ClosetShelfGeneric | 2 | RollerSkates | 1 | 1.2% |
| ClosetShelfGeneric | 2 | PogoStick | 1 | 1.2% |
| ClosetShelfGeneric | 2 | Tricycle | 0.5 | 0.6% |
| CrateRandomJunk | 1 | RollerSkates | 0.5 | 0.3% |
| CrateRandomJunk | 1 | PogoStick | 0.5 | 0.3% |
| CrateRandomJunk | 1 | Tricycle | 0.5 | 0.3% |
| CrateRandomJunk | 1 | Unicycle | 0.1 | 0.1% |
