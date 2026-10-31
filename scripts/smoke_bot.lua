-- Appended to the RL harness's client-side rl_bot_dev.lua by smoke_test.py (the `commands` table and `log` come from there).
-- smokeoutfit: put on basic clothes. A server-side AddItem never reaches a real client, so this runs on the client.
commands.smokeoutfit = function(p, a)
    local worn = 0
    for _, t in ipairs({ "Base.Tshirt_DefaultTEXTURE", "Base.Trousers_DefaultTEXTURE", "Base.Socks_Ankle", "Base.Shoes_TrainerTINT" }) do
        local ok, err = pcall(function()
            local it = p:getInventory():AddItem(t)
            p:setWornItem(it:getBodyLocation(), it)
            worn = worn + 1
        end)
        if not ok then log("smokeoutfit " .. t .. ": " .. tostring(err)) end
    end
    return true, "worn " .. worn
end

-- smokechat|/command ...: type an admin chat command (e.g. /addvehicle "Base.Tricycle" "Smoke1"); needs the admin role (server `admin|user`).
-- shortcut: drives ISChat's own entry path; unverified in B42.21, logs the error if the UI shape changed.
commands.smokechat = function(p, a)
    local ok, err = pcall(function()
        ISChat.instance.textEntry:setText((a and a.a) or "")
        ISChat.onCommandEntered()
    end)
    if not ok then log("smokechat failed: " .. tostring(err)) end
    return ok, tostring(err or "sent")
end

-- the harness re-equips its weapon whenever the hands are empty; turn that off so items can be put away by hand
RL.autoRearm = false
-- smokeunequipaction: put the held item away the way a player does (a real timed action); smokehands then reports the result in the log
commands.smokeunequipaction = function(p, a)
    local item = p:getPrimaryHandItem()
    if not item then return false, "nothing held" end
    ISTimedActionQueue.add(ISUnequipAction:new(p, item, 50))
    return true, "queued"
end
commands.smokehands = function(p, a)
    return p:getPrimaryHandItem() == nil, "hands " .. (p:getPrimaryHandItem() and "full" or "empty")
end

-- smokeequipaction|Type: equip like a player (a real timed action, which the server validates against ITS copy of the item)
commands.smokeequipaction = function(p, a)
    local item = p:getInventory():getFirstTypeRecurse((a and a.a) or "PogoStick")
    if not item then return false, "not in inventory" end
    ISTimedActionQueue.add(ISEquipWeaponAction:new(p, item, 50, true, item:isTwoHandWeapon()))
    return true, "queued"
end

-- smokeclear|Type: drop every copy of an item from this client's inventory (hands are left to real actions) (earlier runs left client-only copies that the server rejects)
commands.smokeclear = function(p, a)
    p:getInventory():RemoveAll((a and a.a) or "PogoStick")
    return true, "cleared"
end

-- smokestumble: force the stumble the rider would otherwise get by chance (the mod's own function, so its variables are the ones tested)
commands.smokestumble = function(p, a)
    local ok, err = pcall(ImpracticalTransport.stumble, p)
    return ok, tostring(err or "stumbled")
end
