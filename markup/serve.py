import .parse
import generic,inserter
import uv

import http.server

class PieceCounter(wrapper.Wrapper):
    def __init__(self,extracter,handler):
        super().__init__(extracter)
        self.handler = handler
        self.wrap()
    def requestPiece(self,chk,ctr,depth):
        return super().requestPiece(chk,ctr,depth).addCallback(self.moarPiece)
    def moarPiece(self,value):
        self.handler.numpieces += 1
        return value

class Handler(http.server.SimpleHTTPRequestHandler):
    root = '/whateer/'
    top = '/usr/share/nginx/html/'+root
    extracter = None
    def setExtracter(self,extracter):
        self.extracter = PieceCounter(extracter,self)
    def do_GET(self):
        if not self.path.startswith(self.root+'/CHK/'):
            return super().do_GET()
        chk,name = self.path.rsplit('/',2)[-2:]
        if not os.path.exists(self.top + "/CHK/"+chk):
            self.checkCHK(chk)
            return
        return super().do_GET()
    def checkCHK(self,chk,name):
        loc = oj(top,chk)
        if not os.path.exists(loc):
            os.makedirs(loc)
        dest = oj(loc,name)
        self.numpieces = 0
        def showProgress():
            self.send_response("301","Try again later")
            self.send_header('Location',self.url)
            self.end_headers()
            self.wfile.write("show progerss {}".format(self.numpieces))
            uv.loop.stop()
        uv.Timer().start(showProgress,1000,False)
        def done(value):
            self.numpieces = 0
            self.send_response("301","Got it all.")
            self.send_header('Location',self.url);
            self.wfile.write("Got the entire chk hashtree thingy")
            uv.loop.stop()
            return value
        generic.extractToFile(self.extracter,dest,root).addCallbacks(done,done)
        # this will block for only one child worker.
        uv.loop.run()
        self.wfile.write("redirect to chk self")

class Server(http.server.HTTPServer,socketserver.ForkingMixIn): pass

server = Server(('::',10244),Handler)
server.serve_forever()
