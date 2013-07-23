from bytelib import bytes_to_long,long_to_bytes

import base64

def decode(b):
    #return base64.b64encode(b)[:-2].decode()
    return base64.b16encode(b).decode()

class DerpKey(bytes):
    type = 'CHK'
    def __str__(self):
        return decode(self)[:4]
    def __repr__(self):
        return self.type+'('+decode(self)[:4]+')'

def Key(b,type='CHK'):
    key = DerpKey(b)
    key.type = type
    return key

def join(keys):
    return Key(b''.join(keys))


