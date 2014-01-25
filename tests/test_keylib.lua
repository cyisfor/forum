require('luarocks.loader')
local withTests = require('minitest')
local assert = require('luassert')

local function makestring(a)
    s = ''
    for _,c in ipairs(a) do
        s = s .. string.char(c)
    end
    return s
end

withTests(function(c)
    c:describe("keylib",function(c)
        local keylib = require('keylib')
        c:describe("key size",function(c)
            c:it("size",function()
                assert.same(0x40,keylib.keySize)
            end)
            c:it("key content",function()
                assert.same('Key(dGVzdA==)',keylib.Key("test").string())
            end)
        end)
    end)
end)
