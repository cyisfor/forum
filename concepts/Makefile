$(error make sucks)
TEXTS:=$(wildcard *.txt)

HTMLS:=$(patsubst %.txt,html/%.html,$(TEXTS))

all: $(HTMLS)

$(HTMLS): html

html: 
	mkdir -p html

html/%.html: %.txt
	sh $<.sh || sh general.sh
	~/code/htmlish/parse <$< >$@
	touch -r $< $@

@PHONY: html

