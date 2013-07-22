# I r so sly

currentStage = 18

import sys,os

from pprint import pprint

skips = set()

if hasattr(sys, '_getframe'):
    currentframe = lambda: sys._getframe(1)
else: #pragma: no cover
    def currentframe():
        """Return the frame object for the caller's stack frame."""
        try:
            raise Exception
        except:
            return sys.exc_info()[2].tb_frame.f_back

def caller():
    f = currentframe().f_back.f_back
    while f.f_code in skips:
        f = f.f_back
    return f

def skip(f):
    skips.add(f.__code__)
    return f



def log(*a):
    if len(a)<2:
        stage = currentStage
        msg = a[0]
        a = []
    else:
        stage, msg, *a = a
        if stage < currentStage: return
    if isinstance(msg,str) and '%' in msg:
        try:
            msg = msg % tuple(a)
        except:
            print(msg,a)
            raise
    else:
        msg = str(msg) + ' ' + ' '.join((repr(i) for i in a))
    f = caller()
    sys.stderr.write(str(stage) + ' ' + os.path.basename(f.f_code.co_filename)+'('+str(f.f_lineno)+'): '+msg+"\n")

info = debug = error = log
