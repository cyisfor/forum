unpack = table.unpack or unpack

function debug.getparams(f)
    params = {}
    for i = 1,debug.getinfo(f).nparams do
        table.insert(params,debug.getlocal(f,i))
    end
    return params
end

local function _stringify(val, spacing, space_n, parsed)
    if type(val) == "string" then
        return string.format("%q", val)
    elseif type(val) == "boolean" then
        return val and "true" or "false"
    elseif type(val) == "number" then
        return tostring(val)
    elseif type(val) == "function" then
        -- XXX: 
        result = {pcall(function()
            local info = debug.getinfo(val, "S")
            if not info or info.what == "C" then
                return "function:([C])"
            else
                return "function:("..table.concat(debug.getparams(val), ", ")..")"
            end
        end)}
        -- XXX: 
        if not result[1] then
            error(result[2])
            return "function([???])"
        else
            return unpack(result,2)
        end
    elseif type(val) == "table" then
        if parsed[val] then
            return "<"..tostring(val)..">"
        else
            parsed[val] = true
            local s = "{\n"
            for key,val2 in pairs(val) do
                s = s..string.rep(spacing, space_n)
                    .."[".._stringify(key, spacing, space_n+1, parsed).."] = "
                    .._stringify(val2, spacing, space_n+1, parsed)..",\n"
            end
            return s..string.rep(spacing, space_n-1).."}"
        end
    elseif type(val) == "nil" then
        return "nil"
    end
    return "<unknown value:"..type(val)..">"
end
function stringify(val, spacing)
    return _stringify(val, spacing or "    ", 1, {})
end
