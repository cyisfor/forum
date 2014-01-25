local function Extracter(backend,frontend) 
    local handlePiece = function(key,piece,ctr,level)
        frontend.gotPiece(key,ctr,level)
        if level == -1 then
            frontend.gotLeaf(key,piece,ctr,level)
        else
            for i,key in keylib.split(piece) do
                -- this should be parallelized...
                backend.requestPiece(key,handlePiece,ctr+i,level-1)
            end
        end
    end
    return {
        extract = function(url)
            uri = keylib.decode(uri)
            backend.requestPiece(uri.key,handlePiece,0,uri.depth)
        end
    }
end

return Extracter
