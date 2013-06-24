from inserter import Inserter,HashLevel
import logging

class NoneLeft(Exception): pass


class Extracter(Inserter):
    def __init__(self,keyLength,graph,root,depth):
        super().__init__(keyLength,graph)
        self.levels = [HashLevel() for i in range(depth)]
        self.levels[-1].append(root)
    def keySplit(self,b):
        for i in range(int(len(b)/self.keyLength)):
            yield b[i*self.keyLength:(i+1)*self.keyLength]
    def decrement(self,level=0):
        """This is not strict subtraction, because ideally we'd like to extract
 * the file from start to end, not from end to start.
 * so instead of having offset start at platform->num and decrementing
 * to 0, it goes up from 0 to num. Otherwise it's pretty much like
 * subtraction...
"""
        if len(self.levels) <= level:
            raise NoneLeft()
        platform = self.levels[level]
        while len(platform) == 0:
            # this platform's empty. Let's borrow from above to fill it
            # up again with the next level's keyes

            # This is also not like subtracting, in that when it fails to borrow,
            # it just tries the next key in the list. That's like... borrowing 2
            # instead of 1? I dunno. But keyes that can't be retrieved are
            # skipped over leaving blank spots in the resulting file
            # (while preserving ctr order!)

            borrow = False
            while not borrow:
                borrow = self.decrement(level+1)
            # ok we subtracted out a key. Now extract it into the platform!
            if level == 0:
                ctr = 0
            else:
                # this took me like days to figure out -_-
                ctr = len(self.levels[level-1])*self.keysPerPiece
            ctr += len(platform)
            # now ctr is what totalNum *would be*
            # make sure to mutate here.
            platform.extend(self.keySplit(self.requestPiece(borrow,ctr,level+1)))
        return platform.pop(0)
    def __iter__(self):
        return self
    def __next__(self):
        try: return self.decrement()
        except NoneLeft: raise StopIteration
