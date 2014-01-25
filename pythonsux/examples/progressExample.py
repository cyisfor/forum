import logging
import progress
import keylib
import generic
import backends.files as backend
#import deferreds
import graph

import sys

with graph('extract.dot') as graph:
    def main():
        inserter = backend.Inserter(graph)
        uri = keylib.URI(sys.argv[1])
        print(uri.depth)
        extracter = progress.ProgressMeasurer(inserter.makeExtracter(),uri.depth)
        generic.extractToFile(extracter,"test.dat",uri)
        #deferreds.run()
    main()
