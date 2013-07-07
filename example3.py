import deferreds,deferred

import crypto

import generic,extracter,info
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

info = info.Info(0xffff,len(makeHash(b'')))

class Extracter(extracter.Extracter):
    def __init__(self):
        super().__init__(info)
    def requestPiece(self,hasht,ctr,depth):
        with open('pieces/{}'.format(str(hasht).replace('/','_')),'rb') as inp:
            piece = inp.read()
        return deferred.succeed(piece)

class Inserter(generic.Inserter):
    def __init__(self,graphderp):
        super().__init__(info,graphderp)
    def insertPiece(self,piece,ctr,level):
        hasht = makeHash(piece)
        logging.info(4,'inserting',hasht)
        with open('pieces/{}'.format(str(hasht).replace('/','_')),'wb') as out:
            out.write(piece)
        return deferred.succeed(hasht)

def example():
    def gotURI(uri,extracter):
        logging.info(2,'got uri '+str(uri))
        return generic.extractToFile(extracter,'test2.dat',uri)
    with graph("graph.dot") as graphderp:
        ins = Inserter(graphderp)
        key = crypto.makeKey(ins)
        info.currentIdentity = key
        logging.log(4,'got key',key,keylib.decode(key))
        ins,ext = crypto.context(ins,Extracter())
        inp = open('test.dat','rb')
        def close(derp):
            inp.close()
            return derp
        ins.add(inp,(key,)).addCallbacks(close,close).addCallback(gotURI,ext)
        deferreds.run()

example()
