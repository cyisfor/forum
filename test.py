import inserter
import shelve

shelf = shelve.open("pieces.shelve")

for k,v in shelf.items():
    print(k,v)

class MyInserter(inserter.Inserter):
    def __init__(self):
        super().__init__(len(str(hash(0)).encode()))
    def insertPiece(self,piece,ctr,level):
        hashthh = str(hash(piece))
        shelf[hashthh] = piece
        return hashthh.encode()


inserter = MyInserter()
inserter += str(hash(23)).encode()
inserter += str(hash(42)).encode()
inserter += str(hash(23)).encode()
print(inserter.finish())
shelf.close()
