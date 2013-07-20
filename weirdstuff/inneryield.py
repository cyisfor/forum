import bluelet
def get():
    yield bluelet.sleep(0.1)
    yield bluelet.end('get')

def dostuff():
    thing = yield get()
    print('dostuff',thing)
    yield bluelet.end('dostuff:'+repr(thing))

def main():
    for i in range(6):
        for herp in dostuff():
            derp = yield herp
            print('derp',derp)
bluelet.run(main())
