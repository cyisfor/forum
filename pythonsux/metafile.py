def insert(inserter,root,depth,name,mime,description):
    data = root + struct.pack('B',depth) + B.encode({
        'Name':name,
        'Type':mime,
        'Description':description})
    inserter.add(data)
    return inserter.finish()
