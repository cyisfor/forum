class Requester:
    def requestPiece(self,hasht,ctr,level): pass

def register(requester):
    global theRequester
    theRequester = requester

def request(hasht,ctr,level):
    return theRequester.requestPiece(hasht,ctr,level)
