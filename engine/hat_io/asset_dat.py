try:
    from . import binary
    from .asset import File
except ImportError:
    import binary
    from asset import File

class LaytonPuzzleData(File):
    def __init__(self):
        File.__init__(self)
        self.idExternal = None
        self.idInternal = None
        self.idLocation = None
        self.idHandler = None
        self.idBackgroundBs = None
        self.idBackgroundTs = None
        self.idReward = None

        self.textName = None
        self.textPrompt = None
        self.textPass = None
        self.textFail = None
        self.textHint = [None,None,None]
        
        self.decayPicarots = [None,None,None]
        self.unks = [None,None,None,None]
    
    def load(self, data):

        def seekAndReadNullTerminatedString(offset, reader):
            prevOffset = reader.tell()
            reader.seek(offset)
            output = reader.readNullTerminatedString('shift-jis')
            reader.seek(prevOffset)
            return output

        reader = binary.BinaryReader(data = data)

        self.idExternal = reader.readU2()
        offsetText = reader.readU2()
        self.textName = reader.readPaddedString(48, 'shift-jis')
        self.unks[0] = reader.read(1)
        self.decayPicarots = [reader.readUInt(1), reader.readUInt(1), reader.readUInt(1)]
        self.unks[1] = reader.read(1)
        self.idLocation = reader.readUInt(1)
        self.idHandler = reader.readUInt(1)
        self.idBackgroundBs = reader.readUInt(1)
        self.unks[2] = reader.read(1)
        self.unks[3] = reader.read(1)
        self.idBackgroundTs = reader.readUInt(1)
        self.idReward = reader.readUInt(1)
        self.textPrompt = seekAndReadNullTerminatedString(reader.readU4() + offsetText, reader)
        self.textPass = seekAndReadNullTerminatedString(reader.readU4() + offsetText, reader)
        self.textFail = seekAndReadNullTerminatedString(reader.readU4() + offsetText, reader)
        for indexHint in range(3):
            self.textHint[indexHint] = seekAndReadNullTerminatedString(reader.readU4() + offsetText, reader)

    def save(self):
        pass