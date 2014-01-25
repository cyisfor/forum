local lfs = require('lfs')

local myexecute = function(command)
    print('> '..command)
    return os.execute(command)
end

local function compilerequire(name, options)
    dest = name .. ".so"
    attr = lfs.attributes(dest,'access')
    if attr then 
        return require(name)
    end

    local cargs = ''
    local largs = ''
    if options then
        if options.cargs then
            cargs = options.cargs
        end
        if options.largs then
            largs = options.largs
        end
    end
    source = options.source or name .. ".c"
    
    assert(0==myexecute("gcc -O2 -fPIC -I/usr/include/luajit-2.0 -c "..source.." -o "..name..".o "..cargs))
    assert(0==myexecute("gcc -shared -o "..dest.." "..name..".o "..largs))
    
    return require(name)
end

return compilerequire
