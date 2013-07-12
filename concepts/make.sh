generate() {
    sh ${src}.sh || sh general.sh
	footer="footer.html" ~/code/htmlish/parse <$src >$dest
	if older $src $sh; then
        touch -r $sh $dest
    else
        touch -r $src $dest
    fi
    #touch -r $src header.html
    echo $name
}

mkdir -p html
for src in *.txt; do
    name=${src%.txt}
    sh=${src}.sh
    dest=html/${name}.html
    if older $dest $src $sh footer.html; then
        generate
    fi
done
