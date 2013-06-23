import inserter,extracter
import shelve
import graph
from hashlib import md5
import logging

logging.basicConfig(level=logging.DEBUG)

def makeHash(b):
    h = md5(b)
    return h.hexdigest().encode()

shelf = shelve.open("pieces.shelve")

with graph("graph.dot") as agraph:
    assert agraph
    graph = agraph
    #for k,v in shelf.items():
    #    print(k,v)

    class MyInserter(inserter.Inserter):
        def __init__(self):
            super().__init__(len(makeHash(b'')),graph)
        def insertPiece(self,piece,ctr,level):
            hashthh = makeHash(piece)
            shelf[hashthh.decode()] = piece
            return hashthh

    class MyExtracter(extracter.Extracter):
        def __init__(self,root,depth):
            super().__init__(len(makeHash(b'')),graph,root,depth)
        def requestPiece(self,hashthh,ctr,level):
            piece = shelf.get(hashthh.decode())
            logging.info("requesting {} {} {} {}".format(hashthh,piece,ctr,level))
            return piece


    inserter = MyInserter()
    inserter += makeHash(b'23')
    inserter += makeHash(b'42')
    inserter += makeHash(b'23')
    root,depth = inserter.finish()
    extractor = MyExtracter(root,depth)
    for piece in extractor:
        print("Extracted",piece)
    shelf.close()
