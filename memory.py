def appendPieces(pieces):
    def handle(data,which):
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
