import os,subprocess,sys

####### Installing dependencies

here = os.path.dirname(os.path.abspath(sys.modules[__name__].__file__))

with open(os.path.join(here,"dependencies.sh"),"wt") as erase: pass

def run(*commands):
    with open(os.path.join(here,"dependencies.sh"),"at") as out:
        for command in commands:
            out.write(command+"\n")
    raise SystemExit("Please run dependencies.sh (in "+here+")")

try: import cffi.ffiplatform
except ImportError:
    run("pip install cffi")

def installSodium():
    if os.path.exists("libsodium"):
        os.chdir("libsodium")
        subprocess.check_call(["git","pull"])
    else:
        subprocess.call(["git","clone","https://github.com/jedisct1/libsodium"])
        os.chdir("libsodium")
    subprocess.check_call(["sh","autogen.sh"])
    subprocess.check_call(["sh","configure"])
    subprocess.check_call(["make","-j8"])
    run("cd "+os.path.abspath("."),
            "make install")

try: from nacl import nacl
except ImportError:
    run("pip install pynacl",
        "echo from nacl import nacl | python")
except PermissionError:
    run("echo from nacl import nacl | python")
except cffi.ffiplatform.VerificationError:
    installSodium()

######### crypto interface starts here

import generic

from nacl.secret import SecretBox
from nacl.utils import random

# copied from pycrypto
import struct
def long_to_bytes(n, blocksize=0):
    """long_to_bytes(n:long, blocksize:int) : string
    Convert a long integer to a byte string.

    If optional blocksize is given and greater than zero, pad the front of the
    byte string with binary zeros so that the length is a multiple of
    blocksize.
    """
    # after much testing, this algorithm was deemed to be the fastest
    s = b''
    n = int(n)
    pack = struct.pack
    while n > 0:
        s = pack('>I', n & 0xffffffff) + s
        n = n >> 32
    # strip off leading zeros
    for i in range(len(s)):
        if s[i] != b'\000'[0]:
            break
    else:
        # only happens when n == 0
        s = b'\000'
        i = 0
    s = s[i:]
    # add back some pad bytes.  this could be done more efficiently w.r.t. the
    # de-padding being done above, but sigh...
    if blocksize > 0 and len(s) % blocksize:
        s = (blocksize - len(s) % blocksize) * b'\000' + s
    return s

def bytes_to_long(s):
    """bytes_to_long(string) : long
    Convert a byte string to a long integer.

    This is (essentially) the inverse of long_to_bytes().
    """
    acc = 0
    unpack = struct.unpack
    length = len(s)
    if length % 4:
        extra = (4 - length % 4)
        s = b('\000') * extra + s
        length = length + extra
    for i in range(0, length, 4):
        acc = (acc << 32) + unpack('>I', s[i:i+4])[0]
    return acc

class Instracter(generic.Inserter,generic.Extracter):
    def __init__(self,key=None):
        if key:
            self.key = key
        else:
            self.key = random(SecretBox.KEY_SIZE)
        self.base = random(SecretBox.NONCE_SIZE)
        self.box = SecretBox(self.key)
    def getNonce(self,ctx,level):
        counter = ctx * 0x100 + level
        #
        return long_to_bytes(bytes_to_long(self.base) ^ counter)
    def insertPiece(self,piece,ctx,level):
        nonce = self.getNonce(ctx,level)
        super().insertPiece(self.box.encrypt(piece,nonce))
    def requestPiece(self,hasht,ctx,level):
        piece = super().requestPiece(hasht,ctx,level)
        nonce = self.getNonce(ctx,level)
        return self.box.decrypt(piece,nonce)

Inserter = Instracter
Extracter = Instracter

def test():
    derp = Instracter()
    print(derp.getNonce(0,1),derp.getNonce(1,22))
test()
