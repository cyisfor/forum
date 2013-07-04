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
        self.hashSize = info.hashSize
        self.maximumPieceSize = info.maximumPieceSize
        self.keysPerPiece = info.keysPerPiece
    def keySplit(self,b):
        for i in range(int(len(b)/self.hashSize)):
            yield keylib.Key(b[i*self.hashSize:(i+1)*self.hashSize])
    def extract(self,uri,handler):
        maxDepth=uri[0]
        # XXX: need the exact offset in pieces from the left
        def downOneLevel(piece,upperBreadth,level):
            hashes = list(self.keySplit(piece))
            if level == 1:
                @deferred.inlineCallbacks
                def doop():
                    for i,hasht in enumerate(hashes):
                        breadth = upperBreadth*self.keysPerPiece + i
                        logging.info(2,'breadth %s %x * %x + %x -> %x',str(hasht)[:4],upperBreadth,self.keysPerPiece,i,breadth)
                        yield handler(hasht,breadth)
                return doop()
            try:
                defs = []
                for i,hasht in enumerate(hashes):
                    breadth = upperBreadth*self.keysPerPiece + i
                    logging.info(2,'bread %s %x * %x + %x -> %x',str(hasht)[:4],upperBreadth,self.keysPerPiece,i,breadth)
                    defs.append(self.requestPiece(hasht,breadth,level)
                            .addCallback(downOneLevel,breadth,level-1))
                logging.info(2,'%x subs',len(defs))
            except:
                import traceback
                traceback.print_exc()
                raise
            return deferred.DeferredList(defs)
        hasht = keylib.Key(uri[1:])
        logging.info(2,'uri %s = %x:%s',uri,maxDepth,hasht)
        return self.requestPiece(hasht,0,maxDepth).addCallback(downOneLevel,0,maxDepth - 1)
