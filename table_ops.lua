table.accumulate = function(self, iter)
    if(iter == nil) then
        iter = self
        self = {}
    end
    for value in iter do
        self[#self+1] = value
    end
    return self
end

table.slice = function(values, i1, i2)
    local res = {}
    local n = #values
    -- default values for range
    i1 = i1 or 1
    i2 = i2 or n
    if i2 < 0 then
        i2 = n + i2 + 1
    elseif i2 > n then
        i2 = n
    end
    if i1 < 1 or i1 > n then
        return {}
    end
    local k = 1
    for i = i1,i2 do
        res[k] = values[i]
        k = k + 1
    end
    return res
end

table.join = function(sep,t)
    local first = false
    local res = nil
    for i,v in ipairs(t) do
        if i ~= 1 then
            res = res .. sep .. v
        else
            res = v
        end
    end
    return res
end
