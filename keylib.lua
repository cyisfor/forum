local bytelib = require('bytelib')
local rockrequire = require('rockrequire')
local sodium = require('sodium')
local b2l = bytelib.bytes_to_long
local l2b = bytelib.long_to_bytes

local mime = require('mime') -- yuck

function lopbyte(data) 
    local byte = string.byte(data,1)
    return byte,string.sub(data,2)
end

function decode(data) 
    if type(data) ~= 'string' then return data end
    data = data.unb64(data)
    if string.len(data) == keySize then
        return Key(data)
    elseif string.len(data) == keySize+1 then
        local depth
        depth,data = lopbyte(data)
        return URI(data,depth)
    end
end

function Key(data)
    return {
        data = data,
        encode = function()
            return mime.b64(data)
        end,
        string = function()
            return 'Key('..mime.b64(data)..')'
        end
    }
end

function override(what,name,over) 
    local old = what[name]
    what[name] = function(...) return over(old,...) end
end

function URI(data, depth)
    if depth then
        key = Key(data)
        data = string.char(depth)..data
    else
        key = Key(string.sub(data,1))
        depth = string.byte(data,0)
    end

    return {
        key = key,
        encode = function()
            return mime.b64(data)
        end,
        string = function()
            return 'URI('..key.string()..','..depth..')'
        end,
        depth = depth
    }
end

function join(keys) 
    data = ""
    for i,key in ipairs(keys) do
        data = data .. key.data
    end
    return {
        data = data,
        encode = function() return mime.b64(data) end,
        string = function()
            return "KeyList("..#keys..")"
        end
    }
end

function split(data)
    local which = -1
    return function()
        which = which + 1
        local amt = which*sodium.hash.size
        return which,string.sub(data,amt,amt+sodium.hash.size)
    end
end

function makeHash(b)
    return sodium.hash(b)
end

local keySize = sodium.hash.size

return {
    URI = URI,
    Key = Key,
    decode = decode,
    join = join,
    split = split,
    keySize = keySize
}
