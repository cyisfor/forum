import logging

import dbm
from contextlib import contextmanager

def open(path):
    while True:
        try:
            return dbm.open(path,'cs')
        except OSError as e:
            if e.errno == errno.EAGAIN:
                logging.info(16,'again?')
                time.sleep(0.1)
            else:
                raise

@contextmanager
def aShelf(path):
    db = None
    try:
        db = open(path)
        yield db
    finally:
        if db:
            db.close()

