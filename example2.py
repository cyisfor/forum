import deferred,deferreds

import crypto

import generic,extracter,info
import graph
import keylib

import shelve

from hashlib import sha512


import logging

logging.basicConfig(level=logging.INFO,
        format='%(module)s:%(lineno)s %(message)s %(funcName)s')
def makeHash(b):
    derp = sha512()
    derp.update(b)
    return keylib.Key(derp.digest())


shelf = shelve.open('pieces.shelve')

info = info.Info(0xffff,len(makeHash(b'')))

class Extracter(extracter.Extracter):
    def __init__(self):
        super().__init__(info)
    def requestPiece(self,hasht,ctr,depth):
        piece = shelf[str(hasht)]
        logging.debug('piece %x %s %x',ctr,hasht,len(piece))
        return deferred.succeed(piece)

class Inserter(generic.Inserter):
    def __init__(self,graphderp):
        super().__init__(info,graphderp)
    def insertPiece(self,piece,ctr,level):
        hasht = makeHash(piece)
        shelf.setdefault(str(hasht),piece)
        logging.debug('inserted %s',hasht)
        return deferred.succeed(hasht)

def example():
    def gotURI(uri,extracter):
        logging.info('got uri '+str(uri))
        return generic.extractToFile(extracter,'test2.dat',uri)
    def gotKey(key,ins):
        ins,ext = crypto.context(ins,Extracter())
        inp = open('test.dat','rb')
        def close(derp):
            inp.close()
            return derp
        ins.add(inp,(key,)).addCallbacks(close,close).addCallback(gotURI,ext)
    with graph("graph.dot") as graphderp:
        ins = Inserter(graphderp)
        crypto.makeKey(ins).addCallback(gotKey,ins)
        deferreds.run()

example()
