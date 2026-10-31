-- Rider state is derived from the equipped item each tick, so no saved state to migrate across patches.
-- The anim nodes in AnimSets/player/*_pogo.xml play only while PogoActive is true and take their speed from the variables set here.
ImpracticalTransport = ImpracticalTransport or {}

-- walk/run: animation speed scale (below 1 is slower than normal walking); drain: endurance lost per second while moving
local PROFILES = {
    ["ImpracticalTransport.PogoStick"] = { walk = 0.45, run = 0.6, drain = 0.0035 },
}

local riding = {}

-- While a timed action such as unequip, drop or place runs, step off the pogo anim nodes so the action's own animation can finish.
-- Walking actions (click-to-move) don't count: they are plain movement.
local WALKING = { ISWalkToTimedAction = true, ISPathFindAction = true }
local function busy(player)
    local ok, queue = pcall(function() return ISTimedActionQueue.getTimedActionQueue(player).queue end)
    local current = ok and queue[1]
    return current ~= nil and not WALKING[current.Type]
end

function ImpracticalTransport.getProfile(player)
    local item = player:getPrimaryHandItem()
    return item and PROFILES[item:getFullType()] or nil
end

Events.OnPlayerUpdate.Add(function(player)
    local profile = ImpracticalTransport.getProfile(player)
    local num = player:getPlayerNum()
    local active = profile ~= nil and not busy(player)
    if active ~= (riding[num] or false) then
        riding[num] = active
        player:setVariable("PogoActive", active)
        print("ImpracticalTransport riding=" .. tostring(active))
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
    end
end)
