package main

import (
	"net/http"
	"log"
	"net/url"
	"os/user"
	"path/filepath"
	// relative imports???
	"derp/cy/forum/hashtree"
)

func buildDir(root string, components ...string) string {
	var res = root
	for _, component := range components {
		res = filepath.Join(res, component)
		if err := os.Mkdir(res, 0700); err != nil && !os.isExist(err) {
			panic(err)
		}
	}
}

type PathInfo struct {
	name  string
	minor string
	major string
	chk   string
}

type BadPath struct {
	path string
}

func (b BadPath) Error() string {
	return "Bad Path " + b.path
}

func stripslash(rest) {
	if len(rest) == 0 {
		return nil, BadPath(rest)
	}
	if rest[len(rest)-1] == '/' {
		rest = rest[:len(rest)-1]
	}
	if len(rest) == 0 {
		return nil, BadPath(rest)
	}
	return rest, nil
}

func parsePath(rest string) (PathInfo, error) {
	if len(rest) == 0 {
		return nil, BadPath(rest)
	}
	if rest[len(rest)-1] == '/' {
		return nil, BadPath("never a directory: " + rest)
	}
	var self PathInfo
	rest, name := path.split(rest)
	if rest, err := stripslash(rest); err != nil {
		return nil, err
	}
	rest, minor := path.split(rest[:len(rest)-1])
	if rest, err := stripslash(rest); err != nil {
		return nil, err
	}

	rest, major := path.split(rest[:len(rest)-1])
	if rest, err := stripslash(rest); err != nil {
		return nil, err
	}

	rest, chk := path.split(rest[:len(rest)-1])
	if rest, err := stripslash(rest); err != nil {
		return nil, err
	}

	if s, err := url.QueryUnescape(name); err == nil {
		self.name = name
	}
	self.minor = minor
	self.major = major
	self.chk = chk
	// MIME types shouldn't have URL encoded stuff in them, right...?

	return self, nil
}

func listenForPieces(db) {
	pn, err := net.ListenPacket("udp", ":8080")
	print("listening for pieces, yay")
	var buf = make([]byte, MAXPIECESIZE)
	for {
		n, addr, err := pn.ReadFrom(buf)
		/* TODO: every time a piece comes in, if it's a signature piece, (what about signature pieces that aren't aimed at us? like someone wants to store their messages on our computer?) then pass its root to the message database, a second database that stores messages that have arrived, and re-exports them to examine their metadata, and stuff.

		Be sure to identify every signature piece ENCRYPTED to us, because that means it's a private message for one of our identities.

				The folder display should use this second database to show folders, not query the entire hashtree database every time. But the second database ONLY has metadata and root hashes, so to get the actual messages you use the first database to figure what to send over the wire.
		*/
		// sophisticated reputation management:
		print("got", db.Import(buf[:n]), "from", addr)
	}
}

var outgoing net.PacketConnection

func init() {
	outgoing, err := net.ListenPacket("udp", ":0")
	if err != nil {
		panic(err)
	}
}

func sendPiece(piece []byte, dest net.Addr) {
	outgoing.WriteTo(piece, dest)
}

func main() {
	base = buildDir(user.Current().HomeDir, ".local", "forum")
	db = hashtree.New(filepath.Join(base, "pieces.leveldb"))

	go listenForPieces(db)

	cache = buildDir(base, "cache")
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

	static = buildDir(base, "static")

	http.Handle("/static/", http.FileServer(http.Dir(static)))
	http.Handle("/", display.New(hashtree.DB))
	//http.Handle("/message", MessageFormatter{})
	http.HandleFunc("/chk/", func(w http.ResponseWriter, r *http.Request) {
		path, err := parsePath(r.URL.Path)
		values := r.URL.Query()
		charset, hasCharset = values["charset"]
		if err != nil {
			print(err)
			return
		}
		h := w.Header()
		ct := path.major + "/" + path.minor
		if hasCharset {
			ct = ct + "; " + charset
		}
		h["Content-Type"] = ct
		cached := filepath.Join(cache, path.chk)
		for {
			if f, err := os.Open(cached); err == nil {
				if s, err := f.Stat(); err != nil {
					panic(err)
				} else {
					http.ServeContent(w, req, name, s.ModTime(), f)
				}
			}
			if err := db.Export(path.chk, cached); err != nil {
				print(err)
				return
			}
		}
	})

	log.Fatal(s.ListenAndServe())
}
