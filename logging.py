# I r so sly

currentStage = 18

import sys,os

from pprint import pprint

skips = set()

alog = open('log.html','wt')

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

def color(c,what,bg=False,element='span'):
    style = '{}: {}'.format(
            ('background-color' if bg else 'color'),
            c)
    if bg:
        style = style + '; width=100%'
    return '<{} style="{}">{}</{}>'.format(
            element,
            style,
            what,
            element)

def bgcolor(c,what):
    return color(c,what,True)

def rainbow(hue):
    return 'hsl({},100%,40%)'.format(hue%256)

def li(c,what):
    return color(c,what,True,'li')

from itertools import count
count = count(1)

hues = {}
nexthue = 0

def log(*a):
    global nexthue
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
    fname = f.f_code.co_filename
    if fname in hues:
        hue = hues[fname]
    else:
        hue = nexthue
        hues[fname] = hue
        nexthue += 79
    alog.write(li(('#E8E8E8' if next(count)%2==0 else 'white'),
        color('red',str(stage)) + ' ' + color(rainbow(hue),os.path.basename(f.f_code.co_filename))+'('+str(f.f_lineno)+'): '+msg)+'\n')
    nexthue += 67

info = debug = error = log

alog.write('<html><head><title>Debug log</title></head><body><ul>\n')
