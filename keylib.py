from bytelib import bytes_to_long,long_to_bytes

import base64

def decode(b):
    return base64.b64encode(b)[:-2].decode()
    #return base64.b16encode(b).decode()

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
        return 'CHK('+decode(self)+')'

def join(keys):
    return Key(b''.join(keys))


