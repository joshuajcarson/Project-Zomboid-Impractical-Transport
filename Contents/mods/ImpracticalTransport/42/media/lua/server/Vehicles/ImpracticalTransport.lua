ImpracticalTransport = ImpracticalTransport or {}

-- Vanilla create hooks roll random wear and fuel; these tricycles always start full so the "pedal power" fiction holds.
-- shortcut: still a battery + petrol engine under the hood; replace with a real pedal part once movement is proven.
function ImpracticalTransport.CreateBattery(vehicle, part)
    local item = VehicleUtils.createPartInventoryItem(part)
    if item then item:setUsedDelta(1) end
end

function ImpracticalTransport.CreateGasTank(vehicle, part)
    VehicleUtils.createPartInventoryItem(part)
    part:setContainerContentAmount(part:getContainerCapacity())
end
