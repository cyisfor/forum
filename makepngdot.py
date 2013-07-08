import os,sys
from itertools import count
from subprocess import call

os.chdir('deferredGraph')

for i in count(0):
    src = 'pass{}.dot'.format(i)
    if not os.path.exists(src): break
    print(i)
    dst = 'pass{}.png'.format(i)
    call(['neato','-T','png','-o',dst,src])
    with open('index{}.html'.format(i),'wt') as out:
        out.write('<html><head><title>derp</title>')
        if i > 0:
            out.write('<link rel=prev href="index{}.html" />'.format(i-1))
        derp = 'pass{}.png'.format(i+1)
        if os.path.exists(derp):
            out.write('<link rel=next href="index{}.html" />'.format(i+1))
        out.write('</head><body>\n')
        out.write('<p><img src="{}" width="100%" height="100%" /></p>'.format(dst))
        out.write('</body></html>')
