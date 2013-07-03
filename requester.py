class Requester:
    def requestPiece(self,hasht,ctr,depth): pass

def register(requester):
    global theRequester,maximumPieceSize,hashSize
    theRequester = requester
    maximumPieceSize = requester.maximumPieceSize
    hashSize = requester.hashSize

def request(hasht,ctr,depth,*args):
    return theRequester.requestPiece(hasht,ctr,depth)
