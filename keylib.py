from bytelib import bytes_to_long,long_to_bytes

import base64
import struct

def decode(b):
    #return base64.b64decode(b).decode()
    return base64.b64encode(b).decode()
def encode(s):
    try:
        return base64.b64decode(s.encode())
    except:
        import logging
        logging.error(20,s)
        raise

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

class DerpURI(DerpKey):
    depth = None
    def __repr__(self):
        return self.type+'URI('+decode(self)[:4]+','+str(self.depth)+')'

def URI(s,depth=None,type='CHK'):
    if depth and isinstance(s,bytes):
        data = struct.pack('B',depth)+s
        uri = DerpURI(data)
        uri.depth = depth
    elif len(data) == keySize:
        data = encode(s)
        uri = DerpURI(data)
        uri.depth = 1
    else:
        data = encode(s)
        uri = DerpURI(data[1:])
        uri.depth = data[0]
    uri.type = 'URI'+type
    return uri

def join(keys):
    return Key(b''.join(keys))

from hashlib import sha512

def makeHash(b):
    derp = sha512()
    derp.update(b)
    return Key(derp.digest())

keySize = len(makeHash(b''))
