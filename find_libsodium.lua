local lfs = require('lfs')
require('table_ops')

local function snarf(command)
    command = command .. "; echo $?"
    local inp = io.popen(command)
    local lines = {}
    while true do
        local line = inp:read("*l")
        if not line then
            break
        end
        lines[#lines+1] = line
    end
    local status = tonumber(lines[#lines])
    local result = table.join("\n",table.slice(lines,1,-2))
    return status==0, result
end

options = {}
ok, options.cflags = snarf('pkg-config --cflags libsodium')
if ok then
    _, options.largs = assert(snarf('pkg-config --libs libsodium'))
else
    local here = io.popen('realpath '..debug.getinfo(1).short_src):read('*a')
    here = string.sub(here,1,-string.len('find_libsodium.lua')-2)

    local libs = here .."/libsodium-ok"
    if not lfs.attributes(libs,'access') then
        local old = lfs.currentdir()
        local temp = here.."/libsodium"
        lfs.chdir(here)
        os.execute('git clone https://github.com/jedisct1/libsodium.git')
        lfs.chdir(temp)
        print(temp)
        assert(os.execute('./autogen.sh')==0)
        assert(os.execute('./configure')==0)
        assert(os.execute('make -j8')==0)
        lfs.chdir(old)
        os.rename(temp,libs)
    end

    options = {
        cargs = '-I '..here..'/libsodium-ok/src/libsodium/include',
        largs = '-Wl,-rpath '..here..'/libsodium-ok/src/libsodium/.libs/ -lsodium'
    }
end

return options
