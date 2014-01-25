import dependencies as d
pyuv = d.Import('pyuv',"apt-get install libuv-dev # Install libuv somehow.","pip3 install pyuv")
from functools import partial

loop = pyuv.Loop.default_loop()

Timer = partial(pyuv.Timer,loop)
TCP = partial(pyuv.TCP,loop)
UDP = partial(pyuv.UDP,loop)
Process = partial(pyuv.Process,loop)
