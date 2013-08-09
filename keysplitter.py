import keylib
class Splitter:
    def __init__(self,keySize):
        self.keySize = keySize
    def keySplit(self,b):
        for i in range(int(len(b)/self.keySize)):
            yield keylib.Key(b[i*self.keySize:(i+1)*self.keySize])
