import inserter,extracter
import logging
class NoneLeft(Exception): pass

class Extracter:
    def __init__(self,requester):
        self.requester = requester
        self.hashesPerPiece = int(requester.maximumPieceSize / requester.keyLength)
        self.keyLength = requester.keyLength
    def keySplit(self,b):
        for i in range(int(len(b)/self.keyLength)):
            yield b[i*self.keyLength:(i+1)*self.keyLength]
    def extract(self,piece,breadth,depth):
        if depth == 0:
            self.finish(piece,breadth,-1)
            return
        for i,hash in enumerate(self.keySplit(piece)):
            yield self.requester.requestPiece(self.extract,breadth*self.hashesPerPiece+i,depth-1)
    def finish(self,piece,ctr,level): pass

class Inserter:
    def insert(self,depth):
        hashes = []
        breadth = 0
        while not self.done:
            hashes.append(self.insertPiece(yield,breadth,depth))
            if len(hashes)==self.hashesPerPiece:
                if not self.sub:
                    self.sub = copy.copy(self)
                    self.sub.send(...with(self.sub.insert(......

