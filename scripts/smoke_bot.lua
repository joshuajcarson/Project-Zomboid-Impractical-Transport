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
    local action = ISUnequipAction:new(p, item, 50)
    print("UNEQUIP maxTime=" .. tostring(action.maxTime) .. " dismount=" .. tostring(action.ipDismount) .. " fromHotbar=" .. tostring(action.fromHotbar))
    ISTimedActionQueue.add(action)
    return true, "queued"
end
-- smokeunequiptime|maxTime: unequip with that maxTime and log how long the action really lasts ("UNEQUIPTIME maxTime=.. real=.. ms")
commands.smokeunequiptime = function(p, a)
    local item = p:getPrimaryHandItem()
    if not item then return false, "nothing held" end
    local action = ISUnequipAction:new(p, item, 50)
    action.maxTime = tonumber(a and a.a) or action.maxTime
    local t0, requested = getTimestampMs(), action.maxTime
    local perform = action.perform
    action.perform = function(self) print("UNEQUIPTIME maxTime=" .. requested .. " real=" .. (getTimestampMs() - t0) .. " ms"); return perform(self) end
    ISTimedActionQueue.add(action)
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
        ISUIHandler.setVisibleAllUI(true)      -- the handler skips a hide it believes is done: a chat message pops the chat back up behind its back
        ISUIHandler.setVisibleAllUI(false)
        if ISChat and ISChat.instance then ISChat.instance:setVisible(false) end
        local before = getCore():getZoom(0)
        for _ = 1, math.abs(steps) do getCore():doZoomScroll(0, steps > 0 and -1 or 1) end
        print("smokeview zoom " .. tostring(before) .. " -> " .. tostring(getCore():getZoom(0)))
    end)
    return ok, tostring(err or "view set")
end
-- smokeui: bring the UI back
commands.smokeui = function(p, a) ISUIHandler.setVisibleAllUI(true); return true, "ui on" end

-- smokegait|walk|run|sprint: hold that gait every update (stands in for the run/sprint keys, which the bot cannot press)
local gaitHandler
commands.smokegait = function(p, a)
    local gait = (a and a.a) or "walk"
    if gaitHandler then Events.OnPlayerUpdate.Remove(gaitHandler); gaitHandler = nil end
    if gait ~= "walk" then
        gaitHandler = function(player)
            if player ~= p then return end
            player:setRunning(gait == "run"); player:setSprinting(gait == "sprint")
        end
        Events.OnPlayerUpdate.Add(gaitHandler)
    else
        p:setRunning(false); p:setSprinting(false)
    end
    return true, "gait " .. gait
end

-- smokestate: log the gait flags and the pogo speed variables the anim nodes read
commands.smokestate = function(p, a)
    print("STATE tier=" .. tostring(p:getVariableString("PogoTier")) .. " endurance=" .. tostring(p:getStats():get(CharacterStat.ENDURANCE)))
    print("STATE canSprint=" .. tostring(pcall(function() return p:canSprint() end) and p:canSprint()) .. " sprintDown=" .. tostring(pcall(function() return p:isSprintButtonDown() end) and p:isSprintButtonDown()) .. " runDown=" .. tostring(pcall(function() return p:isRunButtonDown() end) and p:isRunButtonDown()))
    -- what the engine cancels a sprint for (IsoPlayer.updateInternal2): walk speed under 1/3, walk injury over 0.5, in trees, no real movement input
    print(string.format("STATE sprintKeyRaw=%s walkSpeedVar=%s walkInjuryVar=%s inTrees=%s modSprintVar=%s",
        tostring(pcall(function() return isKeyDown(getCore():getKey(KeybindId.SPRINT)) end) and isKeyDown(getCore():getKey(KeybindId.SPRINT))),
        tostring(p:getVariableFloat("WalkSpeed", -1)), tostring(p:getVariableFloat("WalkInjury", -1)), tostring(p:isInTrees()), tostring(p:getVariableBoolean("PogoSprint"))))
    print(string.format("STATE running=%s sprinting=%s moving=%s walkVar=%s runVar=%s sprintVar=%s node=%s",
        tostring(p:isRunning()), tostring(p:isSprinting()), tostring(p:isPlayerMoving()), tostring(p:getVariableFloat("PogoWalkSpeed", -1)),
        tostring(p:getVariableFloat("PogoRunSpeed", -1)), tostring(p:getVariableFloat("PogoSprintSpeed", -1)), tostring(p:getAnimationDebug()):gsub("%s+", " "):sub(1, 160)))
    return true, "logged"
end

-- smokevar|Name|value (the harness splits arguments at '|' into a.a, a.b): pin an animation variable after the mod's own handler each update (value "off" releases it); experiments with the speed variables
local pinned = {}
local pinHandler
commands.smokevar = function(p, a)
    local name, value = a and a.a, (a and a.b) or ""
    pinned[name] = value ~= "" and (tonumber(value) or value) or nil      -- numbers stay numbers, anything else is a text value
    if not pinHandler then
        pinHandler = function(player)
            if player ~= p then return end
            for n, v in pairs(pinned) do player:setVariable(n, v) end
        end
        Events.OnPlayerUpdate.Add(pinHandler)
    end
    return true, "pinned " .. tostring(name) .. "=" .. tostring(pinned[name])
end

-- smokeprofile|field|value: change a field of the pogo stick's profile table live (e.g. walk|2.0); experiments only, a restart restores the file's values
commands.smokeprofile = function(p, a)
    local field, value = a and a.a, a and a.b
    local profile = ImpracticalTransport.getProfile(p)
    if not profile then return false, "no profile (stick not in hand)" end
    profile[field] = tonumber(value)
    return true, field .. "=" .. tostring(profile[field])
end

-- smokeanim: log the engine's full animation debug text for the player (which node plays, its track, speed and variables)
commands.smokeanim = function(p, a)
    print("ANIM " .. tostring(p:getAnimationDebug()):gsub("%s+", " "))
    return true, "logged"
end

-- smokespeeds: log the engine's movement speed numbers
commands.smokespeeds = function(p, a)
    local function try(f) local ok, v = pcall(f); return ok and tostring(v) or "ERR" end
    print("SPEEDS moveSpeed=" .. try(function() return p:getMoveSpeed() end) .. " speedMod=" .. try(function() return p:getSpeedMod() end)
        .. " movementSpeed=" .. try(function() return p:getMovementSpeed() end) .. " baseSpeed=" .. try(function() return p:calculateBaseSpeed() end)
        .. " slowFactor=" .. try(function() return p:getSlowFactor() end) .. " runMod=" .. try(function() return p:getRunSpeedModifier() end)
        .. " walkVar=" .. try(function() return p:getVariableFloat("WalkSpeed", -1) end))
    return true, "logged"
end
-- smokespeedmod|value: set the engine speed modifier (experiment)
commands.smokespeedmod = function(p, a) p:setSpeedMod(tonumber(a and a.a) or 1); return true, "speedMod " .. tostring(p:getSpeedMod()) end

-- smokeengine|call|value: set one engine speed control for experiments: movespeed, slowfactor (with a long slow timer)
commands.smokeengine = function(p, a)
    local call, value = a and a.a, tonumber(a and a.b)
    if call == "movespeed" then p:setMoveSpeed(value)
    elseif call == "slowfactor" then p:setSlowTimer(100000); p:setSlowFactor(value) end
    return true, call .. "=" .. tostring(value)
end

-- smokeendurance|value: set the endurance stat (0..1); with the pogo this moves the pace tier (below 0.5 tiredness slows the hop)
commands.smokeendurance = function(p, a)
    p:getStats():set(CharacterStat.ENDURANCE, tonumber(a and a.a) or 1)
    return true, "endurance " .. tostring(p:getStats():get(CharacterStat.ENDURANCE))
end

-- Repeatable test conditions: smokereset puts the character, weather, clock and surroundings into a fixed state (and keeps the clock there every update), smokecheck logs what it finds and fails if anything is off, so a measurement can be trusted.
local NEEDS = {"HUNGER", "THIRST", "FATIGUE", "STRESS", "BOREDOM", "UNHAPPINESS", "SICKNESS", "PAIN"}
local NOON, BODY_TEMP, CORPSE_RADIUS = 12, 37, 20
local resetHandler

local function corpsesNear(p, remove)
    local sq, count = p:getCurrentSquare(), 0
    if not sq then return 0 end
    local cell = getCell()
    for dx = -CORPSE_RADIUS, CORPSE_RADIUS do
        for dy = -CORPSE_RADIUS, CORPSE_RADIUS do
            local s = cell:getGridSquare(sq:getX() + dx, sq:getY() + dy, sq:getZ())
            local bodies = s and s:getDeadBodys()
            for i = (bodies and bodies:size() or 0) - 1, 0, -1 do
                count = count + 1
                if remove then s:removeCorpse(bodies:get(i), false) end
            end
        end
    end
    return count
end

commands.smokereset = function(p, a)
    local stats = p:getStats()
    for _, n in ipairs(NEEDS) do if CharacterStat[n] then stats:set(CharacterStat[n], 0) end end
    stats:set(CharacterStat.ENDURANCE, 1)
    if resetHandler then Events.OnPlayerUpdate.Remove(resetHandler) end
    resetHandler = function(player)
        if player ~= p then return end
        getGameTime():setTimeOfDay(NOON)
    end
    Events.OnPlayerUpdate.Add(resetHandler)
    return true, "reset, corpses removed " .. corpsesNear(p, true)
end

commands.smokecheck = function(p, a)
    local stats, inv, problems = p:getStats(), p:getInventory(), {}
    local function read(label, fn)      -- an API that does not exist is reported, not fatal
        local ok, v = pcall(fn)
        if ok and v ~= nil then return v end
        problems[#problems + 1] = "cannot read " .. label
        return 0
    end
    for _, n in ipairs(NEEDS) do
        local v = CharacterStat[n] and stats:get(CharacterStat[n]) or 0
        if v > 0.01 then problems[#problems + 1] = n:lower() .. "=" .. string.format("%.2f", v) end
    end
    local weight, cap = read("weight", function() return p:getInventoryWeight() end), read("capacity", function() return p:getMaxWeight() end)
    if weight > cap then problems[#problems + 1] = string.format("overweight %.1f/%.1f", weight, cap) end
    local temp, hour = read("temperature", function() return p:getBodyDamage():getThermoregulator():getCoreTemperature() end), read("hour", function() return getGameTime():getTimeOfDay() end)
    if math.abs(temp - BODY_TEMP) > 0.5 then problems[#problems + 1] = string.format("temperature=%.1f", temp) end
    if math.abs(hour - NOON) > 0.5 then problems[#problems + 1] = string.format("hour=%.1f", hour) end
    if read("rain", function() return getClimateManager():isRaining() end) == true then problems[#problems + 1] = "raining" end
    local corpses = read("corpses", function() return corpsesNear(p, false) end)
    if corpses > 0 then problems[#problems + 1] = "corpses=" .. corpses end
    local report = string.format("temp=%.1f hour=%.1f weight=%.1f/%.1f endurance=%.2f corpses=%d", temp, hour, weight, cap, stats:get(CharacterStat.ENDURANCE), corpses)
    if #problems > 0 then report = report .. " PROBLEMS " .. table.concat(problems, ", ") end
    print("SMOKECHECK " .. report)
    return #problems == 0, report
end

-- smokeweather|free: log whether it is raining (free = drop the client-side overrides first, so the server's weather shows)
commands.smokeweather = function(p, a)
    local clim = getClimateManager()
    if a and a.a == "free" then for _, f in ipairs({3, 5}) do clim:getClimateFloat(f):setEnableOverride(false) end end
    local function read(fn) local ok, v = pcall(fn); if not ok or v == nil then return "?" end return type(v) == "number" and string.format("%.2f", v) or tostring(v) end
    local msg = string.format("WEATHER raining=%s snowing=%s storm=%s precip=%s fog=%s wind=%s temp=%s running=%s",
        read(function() return clim:isRaining() end), read(function() return clim:isSnowing() end),
        read(function() return clim:getThunderStorm():isRunning() end), read(function() return clim:getClimateFloat(3):getInternalValue() end),
        read(function() return clim:getClimateFloat(5):getInternalValue() end), read(function() return clim:getClimateFloat(6):getInternalValue() end),
        read(function() return clim:getAirTemperatureForCharacter(p) end), read(function() return clim:getWeatherPeriod():isRunning() end))
    print(msg)
    return true, msg
end

-- smokeslip: force a pedal slip on the held tricycle or unicycle (logs "ImpracticalTransport slip")
commands.smokeslip = function(p, a)
    local profile = ImpracticalTransport.getProfile(p)
    if not (profile and profile.slip) then return false, "no slipping transport in hand" end
    ImpracticalTransport.slip(p, profile)
    return true, "slip"
end

-- smokescan|radius: count the ground types (as the mod classifies them) and bushes or trees around the player and log the first square of each as "SCAN <type> n=<count> first=<x>,<y>"
commands.smokescan = function(p, a)
    local r = tonumber(a and a.a) or 40
    local cell, px, py = getCell(), math.floor(p:getX()), math.floor(p:getY())
    local seen, order = {}, {}
    for dx = -r, r do
        for dy = -r, r do
            local sq = cell:getGridSquare(px + dx, py + dy, 0)
            if sq then
                local g = ImpracticalTransport.groundAt(sq)
                local keys = { tostring(g[1] or "neutral") }
                if sq:HasTree() then keys[#keys + 1] = "TREE" end
                if sq:getBush() ~= nil then keys[#keys + 1] = "BUSH" end
                for _, key in ipairs(keys) do
                    if not seen[key] then seen[key] = { n = 0, x = px + dx, y = py + dy }; order[#order + 1] = key end
                    seen[key].n = seen[key].n + 1
                end
            end
        end
    end
    for _, key in ipairs(order) do print(string.format("SCAN %s n=%d first=%d,%d", key, seen[key].n, seen[key].x, seen[key].y)) end
    return true, "scanned " .. #order .. " kinds"
end

-- smokewear|Type: wear a clothing item from the inventory like a player (a real timed action)
commands.smokewear = function(p, a)
    local item = p:getInventory():getFirstTypeRecurse((a and a.a) or "")
    if not item then return false, "not in inventory" end
    ISTimedActionQueue.add(ISWearClothing:new(p, item, 50))
    return true, "queued"
end

-- smokeworn: log what is worn and the transport variables ("WORN <type> ... SkatesActive=..")
commands.smokeworn = function(p, a)
    local worn = p:getWornItems()
    local names = {}
    for i = 0, worn:size() - 1 do names[#names + 1] = tostring(worn:get(i):getItem():getFullType()) end
    print("WORN " .. table.concat(names, " ") .. " SkatesActive=" .. tostring(p:getVariableBoolean("SkatesActive")) .. " profile=" .. tostring(ImpracticalTransport.getProfile(p) and ImpracticalTransport.getProfile(p).name))
    return true, "logged"
end

-- smokeunwear|Type: take a worn clothing item off like a player (a real unequip action)
commands.smokeunwear = function(p, a)
    local item = p:getInventory():getFirstTypeRecurse((a and a.a) or "")
    if not item then return false, "not in inventory" end
    ISTimedActionQueue.add(ISUnequipAction:new(p, item, 50))
    return true, "queued"
end

-- smokeattach|ModelName|ox,oy,oz,rx,ry,rz: LIVE attachment tuner. Sets the offset and rotate of a model script's Bip01_Prop1 attachment in the running game (the same
-- Vector3f objects the vanilla debug attachment editor edits); no value = just log the current ones. ModelName without the module is looked up in Base ("Unicycle_3d").
commands.smokeattach = function(p, a)
    local name = (a and a.a) or "Unicycle_3d"
    if not name:find(".", 1, true) then name = "Base." .. name end
    local script = getScriptManager():getModelScript(name)
    if not script then return false, "no model script " .. name end
    local attach = script:getAttachmentById("Bip01_Prop1")
    if not attach then return false, "no Bip01_Prop1 attachment on " .. name end
    local v = a and a.b
    if v and v ~= "" then
        local n = {}
        for x in tostring(v):gmatch("[^,]+") do n[#n + 1] = tonumber(x) end
        if #n ~= 6 then return false, "need ox,oy,oz,rx,ry,rz" end
        attach:getOffset():set(n[1], n[2], n[3])
        attach:getRotate():set(n[4], n[5], n[6])
    end
    local o, r = attach:getOffset(), attach:getRotate()
    local msg = string.format("ATTACH %s offset %.4f %.4f %.4f rotate %.4f %.4f %.4f", name, o:x(), o:y(), o:z(), r:x(), r:y(), r:z())
    print(msg)
    return true, msg
end

-- smokecars|radius|remove: log the vehicles within `radius` tiles of the player ("CARS n=.. at x,y ..."); with a second argument `remove` also ask the server to remove them
-- (the vanilla vehicle command "remove", the one the debug menu uses), so a test walk is not blocked by parked cars.
commands.smokecars = function(p, a)
    local r = tonumber(a and a.a) or 30
    local found, removed = {}, 0
    local it = getCell():getVehicles():iterator()      -- not an ArrayList: no get(), iterate it
    while it:hasNext() do
        local v = it:next()
        local sq = v:getSquare() or v:getCurrentSquare()
        if sq and math.abs(sq:getX() - p:getX()) <= r and math.abs(sq:getY() - p:getY()) <= r then
            found[#found + 1] = string.format("%d@%d,%d", v:getId(), sq:getX(), sq:getY())
            if a and a.b == "remove" then
                sendClientCommand(p, "vehicle", "remove", { vehicle = v:getId() })
                removed = removed + 1
            end
        end
    end
    local msg = string.format("CARS n=%d removed=%d %s", #found, removed, table.concat(found, " "))
    print(msg)
    return true, msg
end

-- smokecalm|1/0: no random slips or stumbles (speed measurements); forced ones (smokeslip, smokestumble) still happen
commands.smokecalm = function(p, a)
    ImpracticalTransport.calm = (a and a.a) ~= "0"
    return true, "calm " .. tostring(ImpracticalTransport.calm)
end

-- smokeground|class|off: make the mod see that ground under the rider (a SURFACES pattern such as sand, road_, or neutral), whatever tile is really there; only works while
-- smokecalm is on, so normal play never sees it. "off" (or no argument) releases it.
commands.smokeground = function(p, a)
    local class = a and a.a
    if not class or class == "" or class == "off" then ImpracticalTransport.forceGround = nil; return true, "ground released" end
    if not ImpracticalTransport.calm then return false, "needs smokecalm 1 first" end
    ImpracticalTransport.forceGround = class
    return true, "ground forced to " .. class
end

-- smokehold|value: keep endurance at that level every update (god mode refills it), so the winded-rider tiers can be tested; no value = stop holding
local holdHandler
commands.smokehold = function(p, a)
    if holdHandler then Events.OnPlayerUpdate.Remove(holdHandler); holdHandler = nil end
    local v = tonumber(a and a.a)
    if not v then return true, "hold off" end
    holdHandler = function(player) if player == p then player:getStats():set(CharacterStat.ENDURANCE, v) end end
    Events.OnPlayerUpdate.Add(holdHandler)
    return true, "holding endurance at " .. v
end

-- smokenode|ticks: log which anim node plays, once per change, for `ticks` updates ("NODE <tick> <node> <clip> transition=<PogoTransition> active=<PogoActive>")
commands.smokenode = function(p, a)
    local left, tick, last = tonumber(a and a.a) or 300, 0, nil
    local function sample(player)
        if player ~= p then return end
        tick = tick + 1
        local d = tostring(player:getAnimationDebug())
        local node, clip = d:match("Node: (%S+)"), d:match("Anim: (%S+)")
        local key = tostring(node) .. "/" .. tostring(clip) .. "/" .. tostring(player:getVariableString("PogoTransition")) .. "/" .. tostring(player:getVariableBoolean("PogoActive"))
        if key ~= last then last = key; print("NODE " .. tick .. " t=" .. getTimestampMs() .. " " .. key) end
        if tick >= left then Events.OnPlayerUpdate.Remove(sample) end
    end
    Events.OnPlayerUpdate.Add(sample)
    return true, "sampling " .. left
end

-- smokeinv: log the mod's items in the inventory
commands.smokeinv = function(p, a)
    local names, items = {}, p:getInventory():getItems()
    for i = 0, items:size() - 1 do
        local t = items:get(i):getFullType()
        if t:find("ImpracticalTransport", 1, true) then names[#names + 1] = t:gsub("ImpracticalTransport%.", "") end
    end
    print("INV " .. table.concat(names, " "))
    return true, "logged"
end

-- smokeloot|ListName|ref: the chance per container of each of our items and of a vanilla reference item in the merged procedural list, by the game's own formula
-- (the admin LootZed spawn-rate tool: per roll weight * ItemPickerJava.getLootModifier / 100, over the list's rolls). Logs "LOOT list rolls=.. Item=pct% ..".
commands.smokeloot = function(p, a)
    local list, ref = (a and a.a) or "CrateToys", (a and a.b) or "Base.Doll"
    local dist = ProceduralDistributions.list[list]
    if not dist then return false, "no list " .. list end
    local out, rolls = {}, dist.rolls
    for i = 1, #dist.items, 2 do
        local name, w = dist.items[i], dist.items[i + 1]
        if name:find("ImpracticalTransport", 1, true) or name == ref then
            local chance = w * ItemPickerJava.getLootModifier(name) / 100
            out[#out + 1] = string.format("%s=%.1f%%", name:gsub("^.-%.", ""), 100 * (1 - (1 - chance) ^ rolls))
        end
    end
    local msg = "LOOT " .. list .. " rolls=" .. rolls .. " " .. table.concat(out, " ")
    print(msg)
    return true, msg
end

-- smokescan|x|y|radius: count the containers in the loaded squares around x,y (all floors) by room, and list our items found inside them.
-- Logs one "SCAN room containers=.. withOurs=.." line per room and a "SCANHIT room container x,y,z Item" line per item. Use after smokechat /teleportto.
commands.smokescan = function(p, a)
    local cx, cy, r = tonumber(a and a.a) or p:getX(), tonumber(a and a.b) or p:getY(), tonumber(a and a.c) or 40
    local cell, rooms, total, squares = getCell(), {}, 0, 0
    local objs, inroom
    for z = 0, 3 do for x = cx - r, cx + r do for y = cy - r, cy + r do
        local sq = cell:getGridSquare(x, y, z)
        if sq then
            squares = squares + 1
            if z == 0 then objs = (objs or 0) + sq:getObjects():size(); if sq:getRoom() then inroom = (inroom or 0) + 1 end end
            local room = sq:getRoom() and sq:getRoom():getName() or "outside"
            for i = 0, sq:getObjects():size() - 1 do
                local c = sq:getObjects():get(i):getContainer()
                if c then
                    local rec = rooms[room] or {n = 0, ours = 0}; rooms[room] = rec
                    rec.n, total = rec.n + 1, total + 1
                    local hit = false
                    for k = 0, c:getItems():size() - 1 do
                        local t = c:getItems():get(k):getFullType()
                        if t:find("ImpracticalTransport", 1, true) then
                            hit = true; print(string.format("SCANHIT %s %s %d,%d,%d %s", room, c:getType(), x, y, z, t))
                        end
                    end
                    if hit then rec.ours = rec.ours + 1 end
                end
            end
        end
    end end end
    for room, rec in pairs(rooms) do print(string.format("SCAN %s containers=%d withOurs=%d", room, rec.n, rec.ours)) end
    local msg = "SCAN total containers=" .. total .. " squares=" .. squares .. " z0objs=" .. tostring(objs) .. " inRoom=" .. tostring(inroom) .. " at=" .. cx .. "," .. cy .. " player=" .. math.floor(p:getX()) .. "," .. math.floor(p:getY()) .. "," .. p:getZ()
    print(msg); return true, msg
end

-- smokesound|Name: play a sound script on the player and log the emitter handle (0 or error = the sound is not registered / its clip is missing)
commands.smokesound = function(p, a)
    local name = (a and a.a) or "ImpracticalTransportPogoBounce"
    local ok, h = pcall(function() return p:getEmitter():playSound(name) end)
    local known = pcall(function() return GameSounds.isKnownSound(name) end) and tostring(GameSounds.isKnownSound(name)) or "n/a"
    local gs = pcall(function() return GameSounds.getSound(name) end) and GameSounds.getSound(name)
    local clips = gs and gs.clips and tostring(gs.clips:size()) or "n/a"
    local msg = "SOUND known=" .. known .. " clips=" .. clips .. " " .. name .. " handle=" .. tostring(h) .. " ok=" .. tostring(ok) .. " playing=" .. tostring(ok and p:getEmitter():isPlaying(name))
    print(msg); return true, msg
end

-- smokeslowprobe: log the inputs of the mod's vanillaSlowdown() (trees variable, slow factor, slow timer) while moving
commands.smokeslowprobe = function(p, a)
    local function try(f) local ok, v = pcall(f); return ok and tostring(v) or "ERR" end
    local msg = "SLOWPROBE trees=" .. try(function() return p:getVariableFloat("WalkSpeedTrees", 1) end) .. " slowFactor=" .. try(function() return p:getSlowFactor() end)
        .. " slowTimer=" .. try(function() return p:getSlowTimer() end) .. " inTrees=" .. try(function() return p:isInTrees() end) .. " moving=" .. try(function() return p:isPlayerMoving() end)
    print(msg); return true, msg
end
