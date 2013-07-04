import types
import logging
from functools import wraps

class Wrapper:
    def __init__(self,sub):
        self.sub = sub
    @logging.skip
    def wrap(self):
        for name,v in self.__class__.__dict__.items():
            if name[0]=='_': continue
            if hasattr(v,'__call__'):
                logging.log(3,'overriding',name)
                subv = getattr(self.sub.__class__,name)
                wrapper,subwrapper = self.makeWrapper(v,subv)
                setattr(self.__class__,name,wrapper)
                # boing
                setattr(self.sub.__class__,name,subwrapper)

    def makeWrapper(self,top,bottom):
        @wraps(bottom)
        def wrapper(self,*a,**kw):
            return top(self,lambda *a, **kw: bottom(self.sub,*a,**kw),*a,**kw)
        def subwrapper(sub,*a,**kw):
            return bottom(self,*a,**kw)
        return wrapper,subwrapper
    def __getattr__(self,name):
        v = getattr(self.sub,name)
        setattr(self,name,v)
        return v
