import parse
from deferred import inlineCallbacks
import xml.dom.minidom

import backends.shelf as bs

import sys

@inlineCallbacks
def main():
    inserter = bs.Inserter()
    print("OK loading")
    root = yield parse.create(inserter,xml.dom.minidom.parse(sys.stdin))
    parse.load(root,sys.stdout)

if __name__ == '__main__':
    import deferreds
    d = main()
    # XXX: and here it should be complete, since there's only deferred.success and inlineCallbacks!
    # what didn't get called back?
    print('er,done')
    deferreds.run()
