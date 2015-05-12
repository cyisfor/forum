import (
	"code.google.com/p/leveldb-go/leveldb"
)

type LevelDB struct {
	// don't bother with promotions
	l       *leveldb.LevelDB
	pending Batch
}

func (d LevelDB) Put(Hash k, byte []v) error {
	d.pending.Set(k, v)
	if len(d.pending) > CUTOFF {
		return d.Flush()
	}
	return nil
}

func (d LevelDB) Flush() error {
	d.l.apply(d.pending)
	d.pending = nil
}

func (d LevelDB) Get(Hash k) ([]byte, error) {
	if d.pending != nil {
		if err := d.Flush(); err != nil {
			return nil, err
		}
	}
}
		
