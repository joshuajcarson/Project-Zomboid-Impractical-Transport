-- Loot: adds our four items to vanilla procedural container lists. Numbers are the vanilla item weights (higher = more often; vanilla common junk is ~2-20, rare ~0.01-0.5).
-- One line per list; scripts/check_repo.py checks each list name against scripts/loot_list_names.txt and each item against ImpracticalTransport_items.txt.
require "Items/ProceduralDistributions"

local PLACES = {
    -- kids' rooms
    BedroomDresserChild = { RollerSkates = 3, PogoStick = 2, Tricycle = 1 },
    WardrobeChild = { RollerSkates = 2, PogoStick = 1.5, Tricycle = 0.7 },
    -- toys and sport
    CrateToys = { PogoStick = 4, Tricycle = 3, RollerSkates = 3 },
    GiftStoreToys = { PogoStick = 4, Tricycle = 2, RollerSkates = 3, Unicycle = 0.3 },
    GigamartToys = { PogoStick = 4, Tricycle = 2, RollerSkates = 3, Unicycle = 0.3 },
    ClosetSportsEquipment = { RollerSkates = 4, PogoStick = 3, Unicycle = 0.5 },
    SchoolGymSportsGear = { RollerSkates = 3, PogoStick = 2, Unicycle = 0.5 },
    CrateSports = { RollerSkates = 3, Unicycle = 0.5 },
    SportStoreSneakers = { RollerSkates = 4 },
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
