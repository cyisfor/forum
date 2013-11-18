import logging
import keylib
import generic
import backends.files as backend
import wrapper
from deferred import inlineCallbacks,returnValue
import graph

import sys
import struct

class Exporter(wrapper.Wrapper):
    def __init__(self,sub,out):
        super().__init__(sub)
        self.out = out
        self.pieces = []
        self.wrap()
    @inlineCallbacks
    def requestPiece(self,sub,*a):
        piece = yield sub(*a)
        self.out.write(struct.pack(">H",len(piece)))
        self.out.write(piece)
        returnValue(piece)

def main():
    inserter = backend.Inserter(graph)
    uri = keylib.URI(sys.argv[1])
    print(uri.depth)
    out = open('derp','wb')
    out.write(bytes((uri.depth,)))
    extracter = Exporter(inserter.makeExtracter(),out)
    def finished(result):
        out.close()
    generic.extract(extracter,uri,lambda piece, which: None).addCallbacks(finished,finished)
main()
