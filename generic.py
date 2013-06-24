import inserter,extracter
import logging

class Inserter(inserter.Inserter):
    ctr = 0
    def add(self,piece):
        hasht = self.insertPiece(piece,self.ctr,0)
        logging.debug("leaf piece {}".format(piece))
        self.ctr += 1
        super().add(hasht)
        return self

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
