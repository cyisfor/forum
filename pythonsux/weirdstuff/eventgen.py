import bluelet

# Let's say there's a recursive generator...
# Either it generates a ValueEvent, or it delegates to the next level of recursion
# Shouldn't that ...sometimes... yield value events?

def justIteration():
    def listgetter(depth,i):
        if depth == 0:
            yield i
            return
        accum = 0
        for i in range(3):
            for thing in listgetter(depth-1,i):
                accum += thing
                yield accum
    for thing in listgetter(3,4):
        print(thing)
#justIteration()

def justBlocking():
    def listgetter(depth,i):
        # some blocking socket operation here maybe.
        print("blocking yay")
        yield bluelet.sleep(1)
        yield bluelet.end(42)
    def main():
        value = yield listgetter(3,4)
        print(value)
    bluelet.run(main())

#justBlocking()

def both():
    def listgetter(depth,i):
        if depth == 0:
            yield bluelet.end(i)
            return
        accum = 0
        for i in range(3):
            for item in listgetter(depth-1,i):
                # some blocking operation here.
                if hasattr(item,'value'):
                    item = item.value
                    print(item)
                    yield bluelet.sleep(0.1)
                    accum += item
                else:
                    yield item
            print('Yielding a value event here!',depth,accum)
            yield bluelet.ValueEvent(accum)
        yield bluelet.end(accum)

    def main():
        for item in listgetter(3,4):
            if hasattr(item,'value'):
                print('A value was yielded.',item.value)
            else:
                yield item
    bluelet.run(main())
both()
