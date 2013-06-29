import os,subprocess,sys

import shelve

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

class Instracter:
    def __init__(self,sub,key=None):
        self.sub = sub
        if key:
            self.key = key
        else:
            self.key = random(SecretBox.KEY_SIZE)
        self.base = random(SecretBox.NONCE_SIZE)
        self.box = SecretBox(self.key)
    def getNonce(self,ctx,level):
        counter = ctx * 0x100 + level + 1
        return long_to_bytes(bytes_to_long(self.base) ^ counter)
    def addPiece(self,piece,ctx,level):
        nonce = self.getNonce(ctx,level)
        return self.sub.addPiece(self.box.encrypt(piece,nonce))
    def requestPiece(self,hasht,ctx,level):
        piece = self.sub.requestPiece(hasht,ctx,level)
        nonce = self.getNonce(ctx,level)
        return self.box.decrypt(piece,nonce)

Inserter = Instracter
Extracter = Instracter

# dispatcher, if crypto then
# find key via checking private key against encrypted keys
# make new dispatcher coping dispatcher but extractor w/ Instracter + key wrapping old extracter
# new dispatcher.extract on sub-pieces
# continuation when done w/ old dispatcher (w/out crypto)

def splitOffsets(b,*offsets):
    lastPos = 0
    for offset in offsets:
        yield b[lastPos:lastPos+offset]
        lastPos += offset
    yield b[lastPos:]

maxSlots = 6

def handleCrypto(dispatcher,data,continuation):
    slotSize = nacl.secret.SecretBox.KEY_SIZE + 8;
    def slotSplit(self,b):
        for i in range(int(len(b)/slotSize)):
            yield b[i*slotSize:(i+1)*slotSize]
    nonce,slots,data = splitOffsets(data,
            nacl.public.Box.NONCE_SIZE,
            slotSize*maxSlots)
    with closing(shelve.open('privateKeys.shelve')) as privateKeys:
        for priv in privateKeys.values():
            priv = nacl.public.PrivateKey(priv)
            pub = priv.public_key
            box = nacl.public.Box(priv,pub)
            plain = box.decrypt(slots,nonce)
            slots = tuple(slotSplit(slots))
            for slot in slotSplit(slots):
                if bytes_to_long(slot[0:8])==0:
                    key = slot[8:]
                    box = nacl.secret.SecretBox(key)
                    # ok to reuse nonce because this is a different key
                    nextHash = box.decrypt(data,nonce)
                    instracter = Instracter(dispatcher.extracter,key)
                    dispatcher = copy.copy(dispatcher)
                    dispatcher.extracter = instracter
                    dispatcher.parse(instracter.requestPiece(nextHash),continuation)
                    return
    logging.warning("No private key could decrypt a crypto piece.")

def insert(inserter,subInsert):
    instracter = Instracter(inserter)
    nextHash,recipients = subInsert(instracter)
    assert len(recipients)<=6
    data = instracter.nonce
    chash = instracter.key.encrypt(nextHash,instracter.nonce)
    slot = byte(0) * 8 + instracter.key
    extracter = memory.Extracter()
    i = 0
    for i,recipient in enumerate(recipients):
        key = nacl.public.PublicKey(extracter.requestPiece(recipient))
        data += key.encrypt(slot,instracter.nonce)
    if i < 6:
        data += nacl.utils.random(len(slot)*(6-i))
    data += chash
    return inserter.addPieces(data)

def makeKey(inserter,isSigning=False):
    if isSigning:
        cls = nacl.signing.SigningKey
        dest = 'signingKeys.shelve'
    else:
        cls = nacl.public.PrivateKey
        dest = 'privateKeys.shelve'
    priv = cls.generate()
    root = inserter.insertPieces(priv.public_key)
    with closing(shelve.open(dest)) as privateKeys:
        privateKeys[root] = priv.encode()
    return root

def getPrivate(root,isSigning=False):
    if isSigning:
        cls = nacl.signing.SigningKey
        source = 'signingKeys.shelve'
    else:
        cls = nacl.public.PrivateKey
        source = 'privateKeys.shelve'
    with closing(shelve.open(source)) as privateKeys:
        return cls(privateKeys[root])

def sign(self,inserter,pub,hasht):
    priv = getPrivate(pub,isSigning=True)
    signature = priv.sign(hasht)
    data = pub + hasht + signature.message
    return inserter.insertPieces(data)

def handleSignature(self,dispatcher,data):
    pub,hasht,signature = splitOffsets(data,dispatcher.hashSize,dispatcher.hashSize)
    verifyKey = nacl.signing.VerifyKey(memory.extract(dispatcher.startANewHashTreeAt(pub)))
    verifyKey.verify(hasht,signature)
    dispatcher.parse(dispatcher.requestPiece(hasht))

def test():
    derp = Instracter()
    print(derp.getNonce(0,1),derp.getNonce(1,22))
test()
