import inserter
from deferred import inlineCallbacks,returnValue

import logging
from itertools import count

class Inserter(inserter.Inserter):
    ctr = 0
    def addPiece(self,piece,ctr,level=-1):
        ret = self.insertPiece(piece,ctr+1,level).addCallback(self.addLevel,0)
        return ret
    @inlineCallbacks
    def addFile(self,inp):
        piece = bytearray(self.maximumPieceSize)
        counter = count(0)
        while True:
            where = inp.tell()
            amt = inp.readinto(piece)
            if not amt: break
            ctr = next(counter)
            logging.info(1,'reading piece %x %x %x %s',ctr,ctr*self.maximumPieceSize,where,piece[:5])
            yield self.addPiece(piece[:amt],ctr)
        ret = yield self.finish()
        logging.info(6,'finished with',ret,self.finish)
        returnValue(ret)
    @inlineCallbacks
    def addPieces(self,pieces):
        if len(pieces) < self.hashSize:
            raise RuntimeError("Just embed the file itself!")
        for i in range(int(len(pieces)/self.maximumPieceSize+1)):
            yield self.addPiece(pieces[i*self.maximumPieceSize:(i+1)*self.maximumPieceSize],i)
        ret = yield self.finish()
        logging.info(6,'addpieces finish',ret,self.finish)
        returnValue(ret)
    def add(self,thing):
        logging.info(7,'plain add',self.insertPiece)
        if hasattr(thing,'readinto'):
            return self.addFile(thing)
        return self.addPieces(thing)

def extract(extracter,uri,gotPiece=None):
    if gotPiece:
        def leafHash(hasht,which):
            logging.info(12,'extracter.requpi',extracter,extracter.requestPiece)
            try: return extracter.requestPiece(hasht,which,-1).addCallback(gotPiece,which)
            except:
                logging.info(11,'extracter is',extracter.requestPiece)
                raise
    else:
        def leafHash(hasht,which):
            return extracter.requestPiece(hasht,which,0)
    logging.info(6,"using extract",extracter.extract)
    return extracter.extract(uri,leafHash)

def extractToFile(extracter,dest,uri):
    out = open(dest,'wb')
    def writer(piece,which):
        logging.info(1,'writing piece %x %x %x %s',which,which*extracter.maximumPieceSize,len(piece),piece[:5])
        out.seek(which*extracter.maximumPieceSize)
        out.write(piece)
        out.flush()
    def closer(mumble):
        out.close()
    return extract(extracter,uri,writer)
