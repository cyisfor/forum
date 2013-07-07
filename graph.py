from contextlib import contextmanager

class Graph:
    def __init__(self,out):
        self.out = out
        self.nodes = set()
        self.bs = {}
        out.write("digraph extraction {\n")
        import keylib
        self.keylib = keylib
        self.out = out
    def update(self,parent,child,breadth):
        self.nodes.add(parent)
        self.nodes.add(child)
        self.bs[child] = breadth
        self.out.write('"{}" -> '.format(self.keylib.decode(parent)))
        self.out.write("\"{}\";\n".format(self.keylib.decode(child)))
        self.out.flush()
    def finish(self):
        def writeKey(key):
            breadth = self.bs.get(key)
            if breadth is None:
                breadth = '?'
            else:
                breadth = '{:x}'.format(breadth)
            key = self.keylib.decode(key)
            self.out.write("\"{}\" [label=\"{}:{}\"];\n".format(key,key[:4],breadth))
        for key in self.nodes:
            writeKey(key)
        self.out.write("\n}\n");
        self.out.flush()

@contextmanager
def make(path):
    with open(path,'wt') as out:
        graph = Graph(out)
        yield graph
        graph.finish()

import sys
module = sys.modules[__name__]
make.modulederp = module
sys.modules[__name__] = make
