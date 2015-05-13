package display

import (
	"derp/cy/forum/hashtree"
	"net/http"
)

type MessageListDisplayer struct {
	hashtree.KeyValueStore
}

func (s MessageListDisplayer) ServeHTTP(w http.ResponseWriter, r *http.Request) {	
	w.Write([]byte("fuck it"))
}

func New(db hashtree.KeyValueStore) http.Handler {
	return MessageListDisplayer{db}
}

