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

from io import StringIO

Element = ET.Element
SubElement = ET.SubElement

from deferred import inlineCallbacks,returnValue

import generic,memory,wrapper

from functools import partial
import os
from itertools import count

@inlineCallbacks
def extract(extracter,root):
    doc = yield memory.extract(extracter,root)
    doc = ET.parse(StringIO(doc))
    returnValue(doc)

def links(doc):
    return [(e.getAttribute('type'),e.getAttribute('key')) for e in doc.iter('link')]

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

'''The <link> element has attributes that act like rfc822, key=hash, filename=whatever typetype=content-type'''

@inlineCallbacks
def export(extracter,root,dest,level=0):
    if level >= 2:
        return
    extracter = Loader(extracter,dest)
    doc = yield extract(extracter,root)
    for type,link in links(doc):
        if type == DOCTYPE and level < 2:
            yield export(extracter,link,dest,level+1)
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

import mimetypes
mimetypes.init()
try:
    import magic
    magic = magic.Magic(mime=True)
    def guessType(path):
        return magic.from_file(path)
except ImportError:
    from subprocess import Popen,PIPE,call
    if 0==call(['file','--help']):
        def guessType(path):
            pid = Popen(['file','--mime-type',path],stdout=PIPE)
            try: return pid.stdout.read().rstrip().split(": ",1)[-1]
            finally:
                pid.stdout.close()
                pid.wait()
    else:
        import imghdr,mimetypes
        def guessType(path):
            lesser = imghdr.what(path)
            if lesser: return 'image/'+lesser
            return mimetypes.guess_type(path)[0]

guessName = os.path.basename;

@inlineCallbacks
def create(inserter,doc):
    root = doc.getroot()
    for e in flatten(root):
        if e.tag == 'attach':
            path = e['key']
            if not os.path.exists(path):
                raise RuntimeError("Could not find path to attach ",path)
            type = e.get('type')
            with open(path,'rb') as inp:
                if not type:
                    type = guessType(inp)
                name = e.get('name')
                if not name:
                    name = guessName(os.path.basename(path))
                uri = yield inserter.addFile(inp)
            e.tag = 'link'
            e.key = uri
    root = yield inserter.addPieces(doc.toPrettyXML())
    returnValue(root)

ucount = count(0)

def extractAlsoLinks(extracter,root,level=0):
    doc = yield extract(extracter,root)
    for link in links(doc):
        name = e.get('name')
        type = e.get('type')
        if not name:
            if type:
                ext = type.rsplit('.',1)[-1]
            else:
                ext = 'bin'
            name = 'unknown.{}.{}'.format(next(ucount),ext)
        sub = Key(e.get('key'))
        pextracter = ProgressMeter(extracter,self.place)
        yield generic.extractToFile(pextracter,sub,name)
        if pextracter.done:
            e.location = name
        else:
            e.location = self.place+'/progress/'+sub+'.png'
        if type == DOCTYPE and level < 2:
            yield extractAlsoLinks(extracter,sub)
    returnValue(doc)


@inlineCallbacks
def toHTML(extracter,root):
    # do this every refresh, to update completed files?
    doc = yield extractAlsoLinks(root)
    root = doc.getroot()
    root.tag = 'html'
    for e in flatten(root):
        if e.tag == 'link':
            href = e['location']
            if e.get('inline'):
                e.tag = 'img'
                attr = 'src'
            else:
                e.tag = 'a'
                attr = 'href'
            e.attrib.clear()
            name = e.get('name')
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
    returnValue(doc)

def buildLink(key,type,inline=False,name=None,parent=None):
    if parent is None:
        e = Element('link')
    else:
        e = SubElement(parent,'link')
    e.set('key',key)
    e.set('type',type)
    if inline:
        e.set('inline',True)
    if name is not None:
        e.set('name',name)
    return e
