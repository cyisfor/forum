import (
	calgo "aes" // blowfish, salsa20, whatever
	"crypto"
	"crypto/cipher"
	"crypto/rand"
	"crypto/sha256" // this is hard to generalize
	"io"
	"math/rand"
	"os"

	"github.com/syndtr/goleveldb/leveldb"
)

type Piece []byte

const KEYSIZE = 0x20 // AES-256
var CHKSIZE = crypto.SHA256.Size()

var makeHash = sha256.Sum256

type CHK struct {
	key  [KEYSIZE]byte
	echk [CHKSIZE]byte
}

type tier []CHK
type tiers []tier

type hashdb struct {
	store *leveldb.DB
	tiers tiers
}

func HashTreeDB(place string) {
	return hashdb{
		store: tierdb.Open(place, &ldb.Options{
			// 128 mibibytes
			WriteBufferSize: 0x8000000,
			// compression on encrypted pieces?
			Compression: ldb.NoCompression,
			// storing 0xffff sized pieces, ey?
			BlockSize: 0x10000,
		}),
	}
}

func explode(piece []byte) []hash {
	tier = make([]hash, len(piece)/(KEYSIZE+CHKSIZE))
	for i, _ := range tier {
		tier[i] = CHK{
			key:  piece[i*(CHKSIZE+KEYSIZE) : i*(CHKSIZE+KEYSIZE)+KEYSIZE],
			echk: piece[i*(CHKSIZE+KEYSIZE)+KEYSIZE : (i+1)*(CHKSIZE+KEYSIZE)],
		}
	}
	return tier
}

func conjoin(tier tier) []byte {
	// mumble mumble, something with cap, save the underlying piece
	// can't do that while inserting though!

	r = make([]byte, len(tier)*(KEYSIZE+CHKSIZE))
	for i, chk := range tier {
		r[i*(CHKSIZE+KEYSIZE) : i*(CHKSIZE+KEYSIZE)+KEYSIZE] = chk.key
		r[i*(CHKSIZE+KEYSIZE)+KEYSIZE : (i+1)*(CHKSIZE+KEYSIZE)] = chk.hash
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

func (h hashdb) Export(chk []byte, dest *io.Writer) error {
	if len(chk) != CHKSIZE {
		return BadCHK(chk)
	}
	depth := chk[0]
	at := 0

	h.tiers = make([]Tier, depth)
	var mchk = CHK{
		key:  chk[1:KEYSIZE],
		echk: chk[KEYSIZE:],
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
		if len(tier) > CHKPERPIECE {
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
	p := make([]byte, MAXPIECESIZE)
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

func (h hashdb) Insert(piece []byte) CHK {
	iv := make([]byte, calgo.BlockSize)
	key := make([]byte, 0x20)
	rand.Rand(key)
	block, err := calgo.NewCipher(key)
	if err != nil {
		panic(err)
	}
	rand.Rand(iv)
	stream := cipher.NewCtr(block, iv)

	// hmm, this is destructive...
	stream.XORKeyStream(piece, piece)
	echk := makeHash(piece)
	// remember MAXPIECESIZE must be 0xffff /minus/ the size of an IV
	// and maybe a command byte or something
	h.ldb.Put(echk, append(iv, piece...))
	return CHK{
		key:  key,
		echk: echk,
	}
}

func (h hashdb) Extract(chk CHK) []byte {
	var piece []byte
	for {
		if piece, err = h.ldb.Get(chk.echk); err != nil {
			// check if not found error
			h.Fetch(chk.echk)
		} else {
			break
		}
	}
	block, err := calgo.NewCipher(chk.key)
	if err != nil {
		panic(err)
	}
	iv = piece[:IVLEN]
	piece = piece[IVLEN:]

	stream := cipher.NewCtr(block, iv)
	stream.XORKeyStream(piece, piece)

	return piece
}
