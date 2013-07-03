import base64

def decode(b):
    return base64.b64encode(b)[:-2].decode()

class Wrapper:
    def __init__(self,sub):
        self.sub = sub
    def __getattr__(self,name):
        value = getattr(self.sub,name)
        setattr(self,name,value)
        return value

class Key(bytes):
    def __str__(self):
        return decode(self)
    def __repr__(self):
        return 'KEY('+decode(self)+')'

def join(keys):
    return Key(b''.join(keys))


