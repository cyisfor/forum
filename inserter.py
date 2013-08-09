import keylib

import deferred

import logging
import struct
import gc

class HashLevel(list):
    totalNum = 0
    def __repr__(self):
        return 'HashLevel'+super().__repr__()+':{:x}'.format(self.totalNum)

class Inserter:
    finalizing = False
    def __init__(self,info,graph=None):
        self.info = info
        self.levels = []
        self.graph = graph
        self.keysPerPiece = info.keysPerPiece
        self.maximumPieceSize = info.maximumPieceSize
        self.keySize = info.keySize
    def addLevel(self,key,level):
        assert(key)
        if len(self.levels) == level:
            self.levels.append(HashLevel())
        def bottomderp(bottom):
            self.levels[level].append(key)
            self.levels[level].totalNum += 1
            return bottom
        # make room for the key first
        return self.maybeCarry(level).addCallback(bottomderp)
    def maybeCarry(self,level):
        platform = self.levels[level]
        if ( self.finalizing and (len(platform) > 1 or (len(platform)==1 and level + 1 < len(self.levels)) )) or ( len(platform) >= self.keysPerPiece ):
            ctr = platform.totalNum
            def gotkey(newkey):
                if self.graph:
                    for i,hash in enumerate(platform):
                        self.graph.update(newkey,hash,platform.totalNum+i-len(platform))
                platform.clear()
                # this is VERY important:
                if self.finalizing:
                    self.finalizing = False
                    def reFinalize(derp):
                        self.finalizing = True
                        return derp
                    return self.addLevel(newkey,level+1).addCallback(reFinalize)
                return self.addLevel(newkey,level+1)
            if len(self.levels)>level+1:
                upper = self.levels[level+1]
            else:
                upper = False
            return self.insertPiece(keylib.join(platform),upper.totalNum if upper else 0,level).addCallback(gotkey)
        return deferred.succeed(platform)
    def finish(self):
        self.finalizing = True
        def carriedUp(bottom,level):
            if level + 1 < len(self.levels):
                return self.maybeCarry(level+1).addCallback(carriedUp,level+1)
            else:
                return deferred.succeed(bottom)
        def makeURI(platform):
            depth = len(self.levels) - 1
            try:
                result = platform[0]
            except:
                print(self.levels,platform)
                raise
            logging.debug(18,'finished plain',result,logging.color('blue',depth))
            self.levels.clear()
            return deferred.succeed(keylib.Key(struct.pack('B',depth)+result))
        return self.maybeCarry(0).addCallback(carriedUp,0).addCallback(makeURI)
    def insertPiece(self,piece,ctr,level,handler):
        raise NotImplementedError("Override this to insert pieces upon request! Also the pieces generated by carrying.")
