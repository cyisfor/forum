# just testing memory extraction
import deferreds,deferred

import generic,extracter,info,memory
import graph
import keylib

import os

from hashlib import sha512


import logging

def makeHash(b):
    derp = sha512()
    derp.update(b)
    return keylib.Key(derp.digest())

try: os.mkdir('pieces')
except OSError: pass

info = info.Info(0x200,len(makeHash(b'')))

class Extracter(extracter.Extracter):
    def __init__(self):
        super().__init__(info)
    def requestPiece(self,hasht,ctr,level):
        logging.info(19,'requesting',hasht,ctr,level)
        with open('pieces/{}'.format(str(hasht).replace('/','_')),'rb') as inp:
            piece = inp.read()
        return deferred.succeed(piece)

class Inserter(generic.Inserter):
    def __init__(self,graphderp):
        super().__init__(info,graphderp)
    def insertPiece(self,piece,ctr,level):
        hasht = makeHash(piece)
        logging.info(19,'inserting',hasht,ctr,level)
        with open('pieces/{}'.format(str(hasht).replace('/','_')),'wb') as out:
            out.write(piece)
        return deferred.succeed(hasht)

def example():
    @deferred.inlineCallbacks
    def gotURI(theFile,ins):
        ext = Extracter()
        hashes = yield memory.extract(ext,theFile)
        size = 0
        for key in ext.keySplit(hashes):
            data = yield memory.extract(ext,key)
            size += len(data)
        print("Memory yielded",size)
        raise SystemExit
    with graph("graph.dot") as graphderp:
        ins = Inserter(graphderp)
        inp = open('test.dat','rb')
        def close(derp):
            inp.close()
            return derp
        ins.add(inp).addCallbacks(close,close).addCallback(gotURI,ins)
        deferreds.run()

example()
