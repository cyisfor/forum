local keylib = require('keylib')

local function HashLevel()
    local self = {}
    self.string = "HashLevel"
    self.total = 0
    return self
end

local function Inserter(info,Extracter,backend,graph)
    local finalizing = false
    local levels = {}
    local keysPerPiece = math.floor(info.maximumPieceSize / keylib.keySize)
    local makeExtracter = function()
        return backend.Extracter(keylib.keySize,info.maximumPieceSize,keysPerPiece)
    end
    local function addLevel(key, level)
        if #levels == level then
            levels.append(HashLevel())
        end
        maybeCarry(level)
        local place = levels[level];
        place[#place+1] = key
        place.total += 1
    end
    local function maybeCarry(level)
        local place = levels[level];
        if (finalizing and #place > 1) or (#place == 1 and level + 1 < #levels) then
            ctr = place.total
            if #levels > level + 1 then
                upper = levels[level + 1].total
            else
                upper = 0
            end
            newkey = backend.insertPiece(keylib.join(place),upper,level)
            if graph then 
                for i=1..#place do
                    graph.update(newkey, digest, place.total + i - #place)
                end
            end
            if finalizing then
                finalizing = false
                addLevel(newkey,level+1)
                finalizing = true
            else
                addLevel(newkey,level+1)
            end
        end
        return place
    end
    local function finish()
        finalizing = true
        local function carriedUp(bottom,level) 
            if level + 1 < #levels then
                return carriedUp(maybeCarry(level+1),level+1)
            end
            return bottom
        end
        local bottom = carriedUp(maybeCarry(0),0)[0]
        local depth = #levels - 1
        levels = {}
        return keylib.URI(bottom,depth)
    end
    return {
        add = addLevel,
        finish = finish
    }
end

return Inserter
