from contextlib import contextmanager

@contextmanager
def make(path):
    class Graph:
        def __init__(self,out):
            import binascii
            self.rawhexlify = binascii.hexlify
            self.out = out
            self.sigh = set()
            out.write("digraph extraction {\n")
        def hexlify(self,b):
            return self.rawhexlify(b).decode()
        def update(self,parent,child):
            self.sigh.add(parent)
            self.sigh.add(child)
            out.write('"{}" -> '.format(self.hexlify(parent)))
            out.write("\"{}\";\n".format(self.hexlify(child)))
            out.flush()
        def finish(self):
            def writeKey(key):
                hex = self.hexlify(key)
                out.write("\"{}\" [label=\"{}\"];\n".format(hex,hex[-4:]))
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
