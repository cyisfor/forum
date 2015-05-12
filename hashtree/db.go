package hashtree

import (
	calgo "aes" // blowfish, salsa20, whatever
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256" // this is hard to generalize
	"io"
	"math/rand"
	"os"
)

type Piece []byte

const KEYSIZE uint8 = 0x20 // AES-256
var LOOKUP_SIZE uint8 = uint8(sha256.Size)

// eh, this could be false but it'll not compile if ever so
const KIV_SIZE = KEYSIZE

var makeHash = sha256.Sum256

type Hash [sha256.Size]byte

// an abstract key/value store. A leveldb can work for this.
type KeyValueStore interface {
	// don't necessarily put, but definitely queue it up.
	Put(Hash, []byte) error
	Get(Hash) ([]byte, error)
	Flush() error
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
func DeriveKey(piece []byte, bump []byte) [KEYSIZE]byte {
	var key [KEYSIZE]byte
	if bump != nil {
		input = append(input, bump...)
	}
	copy(key[:KEYSIZE], makeHash(input)[:])
	return key
}

type tier []CHK
type tiers []tier

/* An interface to a leveldb backed (?) hash database */
type DB struct {
	store KeyValueStore
	tiers tiers
}

func New(store KeyValueStore) {
	return DB{
		store: store,
		/*leveldb.Open(place, &ldb.Options{
			// 128 mibibytes
			WriteBufferSize: 0x8000000,
			// compression on encrypted pieces?
			Compression: ldb.NoCompression,
			// storing 0xffff sized pieces, ey?
			BlockSize: 0x10000,
		}),*/
	}
}

// size of the serialized CHK (key, lookup)
const CHK_SIZE = KEYSIZE + LOOKUP_SIZE

func explode(piece []byte) []hash {
	tier = make([]hash, len(piece)/CHK_SIZE)
	for i, _ := range tier {
		tier[i] = CHK{
			key:    piece[i*CHK_SIZE : i*CHK_SIZE+KEYSIZE],
			lookup: piece[i*CHK_SIZE+KEYSIZE : (i+1)*CHK_SIZE],
		}
	}
	return tier
}

func conjoin(tier tier) []byte {
	// mumble mumble, something with cap, save the underlying piece
	// can't do that while inserting though!

	r = make([]byte, len(tier)*CHK_SIZE)
	for i, chk := range tier {
		r[i*CHK_SIZE : i*CHK_SIZE+KEYSIZE] = chk.key
		r[i*CHK_SIZE+KEYSIZE : (i+1)*CHK_SIZE] = chk.hash
	}
	return r
}

func (h hashdb) borrow(level uint8) {
	// now treat tiers like a number, with each tier being a digit
	// and subtract 1 piece at a time until you're at 0
	tier = h.tiers[level]
	if len(tier) == 0 {
		if level >= len(h.tiers) {
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

// export a hash tree to a writer, given its root
func (h hashdb) Export(chk CHK, dest *io.Writer) error {
	if len(chk) != LOOKUP_SIZE {
		return BadCHK(chk)
	}
	depth := chk[0]
	at := 0

	h.tiers = make([]Tier, depth)
	var mchk = CHK{
		key:    chk[1:KEYSIZE],
		lookup: chk[KEYSIZE:],
	}
	h.tiers[depth-1] = []tier{mchk} // and everything below it is 0
	for piece := h.borrow(); piece; piece = h.borrow() {
		if n, err := dest.Write(piece); err != nil {
			panic(err)
		}
	}
}

func (h hashdb) ExportFile(chk []byte, dest string) error {
	if f, err := os.Create(dest + ".tmp"); err != nil {
		return error
	}
	defer f.Close()
	return h.Export(chk, f)
}

func (h hashdb) carry(hash s, level int) {
	if level == 0 && len(h.tiers) == 0 {
		h.tiers = []tier{{hash}}
	} else if len(h.tiers) < level {
		tier = []hash{hash}
		h.tiers = append(h.tiers, tier)
	} else {
		tier = h.tiers[level]
		tier = append(tier, hash)
		if len(tier) > CHK_PER_PIECE {
			new = h.Insert(conjoin(tier))
			h.tiers[level] = []tier{}
			carry(new, level+1)
		}
	}
}

func (h hashdb) Import(reader *io.Reader) (depth uint8, root CHK) {
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
	depth := len(h.tiers) // XXX: +1 ?
	toptier := h.tiers[len(h.tiers)-1]
	if len(toptier) != 1 {
		new := h.Insert(conjoin(toptier))
		return depth, new
	}
}

var ziv [calgo.BlockSize]byte // just leave this zero

func (h hashdb) Insert(piece []byte) (CHK, error) {
	key := make([]byte, 0x20)
	rand.Rand(key)
	block, err := calgo.NewCipher(key)
	if err != nil {
		panic(err)
	}
	stream := cipher.NewCtr(block, ziv)

	// hmm, this is destructive...
	stream.XORKeyStream(piece, piece)
	lookup := makeHash(piece)
	if h.store.Put(lookup, piece); err != nil {
		return nil, err
	}
	return CHK{
		key:    key,
		lookup: lookup,
	}, nil
}

func (h hashdb) Extract(chk CHK) ([]byte, error) {
	var piece []byte
	for {
		if piece, err = h.ldb.Get(chk.lookup); err != nil {
			// check if not found error
			h.Fetch(chk.lookup)
		} else {
			break
		}
	}
	block, err := calgo.NewCipher(chk.key)
	if err != nil {
		panic(err)
	}
	stream := cipher.NewCtr(block, ziv)
	stream.XORKeyStream(piece, piece)

	return piece
}
