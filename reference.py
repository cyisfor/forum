import shelve,logging

class Counter:
    def __init__(self,source=None):
        self.source = source
        if source is None:
            self.db = {}
        else:
            self.db = shelve.open(source)
    def ref(self,key):
        refs = self.db.get(key,0)+1
        logging.info(20,'reffing',key,refs)
        self.db[key] = refs
    def unref(self,key):
        refs = self.db.get(key) - 1
        logging.info(20,'unreffing',key,refs)
        if not refs:
            if refs is 0:
                del self.db[key]
            logging.info(20,'want delete',key)
            return True
        self.db[key] = refs
        return False
    def close(self):
        if self.source:
            self.db.close()
