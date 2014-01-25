import deferred

import generic,extracter,info,logging
import graph

import os
try: os.mkdir('pieces')
except OSError: pass

info = info.Info(0x100)

class Extracter(extracter.Extracter):
    def requestPiece(self,hasht,ctr,level):
        logging.info(13,'requesting',hasht,ctr,level)
        with open('pieces/{}'.format(str(hasht).replace('/','_')),'rb') as inp:
            piece = inp.read()
        return deferred.succeed(piece)
    def hasPiece(self,hasht):
        return deferred.succeed(os.path.exists('pieces/{}'.format(str(hasht))))

class Inserter(generic.Inserter):
    Extracter = Extracter
    def __init__(self,graphderp=None):
        super().__init__(info,graphderp)
    def insertPiece(self,piece,ctr,level):
        hasht = self.makeHash(piece)
        logging.info(12,'inserting',hasht,ctr,level)
        with open('pieces/{}'.format(str(hasht).replace('/','_')),'wb') as out:
            out.write(piece)
        return deferred.succeed(hasht)
