# basically a list of hashes.

import keysplitter

import shelve,time

class Mailbox(keysplitter.Splitter):
    def __init__(self,source,keySize,pageSize=50):
        super().__init__(keySize)
        self.pageSize = pageSize
        self.source = source
    def list(self,page=0):
        self.source.seek(page*self.keySize*self.pageSize)
        return self.keySplit(self.source.read(self.keySize*self.pageSize))
    def add(self,key):
        self.source.seek(0,2)
        self.source.write(key)
    def remove(self,key):
        raise NotImplemented("Oh sure we'll just go through the log and remove every instance of this key while retaining ACID and pooping gold!")
        self.delete(key)
        # with open replacerfile(...)
    def delete(self,key):
        raise NotImplemented("Yeah uh, descend the hash tree and remove all the pieces. Except the ones... part of other root hashes? Need a second piecedb for reference counting? How to defrag a piecedb?")
