import bluelet

def a(i):
    res = yield b(i+3)
    print('a',res)
def b(i):
    res = yield c(i+3)
    print('b',res)
    yield bluelet.end(res)
def c(i):
    res = yield d(i+3)
    print('c',res)
    yield bluelet.end(res)
def d(i):
    res = yield bluelet.end(i+3)
    print('d',res)

bluelet.run(a(0))

