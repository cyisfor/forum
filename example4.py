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

info = info.Info(0x80,len(makeHash(b'')))

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
    def begun(result):
        extracter,theSignature = result
        logging.info(18,"Extracted signature",theSignature)
        theFile = yield crypto.checkSignature(extracter,theSignature)
        ret = yield generic.extractToFile(extracter,'test2.dat',theFile)
        deferred.returnValue(ret)

    @deferred.inlineCallbacks
    def gotURI(theFile,ins,cryptins):
        logging.info(18,'added '+str(theFile))
        skey = crypto.makeKey(ins,signing=True)
        theSignature = yield crypto.sign(cryptins,skey,theFile)
        logging.info(18,'signed uri '+str(theSignature))
        cryptpiece = yield cryptins.commit(theSignature)
        logging.info(18,'crypt uri '+str(cryptpiece))
        crypto.Extracter(Extracter()).begin(cryptpiece).addCallback(begun)

    with graph("graph.dot") as graphderp:
        ins = Inserter(graphderp)
        key = crypto.makeKey(ins)
        info.currentIdentity = key
        logging.log(4,'got key',key,keylib.decode(key))
        cryptins = crypto.Inserter(ins)
        inp = open('test.dat','rb')
        def close(derp):
            inp.close()
            return derp
        cryptins.add(inp,(key,)).addCallbacks(close,close).addCallback(gotURI,ins,cryptins)
        deferreds.run()

example()
