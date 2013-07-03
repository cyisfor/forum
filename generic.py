import inserter,extracter
import requester

from deferred import inlineCallbacks,returnValue

import logging
from itertools import count

class Inserter(inserter.Inserter):
    ctr = 0
    def addPiece(self,piece):
        ret = self.insertPiece(piece,self.ctr,-1).addCallback(self.addLevel,0)
        return ret
    @inlineCallbacks
    def addFile(self,inp):
        piece = bytearray(requester.maximumPieceSize)
        counter = count(0)
        while True:
            where = inp.tell()
            amt = inp.readinto(piece)
            if not amt: break
            ctr = next(counter)
            logging.info('reading piece %x %x %x %s',ctr,ctr*requester.maximumPieceSize,where,piece[:5])
            yield self.addPiece(piece[:amt])
        ret = yield self.finish()
        returnValue(ret)
    @inlineCallbacks
    def addPieces(self,pieces):
        for i in range(int(len(pieces)/requester.maximumPieceSize+1)):
            yield self.addPiece(pieces[i*requester.maximumPieceSize:(i+1)*requester.maximumPieceSize])
        ret = yield self.finish()
        returnValue(ret)
    def add(self,thing):
        if hasattr(thing,'readinto'):
            return self.addFile(thing)
        return self.addPieces(thing)

def extract(uri,gotPiece):
    ex = extracter.Extracter()
    def leafHash(hasht,which):
        return requester.request(hasht,which,0).addCallback(gotPiece,which)
    return ex.extract(uri,leafHash)

def extractToFile(dest,uri):
    out = open(dest,'wb')
    hack = extracter.Extracter()
    def writer(piece,which):
        logging.info('writing piece %x %x %x %s',which,which*requester.maximumPieceSize,len(piece),piece[:5])
        out.seek(which*requester.maximumPieceSize)
        out.write(piece)
        out.flush()
    def closer(mumble):
        out.close()
    return extract(uri,writer)
