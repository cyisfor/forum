import types
import logging
from functools import wraps
import copy

nada = []

class Wrapper:
    def __init__(self,sub):
        self.sub = copy.copy(sub)
        self.original = sub
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
                    logging.log(7,'overriding',name)
        for name,v in attrs.items():
            try: subv = getattr(self.sub,name)
            except AttributeError:
                logging.log(3,'subv is none')
                continue
            wrapper = self._makeWrapper(name,v,subv)
            setattr(self,name,wrapper)
            setattr(self.sub,name,wrapper)
    def _makeWrapper(self,name,top,bottom):
        @wraps(top)
        def wrapper(*a,**kw):
            try:
                return top(bottom,*a,**kw)
            except TypeError:
                print(top,bottom)
                raise
        return wrapper
    def __getattr__(self,name):
        v = getattr(self.sub,name)
        setattr(self,name,v)
        return v
