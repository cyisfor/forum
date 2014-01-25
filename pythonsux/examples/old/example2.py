import deferreds,deferred

import crypto

import generic,extracter,info
import graph
import keylib

import shelve

from hashlib import sha512


import logging
import os

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
    def requestPiece(self,hasht,ctr,depth):
        with open('pieces/{}'.format(str(hasht).replace('/','_')),'rb') as inp:
            piece = inp.read()
        logging.debug(13,'piece %x %s %x',ctr,hasht,len(piece))
        return deferred.succeed(piece)

class Inserter(generic.Inserter):
    def __init__(self,graphderp):
        super().__init__(info,graphderp)
    def insertPiece(self,piece,ctr,level):
        hasht = makeHash(piece)
        with open('pieces/{}'.format(str(hasht).replace('/','_')),'wb') as out:
            out.write(piece)
        logging.debug(13,'inserted %s',hasht)
        return deferred.succeed(hasht)

def example():
    def gotURI(uri,extracter):
        logging.info(13,'got uri '+str(uri))
        return generic.extractToFile(extracter,'test2.dat',uri)
    with graph("graph.dot") as graphderp:
        ins = Inserter(graphderp)
        inp = open('test.dat','rb')
        def close(derp):
            inp.close()
            return derp
        ins.add(inp).addCallbacks(close,close).addCallback(gotURI,Extracter())
        deferreds.run()

example()
