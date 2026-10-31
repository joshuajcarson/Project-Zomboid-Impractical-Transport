-- Rider state is derived from the equipped item each tick, so no saved state to migrate across patches.
-- The anim nodes in AnimSets/player/*_pogo.xml play only while PogoActive is true and take their speed from the variables set here.
ImpracticalTransport = ImpracticalTransport or {}

-- walk/run/sprint: playback speed of the Bob_PogoHop clip (1 = one hop per 0.8 s, 0.64 tiles each, so 0.8 tiles/s; bare walking is ~1.4).
--   run and sprint keep roughly vanilla's step up from walking (the ratios are estimates, not yet measured)
-- drain: endurance lost per second while moving, times drainRun / drainSprint when running or sprinting
-- stumble: chance per second of tripping while fresh (about one fall every 80 s of hopping; winded riders trip up to 5x as often),
--   times stumbleRun / stumbleSprint: faster hopping falls much more than it speeds up
local PROFILES = {
    ["ImpracticalTransport.PogoStick"] = {
        walk = 1.0, run = 1.7, sprint = 2.2,
        drain = 0.0035, drainRun = 1.6, drainSprint = 2.5,
        stumble = 0.0125, stumbleRun = 3.0, stumbleSprint = 6.0,
    },
}

-- throw-away calibration variants (tools/make_calibration.py): same behaviour as the real stick
for i = 1, 7 do PROFILES["ImpracticalTransport.PogoCal" .. i] = PROFILES["ImpracticalTransport.PogoStick"] end

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
    { "grass",  speed = 0.90, stumble = 1.3 },
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

local function groundAt(square)
    if not square then return NEUTRAL end
    local label = guarded("ground", function()
        local floor = square:getFloor()
        local material = floor and floor:getProperties() and floor:getProperties():get("FloorMaterial") or ""
        local sprite = floor and floor:getSprite() and floor:getSprite():getName() or ""
        local water = square:isWaterSquare() and "water " or ""   -- shallow water (deep water already stops the walk)
        return (water .. tostring(material) .. " " .. sprite):lower()
    end, "")
    for _, surface in ipairs(SURFACES) do
        if label:find(surface[1], 1, true) then return surface end
    end
    if not seenGround[label] then seenGround[label] = true; print("ImpracticalTransport unclassified ground: " .. label) end
    return NEUTRAL
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

local riding = {}
local held = {}
local transitionUntil = {}
local stumbleAfter = {}
local lastReport = {}
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

function ImpracticalTransport.getProfile(player)
    local item = player:getPrimaryHandItem()
    return item and PROFILES[item:getFullType()] or nil
end

Events.OnPlayerUpdate.Add(function(player)
    local profile = ImpracticalTransport.getProfile(player)
    local num = player:getPlayerNum()
    -- a pogo stick is not a weapon: no aiming, no swinging while it is in hand (the weapon poses would hold it at odd angles)
    local isHeld = profile ~= nil
    if isHeld ~= (held[num] or false) then
        held[num] = isHeld
        player:setIgnoreAimingInput(isHeld)
        player:setAuthorizeMeleeAction(not isHeld)
    end
    local active = isHeld and not busy(player)
    if active ~= (riding[num] or false) then
        riding[num] = active
        player:setVariable("PogoActive", active)
        print("ImpracticalTransport riding=" .. tostring(active))
        -- hop on / step off: the mount and dismount nodes play while PogoTransition names them; the timer below clears it
        -- even if the clip's own end never does (the clips are TRANSITION_SECONDS long)
        if isHeld then
            player:setVariable("PogoTransition", active and "mount" or "dismount")
            transitionUntil[num] = getTimestampMs() + TRANSITION_SECONDS * 1000
        end
    end
    if transitionUntil[num] and getTimestampMs() > transitionUntil[num] then
        transitionUntil[num] = nil
        player:setVariable("PogoTransition", "")
    end
    if not active then return end

    local stats = player:getStats()
    local endurance = stats:get(CharacterStat.ENDURANCE)
    local tired = endurance >= 0.5 and 1 or math.max(0.5, endurance * 0.9 + 0.5)   -- slower when winded
    -- whatever slows walking slows the hop too: the engine's own slowdown values, then the ground, all multiplied together
    local vanilla = vanillaSlowdown(player)
    local ground = groundAt(player:getCurrentSquare())
    local terrain = vanilla * ground.speed
    local report = string.format("vanilla=%.2f ground=%.2f", vanilla, ground.speed)
    if report ~= lastReport[num] then lastReport[num] = report; print("ImpracticalTransport terrain " .. report) end
    -- the engine can keep the walk node playing while the rider runs, so all three nodes read the speed of the current gait
    local gait = player:isSprinting() and "Sprint" or player:isRunning() and "Run" or ""
    local hop = (profile[gait:lower()] or profile.walk) * tired * terrain
    player:setVariable("PogoWalkSpeed", hop)
    player:setVariable("PogoRunSpeed", hop)
    player:setVariable("PogoSprintSpeed", hop)
    player:setVariable("PogoSpeed", 1)

    if player:isPlayerMoving() then
        local fitness = player:getPerkLevel(Perks.Fitness)
        local perSecond = profile.drain * (profile["drain" .. gait] or 1) * (1.5 - fitness * 0.05) / math.max(0.2, terrain)   -- fitter riders tire slower, never zero; slow ground tires more
        stats:set(CharacterStat.ENDURANCE, math.max(0, endurance - perSecond * GameTime.getInstance():getTimeDelta()))

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
