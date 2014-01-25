require('luarocks.loader')
local gmp = require('gmp')
local compilerequire = require('compilerequire')
local _b = compilerequire('_bytelib','bytelib.c')
bit = bit32 or bit

local zc = string.char(0)

local function long2string(n, blocksize)
    blocksize = blocksize or 0
    n = gmp.z(n)
    if n == gmp.zero then
        return zc
    end
    assert(n>gmp.zero)
    s = n:export()
    -- add back some pad bytes
    -- add back some pad bytes.  this could be done more efficiently w.r.t. the
    -- de-padding being done above, but sigh...
    -- note < should be % but hax we only need padded up to a single block
    if blocksize > 0 and string.len(s) < blocksize then
        s = string.rep(string.char(0),(blocksize - string.len(s))) .. s
    end
    return s
end

local function string2long(s)
    s = s:gsub("\0+","")
    return gmp.importz(s)
end

local function splitOffsets(b,...)  
    local offsets = {...}
    local lastPos = 1
    local result = {}
    for _,offset in ipairs(offsets) do
        result[#result+1] = string.sub(b,lastPos,lastPos+offset-1)
        lastPos = lastPos + offset
    end
    result[#result+1] = string.sub(b,lastPos)
    return result
end

-- avoiding coroutines makes this a teensy bit faster
local function splitOffsetsCoroutine(b,...)  
    local offsets = {...}
    local lastPos = 1
    which = 0
    return function()
        if which == #offsets then
            which = which + 1
            return string.sub(b,lastPos)
        elseif which < #offsets then
            which = which + 1
            local offset = offsets[which]
            ret = string.sub(b,lastPos,lastPos+offset - 1)
            lastPos = lastPos + offset 
            return ret
        end
    end
end

return {
    string2long = string2long,
    long2string = long2string,
    splitOffsets = splitOffsetsCoroutine
}
