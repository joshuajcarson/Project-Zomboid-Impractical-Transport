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

-- smokebones|ticks: log the model-space transform of the bones that matter for the pogo pose, once per update for `ticks` updates.
-- Lines read "BONES <tick> <bone> <matrix text>" (translation = the 4th column); the model space is the character's own frame.
-- shortcut: depends on AnimationPlayer:getSkinningBoneIndex / getModelTransformAt being callable from Lua; each failure is logged once.
local BONES = { "Bip01_Pelvis", "Bip01_Head", "Bip01_R_Hand", "Bip01_L_Hand", "Bip01_Prop1", "Bip01_Prop2", "Bip01_R_Foot", "Bip01_L_Foot" }
commands.smokebones = function(p, a)
    local left, tick = tonumber(a and a.a) or 60, 0
    local failed = {}
    local function sample(player)
        if player ~= p then return end
        tick = tick + 1
        local ok, err = pcall(function()
            local ap = player:getAnimationPlayer()
            for _, name in ipairs(BONES) do
                local idx = ap:getSkinningBoneIndex(name, -1)
                if idx >= 0 then
                    print("BONES " .. tick .. " " .. name .. " " .. tostring(ap:getModelTransformAt(idx)):gsub("%s+", " "))
                elseif not failed[name] then failed[name] = true; print("BONES missing bone " .. name) end
            end
        end)
        if not ok and not failed.all then failed.all = true; print("BONES failed: " .. tostring(err)) end
        if tick >= left or failed.all then Events.OnPlayerUpdate.Remove(sample) end
    end
    Events.OnPlayerUpdate.Add(sample)
    return true, "sampling " .. left
end

-- smokeview|zoomsteps: hide every UI panel and zoom the camera in (negative steps zoom out), so a screen capture shows the rider and nothing else
commands.smokeview = function(p, a)
    local steps = tonumber(a and a.a) or 6
    local ok, err = pcall(function()
        ISUIHandler.setVisibleAllUI(false)
        local before = getCore():getZoom(0)
        for _ = 1, math.abs(steps) do getCore():doZoomScroll(0, steps > 0 and -1 or 1) end
        print("smokeview zoom " .. tostring(before) .. " -> " .. tostring(getCore():getZoom(0)))
    end)
    return ok, tostring(err or "view set")
end
-- smokeui: bring the UI back
commands.smokeui = function(p, a) ISUIHandler.setVisibleAllUI(true); return true, "ui on" end
