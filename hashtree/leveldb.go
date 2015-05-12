package hashtree

import (
	// avoid "code.google.com/p/leveldb-go/leveldb" it corrupts like heck
	"github.com/syndtr/goleveldb/leveldb"
	"github.com/syndtr/goleveldb/leveldb/filter"
	"github.com/syndtr/goleveldb/leveldb/opt"
)

// a wrapper for leveldb that is easier to write, but doesn't guarantee
// an arriving piece will be available to Get until after the Flush

type LevelDB struct {
	// don't bother with promotions
	l       *leveldb.LevelDB
	pending *leveldb.Batch
}

const CUTOFF = 0x10

func (d LevelDB) Put(Hash k, byte []v) error {
	if d.pending == nil {
		d.pending = new(leveldb.Batch)
	}
	d.pending.Put(k, v)
	if len(d.pending) > CUTOFF {
		return d.Flush()
	}
	return nil
}

func (d LevelDB) Flush() error {
	pending := d.pending
	d.pending = nil
	return d.l.Write(d.pending)
}

func (d LevelDB) Get(Hash k) ([]byte, error) {
	if d.pending != nil {
		if err := d.Flush(); err != nil {
			return nil, err
		}
	}
}

func (d LevelDB) Close() error {
	err := d.Flush()
	d.l.Close()
}

func LevelDBCreate(path string) KeyValueStore {
	db, err := leveldb.OpenFile(path, &opt.Options{
		Filter:                        filter.NewBloomFilter(0x10),
		BlockCacheCapacity:            0x8000000,
		BlockSize:                     0x10000,
		CompactionTotalSizeMultiplier: 0x10,
		CompactionTotalSize:           0x100000,
		Compression:                   opt.NoCompression,
		IteratorSamplingRate:          0x400000,
		OpenFilesCacheCapacity:        0x400,
		// these pretty much just prevent the database from being recovered...
		Strict:      opt.NoStrict,
		WriteBuffer: 0x1000000,
	})
	if err != nil {
		panic(err)
	}
	return LevelDB{l: db}
}
