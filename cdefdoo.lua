local ffi = require('ffi')
local counter = 0;
local function cdef(source)
    local fname = 'cdefdoo_'..tostring(counter)
    local place = "/dev/shm/"..fname..".c"
    local dest = io.open(place,"w")
    dest:writeString(source)
    dest:close()
    os.execute("gcc -shared -o "..place..".so "..place.." "..cdef.args)
    ffi.cdef("void* "..fname.."(void);")
    local lib = ffi.load(place..".so")
    return lib[fname]
end
cdef.args = ""
return cdef
