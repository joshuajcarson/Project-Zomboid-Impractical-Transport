-- Rider state is derived from the equipped item each tick, so no saved state to migrate across patches.
ImpracticalTransport = ImpracticalTransport or {}

local RIDEABLE = { ["ImpracticalTransport.PogoStick"] = true }

function ImpracticalTransport.getRidden(player)
    local item = player:getPrimaryHandItem()
    return item and RIDEABLE[item:getFullType()] and item or nil
end

-- shortcut: logs only; real hop/speed behaviour needs in-game tuning, see README.
Events.OnPlayerUpdate.Add(function(player)
    local riding = ImpracticalTransport.getRidden(player) ~= nil
    player:setVariable("ImpracticalRiding", riding)
end)
