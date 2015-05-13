package hashtree

import (
	// avoid "code.google.com/p/leveldb-go/leveldb" it corrupts like heck
	"github.com/syndtr/goleveldb/leveldb"
	"github.com/syndtr/goleveldb/leveldb/filter"
	"github.com/syndtr/goleveldb/leveldb/opt"
)

// a wrapper for leveldb that handles read/write options

type LevelDB struct {
	// don't bother with promotions
	l *leveldb.DB
}

func (d LevelDB) Put(k Hash, v []byte) error {
	return d.l.Put(k[:], v, nil)
}

func (d LevelDB) Get(k Hash) ([]byte, error) {
	return d.l.Get(k[:], nil)
}

func (d LevelDB) Close() error {
	return d.l.Close()
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
