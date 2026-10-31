-- Rider state is derived from the equipped item each tick, so no saved state to migrate across patches.
-- The anim nodes in AnimSets/player/*_pogo.xml play only while PogoActive is true and take their speed from the variables set here.
ImpracticalTransport = ImpracticalTransport or {}

-- walk/run: playback speed of the Bob_PogoHop clip (1 = one hop per 0.8 s, 0.64 tiles each, so 0.8 tiles/s; bare walking is ~1.4)
-- drain: endurance lost per second while moving
-- stumble: chance per second of tripping while fresh (about one fall every 80 s of hopping; winded riders trip up to 5x as often)
local PROFILES = {
    ["ImpracticalTransport.PogoStick"] = { walk = 1.0, run = 1.0, drain = 0.0035, stumble = 0.0125 },
}

-- throw-away calibration variants (tools/make_calibration.py): same behaviour as the real stick
for i = 1, 7 do PROFILES["ImpracticalTransport.PogoCal" .. i] = PROFILES["ImpracticalTransport.PogoStick"] end

local riding = {}
local held = {}
local transitionUntil = {}
local stumbleAfter = {}
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
    player:setVariable("PogoWalkSpeed", profile.walk * tired)
    player:setVariable("PogoRunSpeed", profile.run * tired)
    player:setVariable("PogoSpeed", 1)

    if player:isPlayerMoving() then
        local fitness = player:getPerkLevel(Perks.Fitness)
        local perSecond = profile.drain * (1.5 - fitness * 0.05)                    -- fitter riders tire slower, never zero
        stats:set(CharacterStat.ENDURANCE, math.max(0, endurance - perSecond * GameTime.getInstance():getTimeDelta()))

        -- stumbles: rarer for fit riders, much likelier once winded, never twice within the cooldown
        local now = getTimestampMs()
        if now >= (stumbleAfter[num] or 0) then
            local chance = profile.stumble * (1 + (1 - endurance) * 4) * (1.5 - fitness * 0.1)
            if ZombRandFloat(0, 1) < chance * GameTime.getInstance():getTimeDelta() then
                ImpracticalTransport.stumble(player)
            end
        end
    end
end)
