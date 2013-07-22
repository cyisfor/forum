class Info:
    def __init__(self,maximumPieceSize,keySize):
        self.keysPerPiece = int(maximumPieceSize / keySize)
        self.maximumPieceSize = maximumPieceSize
        self.keySize = keySize
