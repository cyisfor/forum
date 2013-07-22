import logging,keylib
import deferred
def appendPieces(pieces,extractLeaf=False,ext=None):
    if extractLeaf:
        @deferred.inlineCallbacks
        def handle(hashes,breadth):
            for i,hash in enumerate(ext.keySplit(hashes)):
                which = breadth+i
                logging.info(20,'newwhich',breadth,i,which)
                pieces[which] = yield ext.requestPiece(hash,which,-1)
    else:
        def handle(data,which):
            logging.info(19,'handle',which,keylib.decode(data[:5]))
            pieces[which] = data
    return handle
def joinPieces(pieces):
    def commit(derp):
        keys = list(pieces.keys())
        keys.sort()
        return b''.join((pieces[key] for key in keys))
    return commit
def extract(extracter,uri):
    pieces = {}
    return extracter.extract(uri,appendPieces(pieces)).addCallback(joinPieces(pieces))
def extractFull(extracter,uri):
    pieces = {}
    return extracter.extract(uri,appendPieces(pieces,extractLeaf=True,ext=extracter)).addCallback(joinPieces(pieces))
