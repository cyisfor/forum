import logging,keylib
import deferred

class TooBig(Exception): pass

def appendPieces(pieces,maxSize,extractLeaf=False,ext=None):
    size = 0
    if extractLeaf:
        @deferred.inlineCallbacks
        def handle(hashes,breadth):
            for i,hash in enumerate(ext.keySplit(hashes)):
                which = breadth+i
                logging.info(20,'newwhich',breadth,i,which)
                piece = yield ext.requestPiece(hash,which,-1)
                size += len(piece)
                if size > maxSize:
                    raise TooBig("Not unpacking more than",maxSize,"bytes into memory.")
                pieces[which] = piece

    else:
        def handle(data,which):
            logging.info(19,'handle',which,keylib.decode(data[:5]))
            size += len(data)
            if size > maxSize:
                raise TooBig("Not unpacking more than",maxSize,"bytes into memory.")
            pieces[which] = data
    return handle

def joinPieces(pieces):
    def commit(derp):
        keys = list(pieces.keys())
        keys.sort()
        return b''.join((pieces[key] for key in keys))
    return commit
def extract(extracter,uri,maxSize=0x100000):
    pieces = {}
    return extracter.extract(uri,appendPieces(pieces,maxSzie)).addCallback(joinPieces(pieces))
def extractFull(extracter,uri,maxSize=0x100000):
    pieces = {}
    return extracter.extract(uri,appendPieces(pieces,maxSize,extractLeaf=True,ext=extracter)).addCallback(joinPieces(pieces))
