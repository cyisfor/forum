# just testing memory extraction
import deferreds,deferred

import generic,extracter,info,memory
import graph
import keylib

from io import BytesIO
from itertools import count
import os

from hashlib import sha512


import logging

def makeHash(b):
    derp = sha512()
    derp.update(b)
    return keylib.Key(derp.digest())

try: os.mkdir('pieces')
except OSError: pass

info = info.Info(0xffff,len(makeHash(b'')))

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
    with open('test.dat','rb') as inp:
        base = inp.read()
    @deferred.inlineCallbacks
    def gotURI(theFile):
        dest = BytesIO()
        ext = Extracter()
        um = yield generic.extractToFile(ext,dest,theFile)
        logging.info(19,"Memory yielded",um)
        assert(dest.getvalue()==base)
    with graph("graph.dot") as graphderp:
        ins = Inserter(graphderp)
        ins.add(base).addCallback(gotURI)
        deferreds.run()

example()
