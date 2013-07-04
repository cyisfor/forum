from wrapper import Wrapper
import memory
from deferred import inlineCallbacks

from contextlib import closing
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

import nacl.secret
import nacl.public
import nacl.utils


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

class Cryptothing(Wrapper):
    def __init__(self,sub,key=None,base=None):
        super().__init__(sub)
        if key:
            self.key = key
        else:
            self.key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
        if base:
            self.base = base
        else:
            self.base = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
        self.box = nacl.secret.SecretBox(self.key)
    def getNonce(self,ctx,level):
        counter = ctx * 0x100 + level + 1
        return long_to_bytes(bytes_to_long(self.base) ^ counter)

class Inserter(Cryptothing):
    def __init__(self,sub,ext):
        super().__init__(sub)
        self.ext = ext
    def add(self,uri,recipients):
        self.recipients = recipients
        return self.sub.add(uri)
    def addPiece(self,piece,ctx,level):
        # make sure ctx,level != 0,0 because that's what ctr the key piece uses.
        nonce = self.getNonce(ctx+1,level)
        return self.sub.addPiece(self.box.encrypt(piece,nonce))
    def finish():
        uri = self.sub.finish()
        def makeWrapper(uri):
            nonce = self.base
            # fine to reuse the nonce because each key is different
            chash = self.key.encrypt(uri,nonce)
            data = nonce + chash
            slot = byte(0) * 8 + instracter.key
            guys = enumerate(recipients)
            def gotKey(data,i):
                key = nacl.public.PublicKey(data)
                data += key.encrypt(slot,nonce)
                try:
                    i,recipient = next(guys)
                    return extracter.requestPiece(recipient).addCallback(gotKey,i)
                except StopIteration:
                    # so how many recipients isn't certain:
                    top = (int(i>>3)+1)<<3
                    if top != i:
                        data += nacl.utils.random(len(slot)*(top-i))
                    return data
            def completePiece(piece):
                return self.sub.add(piece)
            i,recipient = next(guys)
            return extracter.requestPiece(recipient).addCallback(gotKey,i).addCallback(completePiece)
        return uri.addCallback(makeWrapper)


class Extracter(Cryptothing):
    def requestPiece(self,hasht,ctx,level):
        piece = self.sub.requestPiece(hasht,ctx,level)
        nonce = self.getNonce(ctx,level)
        return self.box.decrypt(piece,nonce)

slotSize = nacl.secret.SecretBox.KEY_SIZE + 8;
def request(nextStep):
    @inlineCallbacks
    def doit(uri,handler):
        extracter = nextStep
        data = yield memory.extract(extracter,uri)
        nonce,chash,slots = splitOffsets(data,
                nacl.secret.SecretBox.NONCE_SIZE,
                nacl.secret.SecretBox.KEY_SIZE)
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
                        uri = box.decrypt(chash,nonce)
                        nextStepw = Extracter(nextStep,key,nonce)
                        ret = yield nextStepw.extract(uri,handler)
                        returnValue(ret)
        raise RuntimeError("You don't have a key for this file.")
    class Derp:
        def extract(self,uri,handler):
            return doit(uri,handler)
    return Derp()

def context(subins,subreq):
    return Inserter(subins,subreq),request(subreq)


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

def makeKey(inserter,isSigning=False):
    if isSigning:
        cls = nacl.signing.SigningKey
        dest = 'signingKeys.shelve'
    else:
        cls = nacl.public.PrivateKey
        dest = 'privateKeys.shelve'
    priv = cls.generate()
    def gotRoot(root):
        with closing(shelve.open(dest)) as privateKeys:
            privateKeys[str(root)] = priv.encode()
        return root
    return inserter.add(priv.public_key.encode()).addCallback(gotRoot)

def getPrivate(root,isSigning=False):
    if isSigning:
        cls = nacl.signing.SigningKey
        source = 'signingKeys.shelve'
    else:
        cls = nacl.public.PrivateKey
        source = 'privateKeys.shelve'
    with closing(shelve.open(source)) as privateKeys:
        return cls(privateKeys[str(root)])

def sign(self,inserter,pub,uri):
    priv = getPrivate(pub,isSigning=True)
    signature = priv.sign(uri)
    data = pub + uri + signature.message
    return inserter.add(data)

def checkSignature(extracter,uri):
    def doVerify(data,uri,signature):
        verifyKey = nacl.signing.Verifykey(data)
        verifyKey.verify(uri,signature)
        return uri
    def doGetKey(data):
        pub,uri,signature = splitOffsets(data,dispatcher.uriSize,dispatcher.uriSize)
        return extracter.extract(pub).addCallback(doVerify,uri,signature)
    return extracter.extract(uri).addCallback(doGetKey)

