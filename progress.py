import wrapper

def makeHistogram():
    return [0]*100

class ProgressMeasurer(wrapper.Wrapper):
    def __init__(self,sub):
        super().__init__(sub)
        self.total = 0
        self.highestCounter = None
        self.lowestLevel = None
        self.buckets = makeHistogram()
        self.wrap()
    def requestPiece(self,hasht,ctr,level):
        noUpdate = False
        if self.lowestLevel is None or level < self.lowestLevel:
            self.highestCounter = None
            self.lowestLevel = level
            self.buckets = makeHistogram
        else:
            noUpdate = True

        if self.highestCounter is None or ctr > self.highestCounter:
            self.highestCounter = ctr
            lowerLevels = self.lowestLevel + 1 # lowest is -1 (including leaves)
            self.total = self.highestCounter * self.hashesPerPiece ** lowerLevels

        if noUpdate: pass
        else:
            self.buckets[int(ctr / self.highestcounter)]
        print(ctr,level)
        print(histogram)

        return super().requestPiece(hasht,ctr,level)


