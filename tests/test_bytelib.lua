local withTests = require('minitest')
require('luarocks.loader')
require('table_ops')

local function makestring(a)
    s = ''
    for _,c in ipairs(a) do
        s = s .. string.char(c)
    end
    return s
end

withTests(function()
    describe("bytelib",function()
        local mod = require('bytelib')
        local gmp = require('gmp')
        it("split by 4",function()
            for section in mod.splitOffsets("abcdABCD",4) do
                assert.same(4,string.len(section))
            end
        end)
        it("variable split",function()
            local sections = table.accumulate(mod.splitOffsets("abcdefgABCDEFG",3,3,2))
            assert.same("abc",sections[1])
            assert.same("def",sections[2])
            assert.same("gA",sections[3])
            assert.same("BCDEFG",sections[4])
        end)
        it("long2string",function()
            assert.same(makestring{4,0,0,0,0,0,0,0},mod.long2string(4))
            assert.same(makestring{1,2,3,4,5,6,7,8},mod.long2string(gmp.z("0x807060504030201")))
        end)
        it("string2long",function()
            assert.same(gmp.z(4),mod.string2long(makestring{4,0,0,0,0,0,0,0}))
            assert.same(gmp.z("0x807060504030201"),mod.string2long(makestring{1,2,3,4,5,6,7,8}))
        end)
        it("long2string2long",function()
            for _,n in ipairs({4}) do
                n = gmp.z(n)
                assert.same(n,mod.string2long(mod.long2string(n)))
            end
        end)
    end)
end)
