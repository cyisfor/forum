import backends.files as backend
from deferred import inlineCallbacks
import keylib

import sys
import struct

@inlineCallbacks
def main():
    inserter = backend.Inserter()
    inp = sys.stdin.detach()
    root = None
    depth = inp.read(1)[0]
    print('depth',depth)
    while True:
        derp = inp.read(2)
        if not derp: break
        amt = struct.unpack('>H',derp)[0]
        piece = inp.read(amt)
        if root is None:
            root = yield inserter.insertPiece(piece,0,0)
            print(keylib.URI(root,depth))
        else:
            root = yield inserter.insertPiece(piece,0,0)
    inp.close()
def what(result):
    print(result)
main().addCallbacks(what,what)
