import deferreds
from deferred import succeed,DeferredList,inlineCallbacks,returnValue

def lengthyOperation(i):
    return succeed(i)

def printit(value,mess):
    print(mess,value)
    return value

def basic():
    lengthyOperation(10).addCallback(printit,"basic")
    deferreds.run()
basic()

def listTest():
    DeferredList([lengthyOperation(i).addCallback(printit,"listop") for i in range(10)]).addCallback(printit,"listend")
    deferreds.run()
listTest()

def genTest():
    @inlineCallbacks
    def coro():
        for i in range(10):
            result = yield lengthyOperation(i)
            print('result',result)
        returnValue(42)
    coro().addCallback(printit,"genTest")
    deferreds.run()

genTest()
