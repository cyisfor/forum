import inserter,extracter
import logging

class Inserter(inserter.Inserter):
    ctr = 0
    def addPiece(self,piece):
        hasht = self.insertPiece(piece,self.ctr,0)
        logging.debug("leaf piece {}".format(piece))
        self.ctr += 1
        super().add(hasht)
        return self
    def addFile(self,inp):
        buf = bytearray(self.maximumPieceSize)
        while True:
            amt = inp.readinto(buf)
            if not amt: break
            self.addPiece(buf[:amt])

        return self.finish()
    def addPieces(self,pieces):
        for i in range(len(pieces)/self.maximumPieceSize+1):
            self.addPiece(pieces[i*self.maximumPieceSize,(i+1)*self.maximumPieceSize])
        return self.finish()
    def add(self,thing):
        if hasattr(thing,'readinto'):
            return self.addFile(thing)
        return self.addPieces(thing)

class Extracter(extracter.Extracter):
    ctr = 0
    def __next__(self):
        logging.info("derp! {}".format(self.levels))
        try: hasht = self.decrement()
        except extracter.NoneLeft:
            raise StopIteration
        result = self.requestPiece(hasht,self.ctr,0)
        self.ctr += 1
        return result
