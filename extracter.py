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

class Extracter(requester.Requester):
    def __init__(self,info):
        self.info = info
        self.keySize = info.keySize
        self.maximumPieceSize = info.maximumPieceSize
        self.keysPerPiece = info.keysPerPiece
    def keySplit(self,b):
        for i in range(int(len(b)/self.keySize)):
            logging.info(19,'chk',i,keylib.decode(b[i*self.keySize:4]))
            yield keylib.Key(b[i*self.keySize:(i+1)*self.keySize])
    def extract(self,uri,handler,maxDepth=None):
        if maxDepth is None:
            maxDepth=uri[0]
            hasht = keylib.Key(uri[1:])
        else:
            hasht = uri
        if maxDepth == 1:
            return self.requestPiece(hasht,0,-1).addCallback(handler,1)
        # XXX: need the exact offset in pieces from the left
        def downOneLevel(piece,upperBreadth,level):
            logging.info(18,"going down one level to ",level,upperBreadth)
            hashes = list(self.keySplit(piece))
            defs = []
            for i,hasht in enumerate(hashes):
                breadth = upperBreadth*self.keysPerPiece + i
                logging.info(18,'breadth %s %x * %x + %x -> %x %x',str(hasht)[:4],upperBreadth,self.keysPerPiece,i,breadth,level)
                if level == 1:
                    # XXX:
                    # but if level == 1 it's the second level of a hash tree right?
                    # shouldn't it go to the -1 handler when level *IS* -1?
                    d = handler(hasht,breadth)
                    if d: defs.append(d)
                else:
                    defs.append(self.requestPiece(hasht,breadth,level)
                            .addCallback(downOneLevel,breadth,level-1))
            return deferred.DeferredList(defs)
        logging.info(18,'uri %s = %x:%s',uri,maxDepth,hasht)
        return self.requestPiece(hasht,0,maxDepth - 1).addCallback(downOneLevel,0,max(1,maxDepth - 2))
