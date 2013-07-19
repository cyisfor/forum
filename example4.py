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
    def requestPiece(self,hasht,ctr,level):
        logging.info(13,'requesting',hasht,ctr,level)
        with open('pieces/{}'.format(str(hasht).replace('/','_')),'rb') as inp:
            piece = inp.read()
        return deferred.succeed(piece)

class Inserter(generic.Inserter):
    def __init__(self,graphderp):
        super().__init__(info,graphderp)
    def insertPiece(self,piece,ctr,level):
        hasht = makeHash(piece)
        logging.info(12,'inserting',hasht,ctr,level)
        with open('pieces/{}'.format(str(hasht).replace('/','_')),'wb') as out:
            out.write(piece)
        return deferred.succeed(hasht)

def example():
    @deferred.inlineCallbacks
    def gotURI(uri,inserter,extracter):
        logging.info(2,'got uri '+str(uri))
        skey = crypto.makeKey(ins,signing=True)
        logging.info(14,'signing key',skey)
        uri = yield crypto.sign(inserter,skey,uri)
        logging.info(3,'signature uri '+str(uri))
        uri = yield crypto.checkSignature(extracter,uri)
        yield generic.extractToFile(extracter,'test2.dat',uri)
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
        ins.add(inp,(key,)).addCallbacks(close,close).addCallback(gotURI,ins,ext)
        deferreds.run()

example()
