import deferred._defer
import deferred

import logging

import functools

ignore = set()
deferreds = []

oldInit = deferred.Deferred.__init__
def newInit(self,*a,**kw):
    self.debug = True
    self.delayedResult = None
    oldInit(self,*a,**kw)
    logging.debug('add %s',self)
    deferreds.append(self)
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
    errors = []
    while len(deferreds):
        d = deferreds.pop(0)
        logging.debug('pop %s %s',d,d.called)
        if not (d.called or d in ignore):
            d.callback(d.delayedResult)
            d.called = True
            if isinstance(d.result,deferred.Failure):
                errors.append(d.result)
    for error in errors:
        error.printTraceback()

