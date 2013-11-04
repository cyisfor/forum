from deferred import inlineCallbacks
import backends.files as backend
from deferred.graph import graph

with graph('graph.dot') as graph:

    @inlineCallbacks
    def main():
        inserter = backend.Inserter(graph)
        uri = yield inserter.addPieces(tuple(derp * 100 for derp in (bytes((c,)) * 100 for c in range(256))))
        print(uri)

    main()
