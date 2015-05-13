package hashtree

import (
	calgo "crypto/aes"
	"crypto/cipher"
	"crypto/sha256" // this is hard to generalize
	"io"
	"os"
	// blowfish, salsa20, whatever
)

type Piece []byte

const KEYSIZE uint8 = 0x20 // AES-256
const LOOKUP_SIZE uint8 = uint8(sha256.Size)

// eh, this could be false but it'll not compile if ever so
const IV_SIZE = KEYSIZE

// size of the serialized CHK (key, lookup)
const CHK_SIZE = KEYSIZE + LOOKUP_SIZE

const MAX_PIECE_SIZE = uint(0xffff)
const MAX_ADJ_PIECE_SIZE = MAX_PIECE_SIZE - uint(IV_SIZE)

const CHK_PER_PIECE = MAX_ADJ_PIECE_SIZE / uint(CHK_SIZE)

var makeHash = sha256.Sum256

type Hash [sha256.Size]byte

// an abstract key/value store. A leveldb can work for this.
type KeyValueStore interface {
	// don't necessarily put, but definitely queue it up.
	Put(Hash, []byte) error
	Get(Hash) ([]byte, error)
	Close() error
}

/* This is actually a pair, of a key and a um...
When you insert a piece, it is encrypted first by the key, using a blank iv
since keys aren't repeated. The encrypted piece is hashed, giving you a hash
not of the content of the piece, but of its encrypted content. Choosing a key
based on the content hash will ensure the encrypted content hash doesn't change
every time you encrypt.
So this is a pair of a key, and a content hash of an encrypted piece. Thus it's
a encrypted content hash key / key, not a content hash key. But CHK is easier
to remember, and "lookup" sounds more readable than "encrypted content hash key"
*/

type CHK struct {
	key    [KEYSIZE]byte
	lookup Hash
}

/* derive the key from the content hash, allow for a bump in case our
content hash gets targeted by haters. Or derive from a password idk
*/
func DeriveKey(input []byte, bump []byte) [KEYSIZE]byte {
	var key [KEYSIZE]byte
	if bump != nil {
		input = append(input, bump...)
	}
	derp := makeHash(input)
	copy(key[:KEYSIZE], derp[:])
	return key
}

type tier []CHK
type tiers []tier

/* An interface to a leveldb backed (?) hash database */
type DB struct {
	store KeyValueStore
	tiers tiers
	err error
}

func New(store KeyValueStore) DB {
	self := DB{
		store: store,
	}

	return self
}

func explode(piece []byte) tier {
	var tier = make(tier, len(piece)/int(CHK_SIZE))
	for i, _ := range tier {
		t := CHK{}
		copy(t.key[:],piece[i*int(CHK_SIZE) : i*int(CHK_SIZE+KEYSIZE)])
		copy(t.lookup[:],piece[i*int(CHK_SIZE+KEYSIZE) : (i+1)*int(CHK_SIZE)])
		tier[i] = t
	}
	return tier
}

func conjoin(tier tier) []byte {
	// mumble mumble, something with cap, save the underlying piece
	// can't do that while inserting though!

	r := make([]byte, len(tier)*int(CHK_SIZE))
	for i, chk := range tier {
		copy(r[i*int(CHK_SIZE) : i*int(CHK_SIZE+KEYSIZE)],chk.key[:])
		copy(r[i*int(CHK_SIZE+KEYSIZE) : (i+1)*int(CHK_SIZE)], chk.lookup[:])
	}
	return r
}

func (h DB) borrow(level uint8) []byte {
	// now treat tiers like a number, with each tier being a digit
	// and subtract 1 piece at a time until you're at 0
	var tier = h.tiers[level]
	if len(tier) == 0 {
		if int(level) >= len(h.tiers) {
			return nil
		}
		piece := h.borrow(level + 1)
		if piece == nil {
			return nil
		}
		tier = explode(piece)
	}
	nexthash := tier[0]
	tier = tier[1:]
	h.tiers[level] = tier
	return h.Extract(nexthash)
}

type Root struct {
	chk CHK
	depth uint8
}



// export a hash tree to a writer, given its root
func (h DB) Export(key Root, dest io.Writer) error {
	at := 0

	h.tiers = make([]tier, key.depth)
	h.tiers[key.depth-1] = tier{key.chk} // and everything below it is 0
	for piece := h.borrow(0); piece != nil; piece = h.borrow(0) {
		if n, err := dest.Write(piece); err != nil {
			return err
		}
	}
	if(h.err != nil) {
		return h.err
	}
	return nil
		
}

func (h DB) ExportFile(key Root, dest string) error {
	f, err := os.Create(dest + ".tmp")
	if err != nil {
		return err
	}
	defer f.Close()
	return h.Export(key, f)
}

func (h DB) carry(chk CHK, level int) {
	if level == 0 && len(h.tiers) == 0 {
		h.tiers = []tier{[]CHK{chk}}
	} else if len(h.tiers) < level {
		h.tiers = append(h.tiers, tier{chk})
	} else {
		var tiero = h.tiers[level]
		tiero = append(tiero, chk)
		if uint(len(tiero)) > CHK_PER_PIECE {
			var chk = h.Insert(conjoin(tiero))
			h.tiers[level] = tier{}
			h.carry(chk, level+1)
		}
	}
}

func (h DB) Import(reader io.Reader) (depth uint8, root CHK) {
	if len(h.tiers) != 0 {
		panic("ugh, concurrency")
	}
	p := make([]byte, MAX_PIECE_SIZE)
	for {
		n, err := reader.Read(p)
		if n <= 0 {
			break
		}
		new := h.Insert(p[:n])
		h.carry(new, 0)
	}
	depth = uint8(len(h.tiers)) // XXX: +1 ?
	toptier := h.tiers[len(h.tiers)-1]
	if len(toptier) != 1 {
		new := h.Insert(conjoin(toptier))
		return depth, new
	}
	// XXX: um.....
	panic("Never reach here...?")
}

var ziv [calgo.BlockSize]byte // just leave this zero

func (h DB) Insert(piece []byte) CHK {
	key := DeriveKey(piece, nil)
	block, err := calgo.NewCipher(key[:])
	if err != nil {
		panic(err)
	}
	stream := cipher.NewCTR(block, ziv[:])

	// hmm, this is destructive...
	stream.XORKeyStream(piece, piece)
	lookup := makeHash(piece)
	if h.store.Put(lookup, piece); err != nil {
		panic(err)
	}
	return CHK{
		key:    key,
		lookup: lookup,
	}
}

func (h DB) Extract(chk CHK) []byte {
	var piece []byte
	for {
		if piece, err := h.store.Get(chk.lookup); err != nil {
			// check if not found error
			if err := h.Fetch(chk.lookup); err != nil {
				panic(err);
			}
		} else {
			break
		}
	}
	block, err := calgo.NewCipher(chk.key[:])
	if err != nil {
		panic(err)
	}
	stream := cipher.NewCTR(block, ziv[:])
	stream.XORKeyStream(piece, piece)

	return piece
}
