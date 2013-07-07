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

import wrapper
import memory
from deferred import inlineCallbacks
import keylib

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

class Cryptothing(wrapper.Wrapper):
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
        logging.info(4,'Skey is',self.key)
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
        logging.log(7,'encrypt insert',ctx+1,level)
        try:
           nonce = self.getNonce(ctx+1,level)
        except AttributeError:
            print(self)
            print(dir(self))
            raise
        return subInsertPiece(self.box.encrypt(piece,nonce),ctx,level)
    def finish(self,subFinish):
        logging.info(4,'finishing',subFinish)
        uri = subFinish()
        def makeWrapper(uri):
            logging.log(6,"Making crypto wrapper for",uri)
            nonce = self.base
            # fine to reuse the nonce because each key is different
            chash = self.box.encrypt(uri,nonce)
            if not len(chash)==len(uri) + 0x28:
                raise RuntimeError('Oh no',hex(len(chash)),hex(len(uri)),hex(len(chash)-len(uri)))
            data = nonce + chash + self.info.currentIdentity
            logging.log(7,'Current identity is',keylib.decode(self.info.currentIdentity))
            slot = bytes(8) + self.key
            logging.log(3,'nonce is',nonce)
            for recipient in self.recipients:
                key = nacl.public.PublicKey(recipient)
                logging.log(7,'encrypting to',keylib.decode(recipient),len(data))
                with closing(shelve.open('privateKeys.shelve')) as privateKeys:
                    box = nacl.public.Box(
                            nacl.public.PrivateKey(privateKeys[str(self.info.currentIdentity)]),
                            key)
                try:
                    data += box.encrypt(slot,nonce)
                except:
                    logging.info(5,slot,nonce,'arg')
                    raise
            return self.plainAdd(data)
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
        yield b[i*slotSize:(i+1)*slotSize]

class Extracter:
    def __init__(self,nextStep):
        self.nextStep = nextStep
    @inlineCallbacks
    def extract(self,uri,handler):
        data = yield memory.extract(self.nextStep,uri)
        nonce,chash,theirKey,slots = splitOffsets(data,
                nacl.secret.SecretBox.NONCE_SIZE,
                nacl.secret.SecretBox.KEY_SIZE + 0x28,
                nacl.public.PublicKey.SIZE)
        logging.info(7,'their key',keylib.decode(theirKey))
        theirKey = nacl.public.PublicKey(theirKey)
        with closing(shelve.open('privateKeys.shelve')) as privateKeys:
            for priv in privateKeys.values():
                priv = nacl.public.PrivateKey(priv)
                logging.info(7,"trying pkey",keylib.decode(priv.public_key.encode()))
                box = nacl.public.Box(priv,theirKey)
                try: plain = box.decrypt(slots,nonce)
                except nacl.exceptions.CryptoError as e:
                    logging.info(7,'huh?',e)
                    continue
                slots = tuple(slotSplit(slots))
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
    keyid = priv.public_key.encode()
    with closing(shelve.open(dest)) as privateKeys:
        privateKeys[str(keyid)] = priv.encode()
    logging.info(7,'Made pkey',keylib.decode(keyid))
    return keyid

def getPrivate(keyid,isSigning=False):
    if isSigning:
        cls = nacl.signing.SigningKey
        source = 'signingKeys.shelve'
    else:
        cls = nacl.public.PrivateKey
        source = 'privateKeys.shelve'
    with closing(shelve.open(source)) as privateKeys:
        return cls(privateKeys[str(keyid)])

def sign(self,inserter,pub,uri):
    priv = getPrivate(pub,isSigning=True)
    signature = priv.sign(uri)
    data = pub + uri + signature.message
    return inserter.add(data)

def checkSignature(extracter,uri):
    def doVerify(data):
        pub,uri,signature = splitOffsets(data,dispatcher.uriSize,dispatcher.uriSize)
        verifyKey = nacl.signing.Verifykey(pub)
        verifyKey.verify(uri,signature)
        return uri
    return extracter.extract(uri).addCallback(doVerify)
