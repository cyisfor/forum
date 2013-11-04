from bytelib import bytes_to_long,long_to_bytes

import base64

def decode(b):
    return base64.b64decode(b).decode()
    #return base64.b16encode(b).decode()
def encode(s):
    return base64.b64encode(s.encode())

class DerpKey(bytes):
    type = 'CHK'
    def __str__(self):
        return decode(self)
    def __repr__(self):
        return self.type+'('+decode(self)[:4]+')'

def Key(b,type='CHK'):
    if isinstance(b,str):
        b = encode(b)
    key = DerpKey(b)
    key.type = type
    return key

def join(keys):
    return Key(b''.join(keys))

from hashlib import sha512

def makeHash(b):
    derp = sha512()
    derp.update(b)
    return Key(derp.digest())

keySize = len(makeHash(b''))
