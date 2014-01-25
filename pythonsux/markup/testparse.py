import parse,os,sys
from io import StringIO

doc = parse.ET.parse(StringIO('''<doc>
<link src="hash" type="text/plain">
c
<link src="hash2" type="beep">Q</link>
</link>
d
</doc>'''))
parse.toHTML(doc)
doc.write(sys.stdout.detach())

