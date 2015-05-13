package main

import (
	"encoding/base64"
	"log"
	"net"
	"net/http"
	"net/url"
	"os"
	"os/user"
	"path"
	"path/filepath"
	"strconv"
	// relative imports???
	"derp/cy/forum/display"
	"derp/cy/forum/hashtree"
)

func buildDir(root string, components ...string) string {
	var res = root
	for _, component := range components {
		res = filepath.Join(res, component)
		if err := os.Mkdir(res, 0700); err != nil && !os.IsExist(err) {
			panic(err)
		}
	}
	return res
}

type PathInfo struct {
	name  string
	minor string
	major string
	root  hashtree.Root
}

type BadPath string

func (b BadPath) Error() string {
	return "Bad Path " + string(b)
}

func stripslash(rest string) string {
	if len(rest) == 0 {
		return ""
	}
	for rest[len(rest)-1] == '/' {
		rest = rest[:len(rest)-1]
	}
	return rest
}

func Encode(b hashtree.Hash) string {
	return base64.RawURLEncoding.EncodeToString(b[:])
}

func Decode(s string) (b []byte) {
	b, err := base64.RawURLEncoding.DecodeString(s)
	if err != nil {
		panic(err)
	}
	return
}

func parsePath(rest string) (self PathInfo, fail error) {
	defer func() {
		if x := recover(); x != nil {
			fail = x.(error)
		}
	}()
	if len(rest) == 0 {
		panic(BadPath(rest))
	}
	if rest[len(rest)-1] == '/' {
		panic(BadPath("never a directory: " + rest))
	}
	rest, name := path.Split(rest)
	rest, depth := path.Split(stripslash(rest))
	rest, key := path.Split(stripslash(rest))
	rest, lookup := path.Split(stripslash(rest))
	rest, minor := path.Split(stripslash(rest))
	rest, major := path.Split(stripslash(rest))

	if s, err := url.QueryUnescape(name); err != nil {
		panic(err)
	} else {
		self.name = s
	}
	// MIME types shouldn't have URL encoded stuff in them, right...?
	self.minor = minor
	self.major = major
	copy(self.root.CHK.Key[:], Decode(key))
	copy(self.root.CHK.Lookup[:], Decode(lookup))
	i, err := strconv.ParseInt(depth, 0x10, 8)
	if err != nil {
		panic(err)
	}
	self.root.Depth = uint8(i)

	return self, nil
}

func listenForPieces(db hashtree.DB) {
	pn, err := net.ListenPacket("udp", ":8080")
	if err != nil {
		panic(err)
	}
	println("listening for pieces, yay")
	var buf = make([]byte, hashtree.MAX_PIECE_SIZE)
	for {
		n, addr, err := pn.ReadFrom(buf)
		if err != nil {
			println("Error reading from network",err)
		}
		/* TODO: every time a piece comes in, if it's a signature piece, (what about signature pieces that aren't aimed at us? like someone wants to store their messages on our computer?) then pass its root to the message database, a second database that stores messages that have arrived, and re-exports them to examine their metadata, and stuff.

		Be sure to identify every signature piece ENCRYPTED to us, because that means it's a private message for one of our identities.

				The folder display should use this second database to show folders, not query the entire hashtree database every time. But the second database ONLY has metadata and root hashes, so to get the actual messages you use the first database to figure what to send over the wire.
		*/
		// sophisticated reputation management:
		print("got", Encode(db.Insert(buf[:n]).Lookup), "from", addr)
	}
}

var outgoing net.PacketConn

func init() {
	var err error
	outgoing, err = net.ListenPacket("udp", ":0")
	if err != nil {
		panic(err)
	}
}

func sendPiece(piece []byte, dest net.Addr) {
	outgoing.WriteTo(piece, dest)
}

type Fetcher struct{}

func (f Fetcher) Fetch(hash hashtree.Hash) error {
	panic("ehunno chekc net")
}

func main() {
	var user, err = user.Current()
	var home string
	if err != nil {
		println("warning: Can't find your home directory")
		home = "."
	} else {
		home = user.HomeDir
	}
	var base = buildDir(home, ".local", "forum")
	var db = hashtree.New(
		hashtree.LevelDBCreate(filepath.Join(base, "pieces.leveldb")),
		Fetcher{},
		func(x interface{}) error {
			print("failure", x)
			return x.(error)
		})

	go listenForPieces(db)

	var cache = buildDir(base, "cache")
	clear := func() {
		if f, err := os.Open(cache); err != nil {
			panic(err)
		} else {
			defer f.Close()
			for {
				ns, err := f.Readdirnames(100)
				if err != nil {
					break
				}
				for _, n := range ns {
					_ = os.Remove(filepath.Join(cache, n))
				}
			}
		}
	}
	// clear cache on start/finish
	clear()
	defer clear()

	var static = buildDir(base, "static")

	http.Handle("/static/", http.FileServer(http.Dir(static)))
	http.Handle("/", display.New(db.Store))
	//http.Handle("/message", MessageFormatter{})
	http.HandleFunc("/chk/", func(w http.ResponseWriter, r *http.Request) {
		path, err := parsePath(r.URL.Path)
		values := r.URL.Query()
		charset, hasCharset := values["charset"]
		if err != nil {
			print(err)
			return
		}
		h := w.Header()
		ct := path.major + "/" + path.minor
		if hasCharset {
			ct = ct + "; " + charset[0]
		}
		h["Content-Type"] = []string{ct}
		cached := filepath.Join(cache, Encode(path.root.CHK.Lookup))
		for {
			if f, err := os.Open(cached); err == nil {
				if s, err := f.Stat(); err != nil {
					panic(err)
				} else {
					http.ServeContent(w, r, "herp", s.ModTime(), f)
				}
			}
			f,err := os.Create(cached)
			if err != nil {
				panic(err)
			}
			defer f.Close()
			db.Export(path.root, f)			
		}
	})

	log.Fatal(http.ListenAndServe(":9090", nil))
}
