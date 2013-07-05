import types
import logging
from functools import wraps

nada = []

noreents = set()
def noreent(f):
    noreents.add(f)
    return f

class Wrapper:
    def __init__(self,sub):
        self.sub = sub
    @logging.skip
    def wrap(self):
        attrs = {}
        for klass in reversed(type(self).mro()[:-2]):
            logging.log(3,'klass',klass)
            for name,v in klass.__dict__.items():
                if name[0]=='_': continue
                if name == 'wrap': continue
                if hasattr(v,'__call__'):
                    attrs[name] =getattr(self,name)
                    logging.log(3,'overriding',name)
        for name,v in attrs.items():
            try: subv = getattr(self.sub,name)
            except AttributeError:
                logging.log(3,'subv is none')
                subv = None
            wrapper = self._makeWrapper(name,v,subv)
            setattr(self,name,wrapper)
    def _makeWrapper(self,name,top,bottom):
        if bottom is None:
            logging.info(3,'simply wrappy',top)
            @wraps(top)
            def wrapper(*a,**kw):
                try: return top(*a,**kw)
                except TypeError:
                    logging.info(8,'top',top,'self',self,'a',a)
                    raise RuntimeError
            return wrapper
        if top in noreents:
            bottomWrapper = bottom
        else:
            def bottomWrapper(*a,**kw):
                # boing
                try: old = getattr(self.sub,name)
                except AttributeError:
                    old = nada
                try:
                    setattr(self.sub,name,wrapper)
                    return bottom(*a,**kw)
                finally:
                    # we ONLY want reentrancy WHEN calling from a wrapper
                    if old is not nada:
                        setattr(self.sub,name,old)
        @wraps(top)
        def wrapper(*a,**kw):
            try: return top(bottomWrapper,*a,**kw)
            except TypeError:
                logging.info(8,top,bw,a,kw)
                raise
        return wrapper
    def __getattr__(self,name):
        v = getattr(self.sub,name)
        setattr(self,name,v)
        return v
