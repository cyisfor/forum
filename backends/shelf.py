import deferred

import generic,extracter,info
import graph

import sshelf

db = sshelf.open('pieces.shelve')

info = info.Info(0xffff)

class Extracter(extracter.Extracter):
    def requestPiece(self,hasht,ctr,level):
        return deferred.succeed(db[hasht])

class Inserter(generic.Inserter):
    Extracter = Extracter
    def __init__(self,graphderp=None):
        super().__init__(info,graphderp)
    def insertPiece(self,piece,ctr,level):
        hasht = self.makeHash(piece)
        db[hasht] = piece
        return deferred.succeed(hasht)
