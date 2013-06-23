from inserter import Inserter,HashLevel

class NoneLeft(Exception): pass


class Extracter(Inserter):
    def keySplit(self,b):
        for i in range(int(len(b)/self.keyLength)):
            yield b[i*keyLength:(i+1)*self.keyLength]
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
        if len(platform) == 0:
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
                ctr = self.levels[level-1]*self.keysPerPiece
            ctr += len(platform)
            # now ctr is what totalNum *would be*
            # make sure to mutate here.
            platform.extend(keySplit(self.requestPiece(borrow,ctr,level)))
        return platform.pop(0)
