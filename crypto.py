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
from deferred import inlineCallbacks,returnValue
import keylib
from bytelib import bytes_to_long,long_to_bytes,splitOffsets

import nacl.secret
import nacl.public
import nacl.utils
import nacl.exceptions

from contextlib import closing
import shelve

# copied from pycrypto
import struct
class Cryptothing(wrapper.Wrapper):
    def __init__(self,sub,key=None,base=None):
        super().__init__(sub)
        if key:
            self.key = key
        else:
            self.key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
        self.box = nacl.secret.SecretBox(self.key)
        logging.info(4,'Skey is',self.key)
    def getNonce(self):
        return b'Q'*nacl.secret.SecretBox.NONCE_SIZE
        #return nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)

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
           nonce = self.getNonce()
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
            nonce = self.getNonce()
            # fine to reuse the nonce because each key is different
            chash = self.box.encrypt(uri,nonce)
            if not len(chash)==1 + self.hashSize + nacl.secret.SecretBox.NONCE_SIZE + 0x10:
                raise RuntimeError('Oh no',hex(len(chash)),hex(len(uri)),hex(len(chash)-len(uri)))
            # not nonce + because nonce is already prepended by self.box.encrypt!
            data = chash + self.info.currentIdentity
            logging.log(9,'chash',keylib.decode(chash))
            logging.log(9,'Current identity is',keylib.decode(self.info.currentIdentity))
            logging.log(9,'encoded',keylib.decode(data))
            slot = bytes(8) + self.key
            logging.log(3,'nonce is',nonce)
            for recipient in self.recipients:
                key = nacl.public.PublicKey(recipient)
                logging.log(7,'encrypting to',keylib.decode(recipient),len(data))
                with closing(shelve.open('privateKeys.shelve')) as privateKeys:
                    box = nacl.public.Box(
                            nacl.public.PrivateKey(privateKeys[str(self.info.currentIdentity)]),
                            key)
                slot = box.encrypt(slot,nonce)
                assert len(slot) == slotSize
                logging.info(10,'key',keylib.decode(recipient),'slot',keylib.decode(slot))
                data += slot
            ret = self.plainAdd(data)
            def derp(uri):
                logging.info(7,"wrapper uri =",uri)
                return uri
            ret.addCallback(derp)
            return ret
        return uri.addCallback(makeWrapper)


class RawExtracter(Cryptothing):
    @inlineCallbacks
    def requestPiece(self,subRequestPiece,hasht,ctx,level):
        piece = yield subRequestPiece(hasht,ctx,level)
        nonce,piece = splitOffsets(piece,nacl.secret.SecretBox.NONCE_SIZE)
        logging.info(12,'found nonce',nonce)
        returnValue(self.box.decrypt(piece,nonce))

# determined experimentally
slotSize = nacl.secret.SecretBox.KEY_SIZE + nacl.public.Box.NONCE_SIZE + 0x18
print(hex(slotSize))
def slotSplit(b):
    for i in range(int(len(b)/slotSize)):
        yield b[i*slotSize:(i+1)*slotSize]

class Extracter:
    def __init__(self,nextStep):
        self.nextStep = nextStep
        self.hashSize = nextStep.hashSize
        self.maximumPieceSize = nextStep.maximumPieceSize
    @inlineCallbacks
    def extract(self,uri,handler):
        data = yield memory.extract(self.nextStep,uri)
        logging.info(12,'YAY got crypto wrapper')
        nonce,chash,theirKey,slots = splitOffsets(data,
                nacl.secret.SecretBox.NONCE_SIZE,
                1 + self.hashSize + 0x10,
                nacl.public.PublicKey.SIZE)
        logging.info(9,'their key',keylib.decode(theirKey))
        logging.info(9,keylib.decode(nonce),keylib.decode(chash))
        theirKey = nacl.public.PublicKey(theirKey)
        slots = tuple(slotSplit(slots))
        with closing(shelve.open('privateKeys.shelve')) as privateKeys:
            for slot in slots:
                derpnonce,slot = splitOffsets(slot,nacl.public.Box.NONCE_SIZE)
                assert(derpnonce==nonce)
                for privb in privateKeys.values():
                    priv = nacl.public.PrivateKey(privb)
                    logging.info(10,"pkey",keylib.decode(priv.public_key.encode()),'slot',keylib.decode(slot))
                    box = nacl.public.Box(priv,theirKey)
                    try: plain = box.decrypt(slot,nonce)
                    except nacl.exceptions.CryptoError as e:
                        logging.info(10,'huh?',e)
                        continue
                    logging.info(11,'Yay we found a key!')
                    if bytes_to_long(plain[0:8])==0:
                        key = plain[8:]
                        box = nacl.secret.SecretBox(key)
                        # ok to reuse nonce because this is a different key
                        uri = box.decrypt(chash,nonce)
                        nextStepw = RawExtracter(self.nextStep,key,nonce)
                        nextStepw.wrap()
                        # XXX: how to change this from a wrapper extracter to a hash tree extractor??
                        self.extract = nextStepw.extract
                        # NOT nextStepw and NOT nextStep, nextStepw.sub
                        logging.info(12,'Making raw extracter',nextStepw,nextStepw.sub.requestPiece)
                        self.requestPiece = nextStepw.sub.requestPiece
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
