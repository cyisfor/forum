import progress
import generic
import backends.files as backend
#import deferreds
import graph

import sys

with graph('extract.dot') as graph:
    def main():
        inserter = backend.Inserter(graph)
        extracter = progress.ProgressMeasurer(inserter.makeExtracter())
        generic.extractToFile(extracter,sys.argv[1],"test.dat")
        #deferreds.run()
    main()
