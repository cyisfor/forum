import dependencies

####### Installing dependencies

dependencies.Import('cffi','pip install cffi')
dependencies.Import('nacl',dependencies.git('libsodium'))

import cffi.ffiplatform

try: dependencies.Import('nacl',
    "pip install pynacl",
    "echo from nacl import nacl | python")
except PermissionError:
    run("echo from nacl import nacl | python")
except cffi.ffiplatform.VerificationError:
    installSodium()

######### crypto interface starts here

import logging

from wrapper import Wrapper
import memory
from deferred import inlineCallbacks

import nacl.secret
import nacl.public
import nacl.utils
import nacl.exceptions

from contextlib import closing
import shelve

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
        logging.info(4,'Key is',self.key)
        self.box = nacl.secret.SecretBox(self.key)
    def getNonce(self,ctx,level):
        counter = ctx * 0x100 + level + 1
        return long_to_bytes(bytes_to_long(self.base) ^ counter)

class Inserter(Cryptothing):
    def __init__(self,sub,ext):
        self.plainAdd = sub.add
        super().__init__(sub)
        self.ext = ext
    def add(self,subAdd,uri,recipients):
        logging.log(5,'crypto add')
        self.recipients = recipients
        return subAdd(uri)
    def insertPiece(self,subInsertPiece,piece,ctx,level):
        # make sure ctx,level != 0,0 because that's what ctr the key piece uses.
        logging.log(4,'encrypt nonce',ctx+1,level)
        try:
           nonce = self.getNonce(ctx+1,level)
        except AttributeError:
            print(self)
            print(dir(self))
            raise
        return subInsertPiece(self.box.encrypt(piece,nonce),ctx,level)
    def finish(self,subFinish):
        logging.info(4,'finishing')
        uri = subFinish()
        def makeWrapper(uri):
            nonce = self.base
            # fine to reuse the nonce because each key is different
            chash = self.box.encrypt(uri,nonce)
            data = nonce + chash
            slot = bytes(8) + self.key
            logging.log(3,'nonce is',nonce)
            guys = enumerate(self.recipients)
            def gotKey(data,i,recipient):
                logging.log(5,'encrypting to ',recipient,len(data))
                key = nacl.public.PublicKey(data)
                with closing(shelve.open('privateKeys.shelve')) as privateKeys:
                    box = nacl.public.Box(
                            nacl.public.PrivateKey(privateKeys[str(self.info.currentIdentity)]),
                            key)
                try:
                    data += box.encrypt(slot,nonce)
                except:
                    logging.info(5,slot,nonce,'arg')
                    raise
                try:
                    i,recipient = next(guys)
                    return memory.extract(self.ext,recipient).addCallback(gotKey,i,recipient)
                except StopIteration:
                    # so how many recipients isn't certain:
                    top = (int(i>>3)+1)<<3
                    if top != i:
                        data += nacl.utils.random(len(slot)*(top-i))
                    return data
            def completePiece(piece):
                return self.plainAdd(piece)
            i,recipient = next(guys)
            return memory.extract(self.ext,recipient).addCallback(gotKey,i,recipient).addCallback(completePiece)
        return uri.addCallback(makeWrapper)


class RawExtracter(Cryptothing):
    def requestPiece(self,subRequestPiece,hasht,ctx,level):
        piece = subRequestPiece(hasht,ctx,level)
        nonce = self.getNonce(ctx+1,level)
        logging.log(4,'decrypt nonce',ctx+1,level)
        return self.box.decrypt(piece,nonce)

slotSize = nacl.secret.SecretBox.KEY_SIZE + 8
def slotSplit(b):
    for i in range(int(len(b)/slotSize)):
        yield b[i*slotSize,(i+1)*slotSize]

class Extracter:
    def __init__(self,nextStep):
        self.nextStep = nextStep
    @inlineCallbacks
    def extract(self,uri,handler):
        data = yield memory.extract(self.nextStep,uri)
        nonce,chash,slots = splitOffsets(data,
                nacl.secret.SecretBox.NONCE_SIZE,
                nacl.secret.SecretBox.KEY_SIZE)
        slots = tuple(slotSplit(slots))
        with closing(shelve.open('privateKeys.shelve')) as privateKeys:
            for priv in privateKeys.values():
                priv = nacl.public.PrivateKey(priv)
                pub = priv.public_key
                box = nacl.public.Box(priv,pub)
                try: plain = box.decrypt(slots,nonce)
                except nacl.exceptions.CryptoError: continue
                for slot in slots:
                    if bytes_to_long(slot[0:8])==0:
                        key = slot[8:]
                        box = nacl.secret.SecretBox(key)
                        # ok to reuse nonce because this is a different key
                        uri = box.decrypt(chash,nonce)
                        nextStepw = RawExtracter(self.nextStep,key,nonce)
                        ret = yield nextStepw.extract(uri,handler)
                        returnValue(ret)
        raise RuntimeError("You don't have a key for this file.")

def context(subins,subreq):
    ins,ext = Inserter(subins,subreq),Extracter(subreq)
    ins.wrap()
    return ins,ext


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
    def gotRoot(uri):
        with closing(shelve.open(dest)) as privateKeys:
            privateKeys[str(uri)] = priv.encode()
        logging.info(4,'Made key',uri)
        return uri
    return inserter.add(priv.public_key.encode()).addCallback(gotRoot)

def getPrivate(uri,isSigning=False):
    if isSigning:
        cls = nacl.signing.SigningKey
        source = 'signingKeys.shelve'
    else:
        cls = nacl.public.PrivateKey
        source = 'privateKeys.shelve'
    with closing(shelve.open(source)) as privateKeys:
        return cls(privateKeys[str(uri)])

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
