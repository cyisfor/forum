import deferreds,deferred

import crypto

import generic,extracter,info
import graph
import keylib

import os


import logging

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
    def begun(result):
        extracter,theSignature = result
        logging.info(18,"Extracted signature")
        theFile = yield crypto.checkSignature(extracter,theSignature)
        ret = yield generic.extractToFile(extracter,'test2.dat',theFile)
        deferred.returnValue(ret)

    @deferred.inlineCallbacks
    def gotURI(theFile,ins,cryptins):
        logging.info(21,'added '+str(theFile))
        print("Signer:")
        for i,keyid in enumerate(crypto.listPrivate(signing=True)):
            print("{}) {}".format(i,keyid))
        identity = input('use identity:')
        if identity:
            identity = int(identity)
            for i,keyid in enumerate(crypto.listPrivate()):
                if i == identity:
                    skey = crypto.getPrivate(keyid,signing=True)
                    break
            else:
                raise SystemExit("Bad index.")
        else:
            skey = crypto.makeKey(ins,signing=True)
            print("New signing key",skey)
        theSignature = yield crypto.sign(cryptins,skey,theFile)
        logging.info(18,'signed uri '+str(theSignature))
        cryptpiece = yield cryptins.commit(theSignature)
        logging.info(18,'crypt uri '+str(cryptpiece))
        crypto.Extracter(Extracter()).begin(cryptpiece).addCallback(begun)

    with graph("graph.dot") as graphderp:
        ins = Inserter(graphderp)
        key = keylib.Key(input("Recipient:"),'PUB')
        logging.log(4,'got key',key,keylib.decode(key))
        cryptins = crypto.Inserter(ins)
        inp = open(os.environ['file'],'rb')
        def close(derp):
            inp.close()
            return derp
        cryptins.add(inp,(key,)).addCallbacks(close,close).addCallback(gotURI,ins,cryptins)
        deferreds.run()

example()
