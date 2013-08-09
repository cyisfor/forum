# just testing memory extraction
import deferreds,deferred

import generic,extracter,info,memory,reference
import graph
import keylib

from io import BytesIO
from itertools import count
import os,sys

from hashlib import sha512


import logging

def makeHash(b):
    derp = sha512()
    derp.update(b)
    return keylib.Key(derp.digest())

try: os.mkdir('pieces')
except OSError: pass

info = info.Info(0x100,len(makeHash(b'')))

class Extracter(extracter.Extracter):
    def __init__(self):
        super().__init__(info)
    def requestPiece(self,hasht,ctr,level):
        logging.info(19,'requesting',hasht,ctr,level)
        with open('pieces/{}'.format(str(hasht).replace('/','_')),'rb') as inp:
            piece = inp.read()
        return deferred.succeed(piece)

refs = reference.Counter()

class Inserter(generic.Inserter):
    def __init__(self,graphderp):
        super().__init__(info,graphderp)
    def insertPiece(self,piece,ctr,level):
        hasht = makeHash(piece)
        logging.info(19,'inserting',hasht,ctr,level)
        dest = 'pieces/{}'.format(str(hasht).replace('/','_'))
        #if not os.path.exists(dest):
        # don't do that, because inserting multiple times means multiple entries in mailbox.
        refs.ref(hasht)
        with open(dest,'wb') as out:
            out.write(piece)
        return deferred.succeed(hasht)

class Deleter(Extracter):
    def doDelete(self,piece,hasht):
        if refs.unref(hasht):
            os.unlink('pieces/{}'.format(str(hasht).replace('/','_')))
        return piece # still needed for descending hash tree
    def requestPiece(self,hasht,ctr,level):
        logging.info(20,'Request for delete',hasht)
        return super().requestPiece(hasht,ctr,level).addCallback(self.doDelete,hasht)

def example():
    with open('test.dat','rb') as inp:
        base = inp.read()
    @deferred.inlineCallbacks
    def gotURI(theFile,ins):
        nonlocal base
        dest = BytesIO()
        ext = Extracter()
        um = yield generic.extractToFile(ext,dest,theFile)
        base += b'Q'*(ins.maximumPieceSize*3)
        theSecondFile = yield ins.add(base)
        print("OK now we try deleting teh second...",file=sys.stderr)
        deleter = Deleter()
        yield generic.extract(deleter,theSecondFile)
        print("OK now we try deleting the first...",file=sys.stderr)
        yield generic.extract(deleter,theFile)
    with graph("graph.dot") as graphderp:
        ins = Inserter(graphderp)
        ins.add(base).addCallback(gotURI,ins)
        deferreds.run()

example()
