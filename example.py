import generic,extracter,memory,crypto
import shelve
import graph
from hashlib import md5
import logging

logging.basicConfig(level=logging.INFO)

def makeHash(b):
    h = md5(b)
    return h.hexdigest().encode()

shelf = shelve.open("pieces.shelve")

with graph("graph.dot") as graph:
    #for k,v in shelf.items():
    #    print(k,v)


    class MyInserter(generic.Inserter):
        def __init__(self):
            super().__init__(len(makeHash(b'')),graph)
        def insertPiece(self,piece,ctr,level):
            hashthh = makeHash(piece)
            shelf[hashthh.decode()] = piece
            return hashthh

    class MyExtracter(generic.Extracter):
        def __init__(self,root,depth):
            super().__init__(len(makeHash(b'')),graph,root,depth)
        def requestPiece(self,hashthh,ctr,level):
            piece = shelf.get(hashthh.decode())
            return piece

    inserter = MyInserter()

    publicKey = crypto.makeKey(inserter)
    # publicKey = b'123441251351'
    def subInsert(inserter):
        with open("test.png","rb") as inp:
            root = inserter.add(inp)
        root = metafile.insert(inserter,root,"test.png","image/png","A test (also porn)")
        return root,[publicKey]
    root = crypto.insert(inserter,subInsert)
    root = crypto.sign(inserter,publicKey,root)
    extractor = MyExtracter(root,depth)
    with open("result.png","wb") as out:
        for piece in extractor:
            out.write(piece)

    shelf.close()
