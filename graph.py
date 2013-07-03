
from contextlib import contextmanager

@contextmanager
def make(path):
    class Graph:
        def __init__(self,out):
            self.out = out
            self.sigh = set()
            self.bs = {}
            out.write("digraph extraction {\n")
            import keylib
            self.keylib = keylib
        def update(self,parent,child,breadth):
            self.sigh.add(parent)
            self.sigh.add(child)
            self.bs[child] = breadth
            out.write('"{}" -> '.format(self.keylib.decode(parent)))
            out.write("\"{}\";\n".format(self.keylib.decode(child)))
            out.flush()
        def finish(self):
            def writeKey(key):
                breadth = self.bs.get(key)
                if breadth is None:
                    breadth = '?'
                else:
                    breadth = '{:x}'.format(breadth)
                key = self.keylib.decode(key)
                out.write("\"{}\" [label=\"{}:{}\"];\n".format(key,key[:4],breadth))
            for key in self.sigh:
                writeKey(key)
            out.write("\n}\n");
            out.flush()
    with open(path,'wt') as out:
        graph = Graph(out)
        yield graph
        graph.finish()

import sys
sys.modules[__name__] = make
