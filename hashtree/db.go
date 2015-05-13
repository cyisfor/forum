package hashtree

import (
	calgo "crypto/aes"
	"crypto/cipher"
	"crypto/sha256" // this is hard to generalize
	"io"
	"os"
	"sync"
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
const MAX_EFFECTIVE_PIECE_SIZE = MAX_PIECE_SIZE - uint(IV_SIZE) - 5

const CHK_PER_PIECE = MAX_EFFECTIVE_PIECE_SIZE / uint(CHK_SIZE)

var makeHash = sha256.Sum256

const HashSize = sha256.Size

type Hash [HashSize]byte

// an abstract key/value Store. A leveldb can work for this.
type KeyValueStore interface {
	// don't necessarily put, but definitely queue it up.
	Put(Hash, []byte) error
	Get(Hash) ([]byte, error)
	Close() error
}

type Fetcher interface {
	Fetch(Hash) error
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
	Key    [KEYSIZE]byte
	Lookup Hash
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
	Store KeyValueStore
	fetcher Fetcher
	tiers tiers
	err   error
	recovery_handler func(x interface{}) error
	wlock sync.Mutex
}

func New(
	Store KeyValueStore,
	fetcher Fetcher,
	recovery_handler func (x interface{}) error) DB {
	self := DB{
		Store: Store,
		fetcher: fetcher,
		recovery_handler: recovery_handler,
	}

	return self
}

func explode(piece []byte) tier {
	var tier = make(tier, len(piece)/int(CHK_SIZE))
	for i, _ := range tier {
		t := CHK{}
		copy(t.Key[:], piece[i*int(CHK_SIZE):i*int(CHK_SIZE+KEYSIZE)])
		copy(t.Lookup[:], piece[i*int(CHK_SIZE+KEYSIZE):(i+1)*int(CHK_SIZE)])
		tier[i] = t
	}
	return tier
}

func conjoin(tier tier) []byte {
	// mumble mumble, something with cap, save the underlying piece
	// can't do that while inserting though!

	r := make([]byte, len(tier)*int(CHK_SIZE))
	for i, chk := range tier {
		copy(r[i*int(CHK_SIZE):i*int(CHK_SIZE+KEYSIZE)], chk.Key[:])
		copy(r[i*int(CHK_SIZE+KEYSIZE):(i+1)*int(CHK_SIZE)], chk.Lookup[:])
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
	CHK   CHK
	Depth uint8
}

// export a hash tree to a writer, given its root
func (h DB) ExportStream(key Root, dest io.Writer) (fail error) {
	defer func() {
		fail = recover().(error)
	}()

	h.tiers = make([]tier, key.Depth)
	h.tiers[key.Depth-1] = tier{key.CHK} // and everything below it is 0
	for piece := h.borrow(0); piece != nil; piece = h.borrow(0) {
		if n, err := dest.Write(piece); err != nil {
			return err
		} else if n != len(piece) {
			panic("Partial write")
		}
	}
	if h.err != nil {
		return h.err
	}
	return nil

}

func (h DB) export_parallel(chk CHK,
	breadth int64,
	depth uint8,
	dest io.WriteSeeker,
	parent *sync.WaitGroup) {

	// probably good to guarantee Done by defer, but not Wait unless
	// successfully dispatched
	defer parent.Done()

	defer func() {		
		if x := recover(); x != nil {			
			h.err = h.recovery_handler(x)
		}
	}()

	piece := h.Extract(chk)
	if depth == 0 {
		h.wlock.Lock()
		defer h.wlock.Unlock()
		_, err := dest.Seek(breadth*int64(MAX_EFFECTIVE_PIECE_SIZE), 0)
		if err != nil {
			panic(err)
		}
		n, err := dest.Write(piece)
		if err != nil {
			panic(err)
		}
		if n != len(piece) {
			panic("Partial disk write")
		}
		return
	}
	head := breadth * int64(MAX_EFFECTIVE_PIECE_SIZE)
	chks := explode(piece)
	var wait = sync.WaitGroup{}
	wait.Add(len(chks))
	for i, chk := range chks {
		// XXX: should probably have error reporting wrapper
		go h.export_parallel(chk,
			head+int64(i)*int64(MAX_EFFECTIVE_PIECE_SIZE),
			depth-1,
			dest,
			&wait)
	}
	wait.Wait()
}

// export a hash tree to a writer, in parallel, with swarming!
func (h DB) Export(root Root, dest io.WriteSeeker) {
	if h.err != nil {
		panic(h.err)
	}
	var wait = sync.WaitGroup{}
	wait.Add(1)
	h.export_parallel(root.CHK, 0, root.Depth, dest, &wait)
	wait.Wait()
	/* there could be several errors along the way,
	network failures, disk failures, timeouts, user cancellation, should
	use an error handler, not return a single error for all the things
	that may have went wrong during this export. 
...but we still need to know whether the file is done or not.
*/
	if h.err != nil {
		panic(h.err)
	}
}

func (h DB) ExportFile(key Root, dest string) {
	f, err := os.Create(dest + ".tmp")
	if err != nil {
		panic(err)
	}
	defer f.Close()
	h.Export(key, f)
	f.Sync()
	err = os.Rename(dest + ".tmp",dest)
	if err != nil {
		println("MS sucks")
		os.Remove(dest)
		err := os.Rename(dest+".tmp",dest)
		if err != nil {
			panic(err)
		}
	}
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
		if err != nil {
			if err == io.EOF {
				break
			}
			panic(err)
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
	if h.Store.Put(lookup, piece); err != nil {
		panic(err)
	}
	return CHK{
		Key:    key,
		Lookup: lookup,
	}
}

func (h DB) Extract(chk CHK) []byte {
	var piece []byte
	var err error
	for {
		if piece, err = h.Store.Get(chk.Lookup); err != nil {
			err = h.fetcher.Fetch(chk.Lookup)
			if err != nil {
				panic(err)
			}
			if piece, err = h.Store.Get(chk.Lookup); err != nil {
				panic(err)
			}
		} else {
			break
		}
	}
	block, err := calgo.NewCipher(chk.Key[:])
	if err != nil {
		panic(err)
	}
	stream := cipher.NewCTR(block, ziv[:])
	stream.XORKeyStream(piece, piece)

	return piece
}
