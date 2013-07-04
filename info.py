class Info:
    def __init__(self,maximumPieceSize,hashSize):
        self.keysPerPiece = int(maximumPieceSize / hashSize)
        self.maximumPieceSize = maximumPieceSize
        self.hashSize = hashSize
