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
-- smokeunequip: empty both hands (for a no-item speed baseline)
commands.smokeunequip = function(p, a)
    p:setPrimaryHandItem(nil); p:setSecondaryHandItem(nil)
    return true, "hands empty"
end
