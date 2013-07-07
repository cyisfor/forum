import dependencies
import sys,os
sys.path.append('deferred') # XXX: ugh
dependencies.Import('deferred',dependencies.git('git@github.com:mikeal/deferred.git'))
import deferred._defer
import deferred
from deferred.graph import graphtree,graph

from itertools import count

import logging

import functools
import copy

ignore = set()
deferreds = set()

nada = [] # some distinct guard

oldInit = deferred.Deferred.__init__
def newInit(self,*a,**kw):
    self.debug = True
    self.delayedResult = nada
    oldInit(self,*a,**kw)
    logging.debug(0,'add %s',self)
    deferreds.add(self)
deferred.Deferred.__init__ = newInit

def printFail(fail):
    fail.printTraceback()
    raise SystemExit
    return fail

oldSucceed = deferred.succeed
def succeed(result):
        d = deferred.Deferred()
        d.delayedResult = result
        return d
deferred.succeed = succeed

oldic = deferred.inlineCallbacks
def newic(f):
    f = oldic(f)
    def wrapper(*a,**kw):
        try: d = f(*a,**kw)
        except:
            import traceback
            traceback.print_exc()
            raise
        if hasattr(d,'result') and isinstance(d.result,deferred.Failure):
            printFail(d.result)
        else:
            d.addErrback(printFail)
        ignore.add(d)
        return d
    return functools.update_wrapper(wrapper,f)
deferred.inlineCallbacks = newic

def run():
    global deferreds
    errors = []
    stage = count(0)
    try: os.mkdir('deferredGraph')
    except OSError: pass
    while len(deferreds):
        with graph('deferredGraph/pass{}.dot'.format(next(stage))) as g:
            for d in deferreds:
                graphtree(d,g)
        rem = set()
        for d in copy.copy(deferreds):
            if d.called:
                rem.add(d)
            else:
                if d.delayedResult is not nada:
                    d.callback(d.delayedResult)
                    rem.add(d)
        if len(rem)==0:
            for d in deferreds:
                d.errback(deferred.Failure(RuntimeError("Deferred got lost.")))
                errors.append(d.result)
            break
        for d in rem:
            if isinstance(d.result,deferred.Failure):
                errors.append(d.result)
        deferreds = deferreds.difference(rem)
    for error in errors:
        error.printTraceback()

def remove(d):
    deferreds.remove(d)

