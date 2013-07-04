import types
import logging
from functools import wraps

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
                    attrs[name] =v
                    logging.log(3,'overriding',name)
        for name,v in attrs.items():
            try: subv = getattr(self.sub.__class__,name)
            except AttributeError:
                logging.log(3,'subv is none')
                subv = None
            wrapper = self._makeWrapper(v,subv)
            setattr(self.__class__,name,wrapper)
            # boing
            setattr(self.sub.__class__,name,wrapper)
    def _makeWrapper(self,top,bottom):
        if bottom is None:
            logging.info(3,'simply wrappy',top)
            def wrapper(sub,*a,**kw):
                return top(self,*a,**kw)
            return wrapper
        bw = lambda *a, **kw: bottom(self.sub,*a,**kw)
        @wraps(bottom)
        def wrapper(sub,*a,**kw):
            return top(self,bw,*a,**kw)
        return wrapper
    def __getattr__(self,name):
        v = getattr(self.sub,name)
        setattr(self,name,v)
        return v
