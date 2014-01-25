require('ex')

local here = debug.getinfo(1).short_src
here = string.sub(here,1,string.len('find_libsodium.lua'))

local function snarf(command,...)
    local inp, out = io.pipe()
    local pid = os.spawn(command,{
        args={...},
        stdout=out,
        stderr=out})
    out:close()
    local result = inp:read('*a')
    inp:close()
    local status = pid:wait()
    return status==0, result
end

options = {}
ok, options.cflags = snarf('pkg-config','--cflags','libsodium')
if ok then
    options.libs = assert(snarf('pkg-config','--libs','libsodium'))
else
    local libs = here .."/libsodium"
    if not lfs.attributes(libs,'access') then
        local old = os.currentdir()
        os.chdir(here)
        os.spawn('git','clone','https://github.com/jedisct1/libsodium.git'):wait()
        os.chdir(old)
    end

    options = {
        cargs = '-I '..here..'/libsodium/src/include',
        largs = '-L '..here..'/libsodium/build/ilaboeustnh -lsodium'
    }
end

return options
