try:
    import defusedxml.ElementTree
    class ET:
        @staticmethod
        def parse(source):
            tree = defusedxml.ElementTree()
            tree.parse(source)
            return tree
except ImportError:
    import xml.etree.ElementTree as ET

from . import port
from io import StringIO

Element = ET.Element
SubElement = ET.SubElement

from deferred import inlineCallbacks,returnValue

import generic,memory,wrapper

from functools import partial

@inlineCallbacks
def extract(extracter,root):
    doc = yield memory.extract(extracter,root)
    doc = ET.parse(StringIO(doc))
    returnValue(doc)

def links(doc):
    return [(e.getAttribute('type'),e.getAttribute('src')) for e in doc.iter('link')]

def save(inserter,doc):
    inserter.add(doc.tostring())

class Loader(wrapper.Wrapper):
    def __init__(self,sub,dest):
        super().__init__(sub)
        self.dest = dest
    def requestPiece(self,subRequest,hasht,ctr,level):
        return subRequest(hasht,ctr,level).addCallback(self.appendPiece)
    def appendPiece(self,piece):
        self.dest.write(struct.pack('!H',len(piece)))
        self.dest.write(piece)

DOCTYPE = "message/info"

'''The <link> element has attributes that act like rfc822, src=hash, filename=whatever typetype=content-type'''

@inlineCallbacks
def load(extracter,root,dest,level=0):
    if level >= 2:
        return
    extracter = Loader(extracter,dest)
    doc = yield extract(extracter,root)
    for type,link in links(doc):
        if type == DOCTYPE and level < 2:
            yield load(extracter,link,dest,level+1)
        else:
            yield generic.extract(extracter,link)

def flatten(l):
    try:
        for i in l:
            yield i
            for derp in flatten(i):
                yield derp
    except TypeError as ea:
        yield l

def toHTML(doc):
    root = doc.getroot()
    root.tag = 'html'
    for e in flatten(root):
        if e.tag == 'link':
            name = e.get('name')
            type = e.get('type')
            if not name:
                if type:
                    ext = type.rsplit('.',1)[-1]
                else:
                    ext = 'bin'
                name = 'unknown.'+ext
            href = 'http://127.0.0.1:{}/CHK@{};{}/{}'.format(port,e.get('src'),type,name)
            if e.get('inline'):
                e.tag = 'img'
                attr = 'src'
            else:
                e.tag = 'a'
                attr = 'href'
            e.attrib.clear()
            if name:
                e.set('title',name)
            e.set(attr,href)
    head = Element('head')
    title = SubElement(head,'title')
    title.text = 'Test output as HTML'
    body = Element('body')
    body.extend(iter(root))
    root.clear()
    root.extend((head,body))
    return doc

def buildLink(src,type,inline=False,name=None,parent=None):
    if parent is None:
        e = Element('link')
    else:
        e = SubElement(parent,'link')
    e.set('src',src)
    e.set('type',type)
    if inline:
        e.set('inline',True)
    if name is not None:
        e.set('name',name)
    return e
