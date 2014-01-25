unpack = table.unpack or unpack

local cfg = require('luarocks.cfg')
local install = require('luarocks.install')
local loader = require('luarocks.loader')

local build = require('luarocks.build')
local search = require('luarocks.search')
local fs = require('luarocks.fs')
local path = require('luarocks.path')

require('stringify')

function table.build(iterator_fn, state, ...)
    local res, res_i = {}, 1
    local vars = {...}
    while true do
        vars = {iterator_fn(state, vars[1])}
        if vars[1] == nil then break end
        res[res_i] = vars[1]
        res_i = res_i+1
    end
    return res
end

function addpath(what,path)
    path = table.build(path:gmatch('[^;]+'))
    table.insert(path,what)
    return table.concat(path,';')
end
package.cpath = addpath('rocks/lib/lua/5.1/?.so',package.cpath)
package.path = addpath('rocks/share/lua/5.1/?.lua',package.path)
path.use_tree(fs.absolute_name('rocks'))

oldrequire = require

derpRequire = function(name,alreadyTried)
    args = {pcall(oldrequire,name)}
    if args[1] then
        return unpack(args,2)
    else
        err = args[2]
        if alreadyTried then
            error('installed '..name..' but cannot require!\n'..err)
        end
        desiredErr = "module '"..name.."' not found"
        if err:sub(1,desiredErr:len())==desiredErr then
            result, err = install.run(name,'--local')
            if result == nil then
                error('installing '..name..'\n'..err)
            end
            return derpRequire(name,true)
        else
            error('installing '..name..'\n'..err)
        end
    end
end

return derpRequire
