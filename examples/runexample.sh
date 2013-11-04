cd `dirname $0`
export PYTHONPATH=..:../deferred/
exec python3 "$@"
