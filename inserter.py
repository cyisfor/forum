import requester
import keylib

import deferred
deferred.setDebugging(True)

import logging
import struct
import gc

class HashLevel(list):
    totalNum = 0
    def __repr__(self):
        return 'HashLevel'+super().__repr__()+':{:x}'.format(self.totalNum)

class Inserter:
    finalizing = False
    def __init__(self,graph=None):
        self.levels = []
        self.graph = graph
        self.hashSize = requester.hashSize
        self.keysPerPiece = int(requester.maximumPieceSize / requester.hashSize)
    def addLevel(self,key,level):
        logging.debug('addlevel %s at %s -> %s',key,level,self.levels)
        assert(key)
        if len(self.levels) == level:
            self.levels.append(HashLevel())
        def bottomderp(bottom):
            logging.debug('adding %s to %x (%x) %s',key,level,len(self.levels[level]),(bottom is self.levels[level]))
            self.levels[level].append(key)
            self.levels[level].totalNum += 1
            return bottom
        # make room for the key first
        return self.maybeCarry(level).addCallback(bottomderp)
    def maybeCarry(self,level):
        logging.debug('carry %s',self.levels)
        platform = self.levels[level]
        if ( self.finalizing and (len(platform) > 1 or (len(platform)==1 and level + 1 < len(self.levels)) )) or ( len(platform) >= self.keysPerPiece ):
            logging.debug('carrying to %x',level+1)
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
            return self.insertPiece(keylib.join(platform),ctr,level+1).addCallback(gotkey)
        else:
            logging.debug('nacarry %x %x',level,len(platform))
        return deferred.succeed(platform)
    def finish(self):
        logging.debug('finishing')
        self.finalizing = True
        def carriedUp(bottom,level):
            if level + 1 < len(self.levels):
                return self.maybeCarry(level+1).addCallback(carriedUp,level+1)
            else:
                return deferred.succeed(bottom)
        def makeURI(platform):
            depth = len(self.levels)
            try:
                result = platform[0]
            except:
                print(self.levels,platform)
                raise
            return deferred.succeed(keylib.Key(struct.pack('B',depth)+result))
        return self.maybeCarry(0).addCallback(carriedUp,0).addCallback(makeURI)
    def insertPiece(self,piece,ctr,level,handler):
        raise NotImplementedError("Override this to insert pieces upon request! Also the pieces generated by carrying.")
