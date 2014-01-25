local require = require('rockrequire')
local basexx = require('basexx')
for n,v in pairs(basexx) do
    print(n)
end
print(basexx.to_hex('12345'))
