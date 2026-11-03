-- Loot: adds our four items to vanilla procedural container lists. Numbers are the vanilla item weights (higher = more often; vanilla common junk is ~2-20, rare ~0.01-0.5).
-- One line per list; scripts/check_repo.py checks each list name against scripts/loot_list_names.txt and each item against ImpracticalTransport_items.txt.
require "Items/ProceduralDistributions"

local PLACES = {
    -- kids' rooms
    BedroomDresserChild = { RollerSkates = 3, PogoStick = 3, Tricycle = 1.5 },
    WardrobeChild = { RollerSkates = 2.5, PogoStick = 2, Tricycle = 1 },
    -- toy stores: as common as the vanilla toys there (dolls, bears and bricks are 10-20)
    CrateToys = { PogoStick = 10, Tricycle = 6, RollerSkates = 6 },
    GiftStoreToys = { PogoStick = 10, Tricycle = 6, RollerSkates = 5, Unicycle = 1 },
    GigamartToys = { PogoStick = 10, Tricycle = 6, RollerSkates = 5, Unicycle = 1 },
    -- sports: skates sit with the other shoes (vanilla trainers are 10 each)
    SportStoreSneakers = { RollerSkates = 10 },
    SportStoreAccessories = { RollerSkates = 8, PogoStick = 4, Unicycle = 1 },
    ClosetSportsEquipment = { RollerSkates = 6, PogoStick = 4, Unicycle = 0.5 },
    SchoolGymSportsGear = { RollerSkates = 6, PogoStick = 4, Unicycle = 0.5 },
    CrateSports = { RollerSkates = 8, PogoStick = 4, Unicycle = 1 },
    -- house storage, garages, junk
    ClosetShelfGeneric = { RollerSkates = 1, PogoStick = 1, Tricycle = 0.5 },
    CrateRandomJunk = { RollerSkates = 0.5, PogoStick = 0.5, Tricycle = 0.5, Unicycle = 0.1 },
}

local function addLoot()
    for list, items in pairs(PLACES) do
        local dist = ProceduralDistributions.list[list]
        if dist then
            for item, weight in pairs(items) do
                table.insert(dist.items, "ImpracticalTransport." .. item)
                table.insert(dist.items, weight)
            end
        else
            print("[ImpracticalTransport] loot list not found: " .. list)
        end
    end
end

Events.OnPreDistributionMerge.Add(addLoot)
