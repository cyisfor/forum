dumbnames = [[
ipairs
type_check_item
(for generator)
match
min
len
snk
src
step
gsub
insert
match_name
store_if_match
Q
close
exists
nil
is_dir
read
popen
current_dir
execute
command_at
normalize
remove
concat
path
open
next
lower
sub
split_url
pcall
receive]]
dumbnames = dumbnames:gmatch('[^\n]+')
dn = {}

for name in dumbnames do    
    if name ~= nil and name ~= '' then 
        dn[name] = true
    end
end
dumbnames = dn
function trace(event, line)
    info = debug.getinfo(2,'fn')
    if info.func == assert or 
        info.func == tostring or
        info.func == pairs or
        info.func == type or
        dumbnames[info.name] then return end
    if info.name then
        print(info.name)
    end
end
function start() 
    debug.sethook(trace,'c')
end

-- this is just here for random
function wrap(o,key)
    oldf = o[key]
    o[key] = function(...)
        print(debug.getinfo(1).name,...)
        return oldf(...)
    end
end
