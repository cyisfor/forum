import deferred,deferreds

import requester
import generic
import graph
import keylib

import shelve

from hashlib import md5 as derp


import logging

logging.basicConfig(level=logging.INFO,
        format='%(module)s:%(lineno)s %(message)s %(funcName)s')
def makeHash(b):
    md5 = derp()
    md5.update(b)
    return keylib.Key(md5.digest())


shelf = shelve.open('pieces.shelve')

class Requester(requester.Requester):
    maximumPieceSize = 0x30
    hashSize = len(makeHash(b''))
    def requestPiece(self,hasht,ctr,depth):
        piece = shelf[str(hasht)]
        logging.debug('piece %x %s %x',ctr,hasht,len(piece))
        return deferred.succeed(piece)

class Inserter(generic.Inserter):
    def insertPiece(self,piece,ctr,level):
        hasht = makeHash(piece)
        shelf[str(hasht)] = piece
        logging.debug('inserted %s',hasht)
        return deferred.succeed(hasht)

def example():
    requester.register(Requester())
    def gotURI(uri):
       logging.info('got uri '+str(uri))
       return generic.extractToFile('test2.dat',uri)
    with graph("graph.dot") as graphderp:
        ins = Inserter(graphderp)
        with open('test.dat','rb') as inp:
            ins.add(inp).addCallback(gotURI)
            deferreds.run()

example()
