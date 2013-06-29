import inserter,extracter
import logging

class NoneLeft(Exception): pass

"""requestPiece HAS to take a continuation so
create an Extracter for every piece? Something to happen after piece is extracted.
Must know how many pieces before in this hash level, as well as how many hashes before in this piece!
as well as what level this is...
"""

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
            return
        for i,hash in enumerate(self.keySplit(piece)):
            ctr = breadth*self.hashesPerPiece+i
            piece = yield self.requester.requestPiece(hash,ctr,depth-1)
            yield self.extract(piece,ctr,depth-1)
    def leaf(self,piece,ctr,level): pass
