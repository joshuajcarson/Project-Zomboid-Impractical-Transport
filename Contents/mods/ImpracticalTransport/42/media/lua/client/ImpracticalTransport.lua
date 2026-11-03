-- Rider state is derived from the equipped item each tick, so no saved state to migrate across patches.
-- Each transport's anim nodes (AnimSets/player/*/<kind>_*.xml, written by tools/make_gait_nodes.py) play only while <Name>Active is true and pick their
-- clip tier from <Name>Tier, both set here; a profile's `name` is Pogo or Trike. `mount` says the transport has mount and dismount clips.
ImpracticalTransport = ImpracticalTransport or {}

-- speed lives in the clips (tools/blender/pogo_hop.py: DISTANCE, GAITS, TIERS), not here
-- tier1, tier2: pace (tiredness x terrain x engine slowdown) under which the slower hop clips play; dirt and grass stay at full pace
-- speed: tiles per second at full pace (tier 0) by gait, measured from the clips; only used for the expectation printed in the pace log
-- drain: endurance lost per second while moving, times drainRun / drainSprint when running or sprinting
-- stumble: chance per second of tripping while fresh (about one fall every 80 s of hopping; winded riders trip up to 5x as often),
--   times stumbleRun / stumbleSprint: faster hopping falls much more than it speeds up
local PROFILES = {
    ["ImpracticalTransport.PogoStick"] = {
        name = "Pogo", mount = true,
        speed = { [""] = 0.86, Run = 1.6, Sprint = 2.0 },      -- Sprint is an estimate from the clip factors (2.2 against run 1.7), not yet measured
        tier1 = 0.8, tier2 = 0.5,
        drain = 0.0035, drainRun = 1.6, drainSprint = 2.5,
        stumble = 0.0125, stumbleRun = 3.0, stumbleSprint = 6.0,
    },
    -- a child's tricycle under a grown rider: slow and tiring, but it rarely throws the rider
    ["ImpracticalTransport.Tricycle"] = {
        name = "Trike", mount = true, transitionSeconds = 1.1,
        dismount = { time = 105 },      -- see the unicycle
        speed = { [""] = 0.58, Run = 0.78 },
        slip = 0.03, slipRun = 2.0, slipSeconds = { 1.0, 2.0 }, slipFall = 0.25,      -- pedal slip: chance per second, run multiplier, how long it lasts; slipFall: share of slips that tip over backwards
        tier1 = 0.8, tier2 = 0.5,
        drain = 0.003, drainRun = 1.5, drainSprint = 1.5,
        stumble = 0.0015, stumbleRun = 3.0, stumbleSprint = 3.0,      -- falling back off the seat is rare; slipping is the common failure
    },
    -- roller skates are WORN (shoes slot), not held: no aiming block, no mount clips; speed and falls like the others
    ["ImpracticalTransport.RollerSkates"] = {
        name = "Skates", worn = true, mount = false,
        paved = 2.6, tierFast = 1.4,      -- on pavement: speed x2.6 (a little faster than bare walking), the "F" clips
        speed = { [""] = 0.7, Run = 1.0 },
        stopFall = { walk = 0.05, run = 0.25 },      -- chance that stopping ends in a fall (winded riders and bad ground make it likelier)
        coast = { walk = 0.6, run = 1.2 },      -- seconds the rider keeps gliding after the keys are released: the length of Bob_SkateCoast / Bob_SkateCoastRun (tools/blender/skates_glide.py), which start at the skating speed and ease to zero
        tier1 = 0.8, tier2 = 0.5,
        drain = 0.003, drainRun = 1.5, drainSprint = 1.5,
        stumble = 0.01, stumbleRun = 4.0, stumbleSprint = 4.0,
    },
    -- a unicycle: balance is the whole job, so it wobbles often and falls more than the tricycle
    ["ImpracticalTransport.Unicycle"] = {
        name = "Uni", mount = true, transitionSeconds = 1.1,
        dismount = { time = 105 },      -- the unequip action lasts this long (maxTime units: 40 measured as about 0.5 s, the clip is 1.1 s) while the dismount node plays Bob_UniDismount, instead of the vanilla pick-up      -- Bob_UniMount / Bob_UniDismount are 32 frames
        speed = { [""] = 0.46, Run = 0.62 },
        slip = 0.10, slipRun = 2.5, slipSeconds = { 0.8, 1.4 },      -- a wobble every ~10 s that usually recovers
        tier1 = 0.8, tier2 = 0.5,
        drain = 0.004, drainRun = 1.6, drainSprint = 1.6,
        stumble = 0.02, stumbleRun = 4.0, stumbleSprint = 4.0,      -- and a real fall about every 50 s
    },
}

-- throw-away calibration variants (tools/make_tilt_calibration.py writes PogoCal1..6 / UniCal1..6 items): same behaviour as the real transport
for i = 1, 8 do
    PROFILES["ImpracticalTransport.PogoCal" .. i] = PROFILES["ImpracticalTransport.PogoStick"]
    PROFILES["ImpracticalTransport.UniCal" .. i] = PROFILES["ImpracticalTransport.Unicycle"]
end

-- Ground under the rider, first match wins (lower-cased FloorMaterial property plus floor sprite name). Every number is a multiplier on top
-- of the profile and of whatever vanilla already slows walking by: speed scales the hop, stumble scales the trip chance (endurance drain
-- rises as speed falls). Unmatched ground counts as 1. Unknown ground is printed once so this list can be extended after a play session.
local SURFACES = {
    { "water",  speed = 0.30, stumble = 3.0 },
    { "mud",    speed = 0.35, stumble = 3.0 },
    { "sand",   speed = 0.50, stumble = 2.5 },
    { "snow",   speed = 0.55, stumble = 2.5 },
    { "gravel", speed = 0.70, stumble = 2.0 },
    { "dirt",   speed = 0.85, stumble = 1.5 },
    { "clay",   speed = 0.85, stumble = 1.5 },      -- blends_natural_01 Clay: the same as bare dirt
    { "grass",  speed = 0.90, stumble = 1.3 },
    { "floors_exterior_natural", speed = 0.90, stumble = 1.3 },      -- the old grass floor set (no FloorMaterial)
    -- paved ground (labels seen at the parking lot: "road_07 blends_street_01_96"): neutral for most transports; a profile with `paved` (skates) gets a speed bonus
    { "road_",  speed = 1.0, stumble = 1.0, paved = true },
    { "blends_street", speed = 1.0, stumble = 1.0, paved = true },
    { "asphalt", speed = 1.0, stumble = 1.0, paved = true },
    { "concrete", speed = 1.0, stumble = 1.0, paved = true },
    { "floors_exterior_street", speed = 1.0, stumble = 1.0, paved = true },      -- sidewalks and pavers (no FloorMaterial)
    { "tilesandstone", speed = 1.0, stumble = 1.0, paved = true },
}
local BUSH_STUMBLE = 4.0        -- tripping multiplier on a bush or tree square, on the square ahead, or inside vanilla's "in trees" state
local NEUTRAL = { speed = 1, stumble = 1 }
local seenGround = {}

-- Runs fn; if it throws (a game patch renamed a call) it prints once and is skipped from then on, so the log is never flooded
-- (the game dumps a stack trace for every caught failure).
local broken = {}
local function guarded(name, fn, default)
    if broken[name] then return default end
    local ok, result = pcall(fn)
    if ok then return result end
    broken[name] = true
    print("ImpracticalTransport " .. name .. " disabled: " .. tostring(result))
    return default
end

local function groundAt(square, forced)
    if not square then return NEUTRAL end
    local label = forced or guarded("ground", function()
        local floor = square:getFloor()
        local material = floor and floor:getProperties() and floor:getProperties():get("FloorMaterial") or ""
        local sprite = floor and floor:getSprite() and floor:getSprite():getName() or ""
        local water = square:isWaterSquare() and "water " or ""   -- shallow water (deep water already stops the walk)
        return (water .. tostring(material) .. " " .. sprite):lower()
    end, "")
    for _, surface in ipairs(SURFACES) do
        if label:find("%f[%a]" .. surface[1]) then return surface end      -- at a word start, so "tilesandstone" is not sand
    end
    if not seenGround[label] then seenGround[label] = true; print("ImpracticalTransport unclassified ground: " .. label) end
    return NEUTRAL
end

ImpracticalTransport.groundAt = groundAt      -- the test bot scans the world with it (smokescan)

-- What the rider stands on. The test bot can name a ground class (ImpracticalTransport.forceGround = "sand", "neutral" for none) but only under the calm
-- test switch, so normal play never sees it.
local function groundHere(player)
    local forced = ImpracticalTransport.calm and ImpracticalTransport.forceGround or nil
    return groundAt(player:getCurrentSquare(), forced)
end

local function bushNear(player)
    return guarded("bush", function()
        local square = player:getCurrentSquare()
        if not square then return false end
        if square:HasTree() or square:getBush() ~= nil or player:isInTrees() then return true end
        local ahead = square:getAdjacentSquare(player:getDir())
        return ahead ~= nil and (ahead:HasTree() or ahead:getBush() ~= nil)
    end, false)
end

-- Factor (0.2..1) the engine slows walking by: the in-trees walk speed variable and the character's slow factor. Missing calls count as 1.
local function vanillaSlowdown(player)
    return math.max(0.2, guarded("slowdown", function()
        local trees = player:getVariableFloat("WalkSpeedTrees", 1)
        local slowed = 1 - math.min(0.8, math.max(0, player:getSlowFactor()))
        return math.min(1, trees) * slowed
    end, 1))
end

-- Is the sprint key (or the toggle that stands for it) down? Reads the game's own binding, never a fixed key.
local function sprintAsked(player)
    return guarded("sprintkey", function()
        return player:isSprintButtonDown() or isKeyDown(getCore():getKey(KeybindId.SPRINT))
    end, false)
end

local riding = {}
local held = {}
local transitionUntil = {}
local lastKind = {}      -- the Name of the last transport held, so its Active variable can be cleared after the item is gone
local stumbleAfter = {}
local lastReport = {}

-- Putting a transport away: vanilla plays its pick-up-and-toss animation with the whole item in hand. For profiles with a `dismount` the unequip action
-- sets no action animation at all (an unknown action node falls back to the engine's surrender emote); the transport's own dismount node (idle state, driven
-- by <Name>Transition) plays instead: the rider steps off and the item stays where it was. The item is taken away when the action ends after `time`.
require "TimedActions/ISUnequipAction"
local vanillaUnequipNew = ISUnequipAction.new
function ISUnequipAction:new(character, item, maxTimeInit, reason)
    local o = vanillaUnequipNew(self, character, item, maxTimeInit, reason)
    local profile = item and PROFILES[item:getFullType()]
    if profile and profile.dismount and reason ~= "drop" and reason ~= "place" and not o.fromHotbar then
        o.maxTime = profile.dismount.time
        o.ipDismount = true
    end
    return o
end
local vanillaUnequipStart = ISUnequipAction.start
function ISUnequipAction:start()
    if self.ipDismount then
        self.item:setJobType(getText("ContextMenu_Unequip") .. " " .. self.item:getName())
        self.item:setJobDelta(0.0)
        return
    end
    vanillaUnequipStart(self)
end
local lastPace = {}
local stallUntil = {}
local coastUntil = {}
local coastFrom = {}
local wasMoving = {}
local TIER_SPEED = { ["0"] = 1.0, ["1"] = 0.6, ["2"] = 0.3, ["3"] = 2.6 }      -- what the T1 and T2 clips scale the travel by (3 = the fast clips on pavement, skates only)
local STUMBLE_COOLDOWN_SECONDS = 20
local TRANSITION_SECONDS = 0.8     -- length of Bob_PogoMount / Bob_PogoDismount (24 frames at 30 fps)

-- While a timed action such as unequip, drop or place runs, step off the pogo anim nodes so the action's own animation can finish.
-- Walking actions (click-to-move) don't count: they are plain movement.
local WALKING = { ISWalkToTimedAction = true, ISPathFindAction = true }
local function busy(player)
    local ok, queue = pcall(function() return ISTimedActionQueue.getTimedActionQueue(player).queue end)
    local current = ok and queue[1]
    return current ~= nil and not WALKING[current.Type]
end

-- Trips the rider the way vanilla's debug "stagger and fall" does (the same bump variables), costs some endurance, and starts the cooldown.
function ImpracticalTransport.stumble(player)
    stumbleAfter[player:getPlayerNum()] = getTimestampMs() + STUMBLE_COOLDOWN_SECONDS * 1000
    player:setBumpType("stagger")
    player:setVariable("BumpDone", false)
    player:setVariable("BumpFall", true)
    player:setVariable("BumpFallType", "pushedFront")
    local stats = player:getStats()
    stats:set(CharacterStat.ENDURANCE, math.max(0, stats:get(CharacterStat.ENDURANCE) - 0.1))
    print("ImpracticalTransport stumble")
end

-- The pedals lose their grip: the feet spin for a second or two (Bob_TrikeSlip, no travel) and the trike stands still, then it goes on.
function ImpracticalTransport.slip(player, profile)
    local seconds = ZombRandFloat(profile.slipSeconds[1], profile.slipSeconds[2])
    stallUntil[player:getPlayerNum()] = getTimestampMs() + seconds * 1000
    player:setVariable(profile.name .. "Stall", true)
    print(string.format("ImpracticalTransport slip %.1fs", seconds))
    -- a slip sometimes ends in a fall: likelier when running or winded
    if profile.slipFall and not ImpracticalTransport.calm then
        local endurance = player:getStats():get(CharacterStat.ENDURANCE)
        if ZombRandFloat(0, 1) < profile.slipFall * (player:isRunning() and 1.5 or 1) * (1 + (1 - endurance)) then ImpracticalTransport.stumble(player) end
    end
end

function ImpracticalTransport.getProfile(player)
    local item = player:getPrimaryHandItem()
    local held = item and PROFILES[item:getFullType()]
    if held then return held end
    return guarded("worn", function()
        local worn = player:getWornItems()
        for i = 0, worn:size() - 1 do
            local wornItem = worn:get(i):getItem()
            local profile = wornItem and PROFILES[wornItem:getFullType()]
            if profile and profile.worn then return profile end
        end
        return nil
    end, nil)
end

Events.OnPlayerUpdate.Add(function(player)
    local profile = ImpracticalTransport.getProfile(player)
    local num = player:getPlayerNum()
    -- a pogo stick is not a weapon: no aiming, no swinging while it is in hand (the weapon poses would hold it at odd angles)
    local isHeld = profile ~= nil and not profile.worn      -- a worn transport (skates) leaves aiming and swinging alone
    if isHeld ~= (held[num] or false) then
        held[num] = isHeld
        player:setIgnoreAimingInput(isHeld)
        player:setAuthorizeMeleeAction(not isHeld)
    end
    if profile then lastKind[num] = profile.name end
    local kind = lastKind[num]
    local active = profile ~= nil and not busy(player)
    if active ~= (riding[num] or false) then
        riding[num] = active
        player:setVariable(kind .. "Active", active)
        print("ImpracticalTransport riding=" .. tostring(active))
        -- hop on / step off: the mount and dismount nodes play while PogoTransition names them; the timer below clears it
        -- even if the clip's own end never does (the clips are TRANSITION_SECONDS long)
        if isHeld and profile.mount then
            player:setVariable(kind .. "Transition", active and "mount" or "dismount")
            transitionUntil[num] = getTimestampMs() + (profile.transitionSeconds or TRANSITION_SECONDS) * 1000
        end
    end
    if transitionUntil[num] and getTimestampMs() > transitionUntil[num] then
        transitionUntil[num] = nil
        player:setVariable(kind .. "Transition", "")
    end
    if not active then
        if kind then player:setVariable(kind .. "Sprint", false) end
        if stallUntil[num] then stallUntil[num] = nil; player:setVariable(kind .. "Stall", false) end
        if coastUntil[num] then coastUntil[num] = nil; player:setVariable(kind .. "Coast", false) end
        wasMoving[num] = false
        return
    end
    if stallUntil[num] and getTimestampMs() > stallUntil[num] then
        stallUntil[num] = nil
        player:setVariable(profile.name .. "Stall", false)
    end
    -- stopping is not instant on skates: when the rider stops moving the coast clip carries them on for a moment
    if profile.coast then
        local moving = player:isPlayerMoving()
        local nowMs = getTimestampMs()
        if moving then
            coastUntil[num] = nil
            player:setVariable(profile.name .. "Coast", false)
        elseif wasMoving[num] then
            local running = player:isRunning()
            local seconds = running and profile.coast.run or profile.coast.walk
            local fallChance = profile.stopFall and (running and profile.stopFall.run or profile.stopFall.walk) or 0
            fallChance = fallChance * (1 + (1 - player:getStats():get(CharacterStat.ENDURANCE))) * groundHere(player).stumble
            if not ImpracticalTransport.calm and ZombRandFloat(0, 1) < fallChance then
                print(string.format("ImpracticalTransport stop fall (chance %.2f)", fallChance))
                ImpracticalTransport.stumble(player)
            else
                coastUntil[num] = nowMs + seconds * 1000
                player:setVariable(profile.name .. "CoastGait", running and "Run" or "walk")
                player:setVariable(profile.name .. "Coast", true)
                coastFrom[num] = { x = player:getX(), y = player:getY(), tier = tostring(player:getVariableString(profile.name .. "Tier")), gait = running and "run" or "walk" }
                print(string.format("ImpracticalTransport coast %.1fs", seconds))
            end
        elseif coastUntil[num] and nowMs > coastUntil[num] then
            local from = coastFrom[num]
            if from then print(string.format("ImpracticalTransport coast distance %.2f tiles (gait %s tier %s)", math.sqrt((player:getX() - from.x) ^ 2 + (player:getY() - from.y) ^ 2), from.gait, from.tier)) end
            coastUntil[num] = nil
            player:setVariable(profile.name .. "Coast", false)
        end
        wasMoving[num] = moving
    end

    local stats = player:getStats()
    local endurance = stats:get(CharacterStat.ENDURANCE)
    local tired = endurance >= 0.5 and 1 or math.max(0.5, endurance * 0.9 + 0.5)   -- slower when winded
    -- whatever slows walking slows the hop too: the engine's own slowdown values, then the ground, all multiplied together
    local vanilla = vanillaSlowdown(player)
    local ground = groundHere(player)
    local terrain = vanilla * ground.speed
    local report = string.format("vanilla=%.2f ground=%.2f", vanilla, ground.speed)
    if report ~= lastReport[num] then lastReport[num] = report; print("ImpracticalTransport terrain " .. report) end
    -- Speed comes from which clip plays, not from a playback variable (those do nothing, see the README): the anim nodes pick a clip tier from PogoTier.
    -- Run and sprint have their own faster clips. Tier 0 is full pace, 1 and 2 are the slower clips for loose ground, a tired rider or a heavy slowdown.
    -- The engine can leave a rider in the run state with the sprint key held (the cause is not found, see docs/dev/journal.md); then the key itself counts as
    -- sprint and the run-state sprint node (<Name>Sprint) plays the sprint clip. ImpracticalTransport.forceSprint = false turns this off for tests.
    local engineSprint = player:isSprinting()
    local forced = not engineSprint and ImpracticalTransport.forceSprint ~= false and player:isRunning() and player:isPlayerMoving() and not player:isInTrees() and sprintAsked(player)
    player:setVariable(profile.name .. "Sprint", forced)
    local gait = (engineSprint or forced) and "Sprint" or player:isRunning() and "Run" or ""
    local pace = tired * terrain * ((ground.paved and profile.paved) or 1)      -- skates only: pavement is where they beat walking
    local tier = (profile.paved and pace >= profile.tierFast) and "3" or pace >= profile.tier1 and "0" or pace >= profile.tier2 and "1" or "2"
    player:setVariable(profile.name .. "Tier", tier)
    -- once a second while moving: every input to the slowdown and the speed it should produce, so a test can compare with the measured speed
    local nowMs = getTimestampMs()
    if player:isPlayerMoving() and nowMs - (lastPace[num] or 0) >= 1000 then
        lastPace[num] = nowMs
        -- the clip that plays decides the speed, and it can differ from the engine's gait flag (a bot's walk order sets isRunning but plays the walk clip)
        local clip = tostring(player:getAnimationDebug()):match("Anim: (%S+)") or ""
        local clipGait = clip:find("Sprint", 1, true) and "Sprint" or clip:find("Run", 1, true) and "Run" or ""
        local base = profile.speed and profile.speed[clipGait]
        print(string.format("ImpracticalTransport pace clip=%s gait=%s tired=%.2f vanilla=%.2f ground=%.2f pace=%.2f tier=%s expected=%.2f",
            clip, gait == "" and "walk" or gait, tired, vanilla, ground.speed, pace, tier, base and base * TIER_SPEED[tier] or -1))
    end

    if player:isPlayerMoving() then
        local fitness = player:getPerkLevel(Perks.Fitness)
        local perSecond = profile.drain * (profile["drain" .. gait] or 1) * (1.5 - fitness * 0.05) / math.max(0.2, terrain)   -- fitter riders tire slower, never zero; slow ground tires more
        stats:set(CharacterStat.ENDURANCE, math.max(0, endurance - perSecond * GameTime.getInstance():getTimeDelta()))

        if ImpracticalTransport.calm then return end      -- tests set this to measure speed without random slips and falls (forced ones still work)
        if profile.slip and not stallUntil[num] and ZombRandFloat(0, 1) < profile.slip * (profile["slip" .. gait] or 1) * (1 + (1 - endurance) * 4) * ground.stumble * GameTime.getInstance():getTimeDelta() then
            ImpracticalTransport.slip(player, profile)
        end
        -- stumbles: rarer for fit riders, much likelier once winded, never twice within the cooldown
        local now = getTimestampMs()
        if now >= (stumbleAfter[num] or 0) then
            local chance = profile.stumble * (profile["stumble" .. gait] or 1) * (1 +(1 - endurance) * 4) * (1.5 - fitness * 0.1) * ground.stumble * (bushNear(player) and BUSH_STUMBLE or 1)
            if ZombRandFloat(0, 1) < chance * GameTime.getInstance():getTimeDelta() then
                ImpracticalTransport.stumble(player)
            end
        end
    end
end)
