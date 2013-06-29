import gc
import logging
from pprint import pprint

class HashLevel(list):
    totalNum = 0

class Inserter:
    finalizing = False
    maximumPieceSize = 0xffff
    def __init__(self,keyLength,graph=None):
        self.levels = []
        self.graph = graph
        self.keyLength = keyLength
        self.keysPerPiece = int(self.maximumPieceSize / self.keyLength)
    def add(self,keys):
        for key in keys:
            yield self.addLevel(key,0)
        return
    def addLevel(self,key,level):
        if len(self.levels) == level:
            self.levels.append(HashLevel())
        # make room for the key first
        bottom = yield self.maybeCarry(level)
        bottom.append(key)
        logging.info("Added {}".format(key))
        return bottom
    def maybeCarry(self,level):
        platform = self.levels[level]
        logging.info("levels {}".format(self.levels))
        logging.info("finalizing? {} {} {}".format(self.finalizing,len(platform),level))
        if ( self.finalizing and len(platform) > 1 ) or ( len(platform) == self.keysPerPiece ):
            logging.info("We need to carry")
            ctr = platform.totalNum
            newkey = yield self.insertPiece(b''.join(platform),ctr,level+1)
            if self.graph:
                for hash in platform:
                    self.graph.update(newkey,hash)
            platform.clear()
            logging.info("Carried a level to {}".format(newkey))
            finalizing = self.finalizing
            if finalizing:
                self.finalizing = False
            self.addLevel(newkey,level+1)
            if finalizing:
                self.finalizing = True
        yield bluelet.ReturnEvent(platform)
    def finish(self):
        self.finalizing = True
        level = 0
        while level < len(self.levels):
            bottom = yield self.maybeCarry(level)
            #if len(bottom)==1:
            #    logging.info("Found root {} {}".format(bottom,self.levels))
            #    break
            level = level + 1
            hack = len(self.levels)
        level -= 1
        depth = len(self.levels)
        logging.info("depth {} {}".format(depth,level))
        platform = self.levels[level]
        assert platform
        result = platform[0]
        self.levels = []
        self.finalizing = False
        gc.collect()
        return struct.pack('B',depth)+result
    def insertPiece(self,piece,ctr,level):
        raise NotImplementedError("Override this to insert pieces upon request, not just the pieces passed to +=! Also the pieces generated by carrying.")


