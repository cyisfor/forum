import inserter,extracter,deferred,requester
import keylib
import logging
import time

class NoneLeft(Exception): pass

"""requestPiece HAS to take a continuation so
create an Extracter for every piece? Something to happen after piece is extracted.
Must know how many pieces before in this hash level, as well as how many hashes before in this piece!
as well as what level this is...
"""

### Note: this extracts the hash tree, not the leaf pieces!

class Extracter(requester.Requester):
    # these are pre-calculated by Inserter.makeExtracter
    def __init__(self,keySize,maximumPieceSize,keysPerPiece):
        super().__init__(keySize)
        self.maximumPieceSize = maximumPieceSize
        self.keysPerPiece = keysPerPiece
    def extract(self,uri,handler,maxDepth=None):
        if maxDepth is None:
            if hasattr(uri,'depth'):
                maxDepth = uri.depth
                hasht = uri
            else:
                maxDepth=1
                hasht=keylib.Key(uri)
            logging.info(19,'new extract',maxDepth,uri,hasht)
        else:
            hasht = uri
        if maxDepth == 0:
            # YOU LOSE
            # YOU GET NOTHING
            # GOOD DAY SIR
            return handler(hasht,0)
        # XXX: need the exact offset in pieces from the left
        def downOneLevel(piece,upperBreadth,level,lasthasht):
            logging.info(18,"going down one level to",level,'from',lasthasht)
            #logging.info(19,keylib.decode(piece))
            hashes = list(self.keySplit(piece))
            defs = []
            for i,hasht in enumerate(hashes):
                breadth = upperBreadth*self.keysPerPiece + i
                if level == 0:
                    # the next one down is -1, so let the -1 (leaf) handler take it.
                    d = handler(hasht,breadth)
                    if d: defs.append(d)
                else:
                    defs.append(self.requestPiece(hasht,breadth,level-1)
                            .addCallback(downOneLevel,breadth,level-1,hasht))
            return deferred.DeferredList(defs)
        logging.info(18,"maxdepth is still",maxDepth)
        return self.requestPiece(hasht,0,maxDepth - 1).addCallback(downOneLevel,0,maxDepth - 1,hasht)
