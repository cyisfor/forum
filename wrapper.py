import types

def _makeWrapper(top,bottom):
    @wraps(bottom)
    def wrapper(*a,**kw):
        return top(bottom,*a,**kw)
    return wrapper

class Wrapper:
    def __init__(self,sub):
        self.sub = sub
        for name,v in self.__dict__.items():
            if name[0]=='_': continue
            print('wrapping',name)
            if hasattr(v,'__call__'):
                subv = getattr(self.sub,name)
                wrapper = makeWrapper(v,subv)
                setattr(self,name,wrapper)
                # boing
                setattr(self.sub,name,wrapper)
    def __getattr__(self,name):
        v = getattr(self.sub,name)
        setattr(self,name,v)
        return v
