def flatten(g):
    for thing in g:
        if hasattr(thing,'__next__'):
            for subthing in flatten(thing):
                yield subthing
        else:
            yield thing
