import .parse
import generic,inserter

import http.server

class Handler(http.server.SimpleHTTPRequestHandler):
    top = '/usr/share/nginx/html/whateer/'
    extracter = None
    def do_GET(self):
        if self.path.startswith('/CHK'):
            match = chkpattern.match('/CHK@([^;]+);(.*)/(.*)')
            if match:
                chk,type,name = match.groups()
                self.checkCHK(chk,type,name)
                return
        return super().do_GET()
    def checkCHK(self,root,type,name):
        loc = oj(top,root)
        if not os.path.exists(loc):
            os.makedirs(loc)
        dest = oj(loc,name)
        generic.extractToFile(self.extracter,dest,root)
        # .addCallback then the socket server async handles callback argh

