require('luarocks.loader')
function rockrequire(name,tries)
    tries =  tries or 0
    if tries > 2 then
        error('Failed too much trying to install '..name)
    end
    status, err = pcall(require,name)
    if status == false then
        os.execute("luarocks install --local "..name)
        return rockrequire(name,tries+1)
    end
    return err
end
return rockrequire
