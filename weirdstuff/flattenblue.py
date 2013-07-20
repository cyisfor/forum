from flatten import flatten
import bluelet

def coro(depth):
    if depth <= 0:
        yield bluelet.ValueEvent('q')
    else:
        for i in range(3):
            value = yield bluelet.ValueEvent((depth,i))
            print('val',value)
            yield coro(depth-1)

for item in flatten(coro(3)):
    print(item.value)
