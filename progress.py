import wrapper,time
import logging
from deferred import inlineCallbacks,returnValue

def makeHistogram():
    return [0]*100

def stretchBucket(bucket,total):
    try:
        length = min(total,100)
        if bucket is None: return [0] * length
        if len(bucket) == length: return bucket
        oldTotal = len(bucket)
        newBucket = [0] * length
        for i in range(len(newBucket)):
            newBucket[i] = bucket[int(i*oldTotal/length)]
        return newBucket
    except TypeError as e:
        import traceback
        logging.error(20,total)
        traceback.print_exc()
        raise SystemExit


class ProgressMeasurer(wrapper.Wrapper):
    def __init__(self,sub,depth):
        super().__init__(sub)
        self.buckets = [None for i in range(depth+1)]
        self.target = 0
        self.targetLevel = depth
        self.depth = depth
        self.wrap()
        self.getTotal()
    def getTotal(self):
        self.possibleTotal = int(self.target * self.keysPerPiece ** (self.targetLevel))
        logging.info(19,'possible total',self.possibleTotal,self.target,self.targetLevel)
    @inlineCallbacks
    def requestPiece(self,subreq,hasht,ctr,level):
        thisPiece = yield subreq(hasht,ctr,level)
        logging.info(19,"piece is",thisPiece[:4],self.targetLevel,ctr,level)
        if self.targetLevel == level + 1:
            if self.target == ctr:
                # now we're moving to a lower level (unless at the lowest)
                self.targetLevel -= 1
                self.buckets[self.targetLevel] = None
                self.target = ctr*self.keysPerPiece + len(thisPiece)/self.keySize
                logging.info(19,"new target",ctr,level,self.target)
                self.getTotal()
                # impossible to get the target for this, before this
                # because this is the hash of the list containing the target for this.
        if level < self.targetLevel:
            bucket = self.buckets[level]
            logging.info(19,'got',ctr,self.possibleTotal,ctr*100/self.possibleTotal)
            self.buckets[level] = bucket = stretchBucket(bucket,self.possibleTotal)
            bucket[int(ctr* len(bucket) / self.possibleTotal)] += 1
        self.showBucket(self.buckets[level])
        returnValue(thisPiece)
    def showBucket(self,bucket):
        logging.info(19,bucket)
        time.sleep(0.2)
