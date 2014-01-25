class Dispatcher:
    def __init__(self,extracter):
        self.extracter = extracter
        self.parsers = {}
    def parse(self,data):
        self.parsers[data[0]](data[1:])
    def register(self,i,parser):
        assert not i in self.parsers
        self.parsers[i] = parser
