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

dummy = False

import logging

import wrapper
import memory
from deferred import inlineCallbacks,returnValue
import keylib
from bytelib import bytes_to_long,long_to_bytes,splitOffsets

import nacl.signing
import nacl.nacl
import nacl.secret
import nacl.public
import nacl.utils
import nacl.exceptions

from contextlib import contextmanager
import dbm
import errno
import time

@contextmanager
def aShelf(path):
    db = None
    try:
        while True:
            try:
                db = dbm.open(path,'cs')
                break
            except OSError as e:
                if e.errno == errno.EAGAIN:
                    logging.info(16,'again?')
                    time.sleep(0.1)
                else:
                    raise
        yield db
    finally:
        if db:
            db.close()


def exNonce(b):
    # SIGH
    return b[nacl.secret.SecretBox.NONCE_SIZE:]

# copied from pycrypto
import struct
class Cryptothing(wrapper.Wrapper):
    def __init__(self,sub,key=None,base=None):
        super().__init__(sub)
        if key:
            self.key = key
        else:
            if dummy:
                self.key = b'K'*nacl.secret.SecretBox.KEY_SIZE
            else:
                self.key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
        if base:
            self.base = bytes_to_long(base)
        else:
            if dummy:
                self.base = bytes_to_long(b'N'*nacl.secret.SecretBox.NONCE_SIZE)
            else:
                self.base = bytes_to_long(nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE))
        self.box = nacl.secret.SecretBox(self.key)
        self.key = keylib.Key(self.key,'SYM')
        logging.info(4,'Skey is',self.key)
    def getNonce(self,ctx,level):
        ret = self.base ^ (0x100*ctx + level)
        logging.info(17,'derp nonce',0x100*ctx+level)
        return long_to_bytes(ret,nacl.secret.SecretBox.NONCE_SIZE)[:nacl.secret.SecretBox.NONCE_SIZE]
        #return b'Q'*nacl.secret.SecretBox.NONCE_SIZE
        #return nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)

class PleaseClone(Exception): pass

""" Inserter... adds files and produces keys. When you commit() it wraps it all in an encryption
piece... not the URI for each piece, but whatever top URI you provide. In that piece's slot is the
top baseLevel achieved. To get an extracter you must provide the encryption piece URI, which will
result in (if successful) an extracter and a top piece. You can then use the extracter to extract
the URIs within the top piece as necessary. You don't see the top URI because it just requests and decrypts the top piece automatically for you.
"""

class Inserter(Cryptothing):
    baseLevel = 0
    finished = False
    def __init__(self,sub):
        self.plainAdd = sub.add
        super().__init__(sub)
        # crypto data may be up to 0x10 bigger than plaintext
        self.sub.maximumPieceSize -= 0x10
        self.wrap()
    def add(self,subAdd,uri,recipients=None):
        if self.finished:
            raise RuntimeError("This inserter has already committed its utmost piece.")
        logging.log(5,'crypto add')
        if recipients:
            self.recipients = recipients
        return subAdd(uri)
    def insertPiece(self,subInsertPiece,piece,ctr,level):
        # make sure ctr,level != 0,0 because that's what ctr the key piece uses.
        if level == 0: ctr += 1
        nonce = self.getNonce(ctr,level+self.baseLevel)
        def gotHash(hasht):
            logging.info(18,'inserting',hasht,ctr,'<span style="color: blue">',level,'</span>',self.baseLevel)
            return hasht
        return subInsertPiece(exNonce(self.box.encrypt(piece,nonce)),ctr,level).addCallback(gotHash)
    def finish(self,subFinish):
        def increaseBaseLevel(uri):
            self.baseLevel += uri[0] + 1 # 1 extra for the leaf levels
            return uri
        return subFinish().addCallback(increaseBaseLevel)
    def commit(self,topURI):
        self.finished = True
        nonce = self.getNonce(0,0)
        # fine to reuse the nonce because each key is different
        uri = struct.pack('B',self.baseLevel-1)+topURI
        chash = self.box.encrypt(uri,nonce)
        #assert(chash[:len(nonce)]==nonce)
        # do NOT exNonce this... we need to save the base nonce, once
        if not len(chash)==2 + self.keySize + nacl.secret.SecretBox.NONCE_SIZE + 0x10:
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
            box = nacl.public.Box(
                    getPrivate(self.info.currentIdentity),
                    key)
            slot = exNonce(box.encrypt(slot,nonce))
            assert len(slot) == slotSize
            logging.info(10,'key',keylib.decode(recipient),'slot',keylib.decode(slot))
            data += slot
        return self.plainAdd(data)

class RawExtracter(Cryptothing):
    def __init__(self,sub,baseLevel,key,nonce):
        self.maximumPieceSize = sub.maximumPieceSize - 0x10
        self.baseLevel = baseLevel
        super().__init__(sub,key,nonce)
    def extract(self,subExtract,url,handler):
        depth = url[0]
        logging.info(18,'key',self.key,'depth of',depth,self.baseLevel)
        def reduceBaseLevel(thing):
            self.baseLevel -= depth + 3 # XXX: +2? what's goin on here?
            return thing
        return subExtract(url,handler).addCallback(reduceBaseLevel)
    @inlineCallbacks
    def requestPiece(self,subRequestPiece,hasht,ctr,level):
        piece = yield subRequestPiece(hasht,ctr,level)
        if level == 0: ctr += 1
        nonce = self.getNonce(ctr,level+self.baseLevel)
        logging.info(18,'requesting',hasht,ctr,logging.color('blue',level),self.baseLevel)
        returnValue(self.box.decrypt(piece,nonce))

# determined experimentally
slotSize = nacl.secret.SecretBox.KEY_SIZE + 0x18
def slotSplit(b):
    for i in range(int(len(b)/slotSize)):
        yield b[i*slotSize:(i+1)*slotSize]

class Extracter:
    def __init__(self,nextStep):
        self.nextStep = nextStep
        self.keySize = nextStep.keySize
        self.maximumPieceSize = nextStep.maximumPieceSize - 0x10
    @inlineCallbacks
    def begin(self,uri):
        data = yield memory.extractFull(self.nextStep,uri)
        assert(len(data) > 0)
        logging.info(18,'begin extraction data = ',len(data))
        nonce,chash,theirKey,slots = splitOffsets(data,
                nacl.secret.SecretBox.NONCE_SIZE,
                2 + self.keySize + 0x10,
                nacl.public.PublicKey.SIZE)
        logging.info(19,'YAY got crypto wrapper',keylib.decode(nonce))
        theirKey = nacl.public.PublicKey(theirKey)
        slots = tuple(slotSplit(slots))
        with aShelf('privateKeys.shelve') as privateKeys:
            for slot in slots:
                for keyid in privateKeys.keys():
                    priv = nacl.public.PrivateKey(privateKeys[keyid])
                    logging.info(10,"pkey",keylib.decode(priv.public_key.encode()),'slot',keylib.decode(slot))
                    box = nacl.public.Box(priv,theirKey)
                    try: plain = box.decrypt(slot,nonce)
                    except nacl.exceptions.CryptoError as e:
                        logging.info(10,'huh?',e)
                        continue
                    if bytes_to_long(plain[0:8])==0:
                        key = plain[8:]
                        box = nacl.secret.SecretBox(key)
                        # ok to reuse nonce because this is a different key
                        uri = box.decrypt(chash,nonce)
                        # subtract the initial depth first
                        # (just as we add the initial depth last when inserting)
                        baseLevel = uri[0] - uri[1]
                        topURI = uri[1:]
                        logging.info(20,'Making raw extracter',keylib.Key(nonce,'NONCE'),baseLevel,keylib.Key(topURI,'URI'))
                        nextStepw = RawExtracter(self.nextStep,baseLevel,key,nonce)
                        nextStepw.wrap()
                        returnValue((nextStepw,topURI))
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

def makeKey(inserter,signing=False):
    if signing:
        cls = nacl.signing.SigningKey
        size = nacl.nacl.lib.crypto_sign_PUBLICKEYBYTES
        dest = 'signingKeys.shelve'
    else:
        cls = nacl.public.PrivateKey
        size = cls.SIZE
        dest = 'privateKeys.shelve'

    if dummy:
        priv = cls(b'Q'*size)
    else:
        priv = cls.generate()

    if signing:
        keyid = priv.verify_key.encode()
    else:
        keyid = priv.public_key.encode()
    with aShelf(dest) as privateKeys:
        privateKeys[keyid] = priv.encode()
    keyid = keylib.Key(keyid,type='SIGN' if signing else 'ENCRYPT')
    logging.info(15,'Made pkey',keyid)
    return keyid

def getPrivate(keyid,signing=False):
    if signing:
        cls = nacl.signing.SigningKey
        source = 'signingKeys.shelve'
    else:
        cls = nacl.public.PrivateKey
        source = 'privateKeys.shelve'
    with aShelf(source) as privateKeys:
        return cls(privateKeys[keyid])

def sign(inserter,pub,uri):
    priv = getPrivate(pub,signing=True)
    signature = priv.sign(uri)
    assert len(uri) == inserter.keySize + 1
    logging.info(16,'hmm',type(signature))
    data = pub + uri + signature.signature
    logging.info(15,'signing',keylib.decode(data[:len(pub)]))
    try:
        return inserter.add(data)
    except PleaseClone:
        return inserter.clone().add(data)

@inlineCallbacks
def checkSignature(extracter,uri):
    data = yield memory.extractFull(extracter,uri)
    logging.info(15,'verifying',len(data))
    pub,uri,signature = splitOffsets(data,nacl.nacl.lib.crypto_sign_PUBLICKEYBYTES,extracter.keySize+1)
    verifyKey = nacl.signing.VerifyKey(pub)
    logging.info(15,keylib.decode(pub),keylib.decode(verifyKey.encode()))
    verifyKey.verify(uri,signature)
    logging.info(16,'verified',uri)
    returnValue(uri)
