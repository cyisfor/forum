import logging
from bytelib import bytes_to_long,long_to_bytes

class Counter:
    def __init__(self,source=None):
        self.source = source
        if source is None:
            self.db = {}
        else:
            self.db = source
    def ref(self,key):
        refs = self.db.get(key)
        if refs is None:
            refs = 0
        else:
            refs = bytes_to_long(refs)+1
        logging.info(20,'reffing',key,refs)
        self.db[key] = long_to_bytes(refs)
    def unref(self,key):
        refs = bytes_to_long(self.db.get(key)) - 1
        logging.info(20,'unreffing',key,refs)
        if not refs:
            if refs is 0:
                del self.db[key]
            logging.info(20,'want delete',key)
            return True
        self.db[key] = long_to_bytes(refs)
        return False
