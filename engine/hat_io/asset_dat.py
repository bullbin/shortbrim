try:
    from . import binary
    from .asset import File
except ImportError:
    import binary
    from asset import File

class Boundary():
    def __init__(self, cornerPos, boundarySize):
        self.posCorner = cornerPos
        self.sizeBounding = boundarySize

class TObj():
    def __init__(self, boundary, charId, tObjId):
        self.bounding = boundary
        self.idChar = charId
        self.idTObj = tObjId

class PlaceEvent():
    def __init__(self, boundary, eventObjId, eventId):
        self.bounding = boundary
        self.idEventObj = eventObjId
        self.idEvent = eventId

class LaytonPlaceData(File):

    def __init__(self):
        File.__init__(self)
        
        self.mapPos = (0,0)
        self.mapTsId = 0
        self.mapBgId = 0
        self.hints = []
        self.tObj = []
        self.objAnim = []
        self.objEvent = []
        self.objTap = []

    def load(self, data):
        reader = binary.BinaryReader(data=data)
        tempId = reader.readU4()
        reader.seek(20, 1)
        self.mapPos = (reader.readUInt(1), reader.readUInt(1))
        self.mapBgId = reader.readUInt(1)
        self.mapTsId = reader.readUInt(1)

        for _indexHint in range(4):
            tempHint = Boundary((reader.readUInt(1), reader.readUInt(1)),
                                (reader.readUInt(1), reader.readUInt(1)))
            if tempHint.posCorner != (0,0) and tempHint.sizeBounding != (0,0):
                self.hints.append(tempHint)
        
        for _indexTObj in range(16):
            tempBoundary = Boundary((reader.readUInt(1), reader.readUInt(1)),
                                    (reader.readUInt(1), reader.readUInt(1)))
            tempCharId = reader.readUInt(2)
            tempTObjId = reader.readUInt(4)
            if tempBoundary.posCorner != (0,0) and tempBoundary.sizeBounding != (0,0):
                self.tObj.append(TObj(tempBoundary, tempCharId, tempTObjId))

        for _indexAnim in range(12):
            tempPos = ((reader.readUInt(1), reader.readUInt(1)))
            tempAnimName = reader.readPaddedString(30, encoding='shift-jis')
            if tempPos != (0,0) and tempAnimName != "":
                self.objAnim.append((tempPos, tempAnimName))
        
        for _indexEvent in range(16):
            tempBoundary = Boundary((reader.readUInt(1), reader.readUInt(1)),
                                    (reader.readUInt(1), reader.readUInt(1)))
            tempEventObjId = reader.readUInt(2)
            tempEventId = reader.readUInt(2)
            if tempBoundary.posCorner != (0,0) and tempBoundary.sizeBounding != (0,0):
                self.objEvent.append(PlaceEvent(tempBoundary, tempEventObjId, tempEventId))

class LaytonPuzzleData(File):

    OFFSET_TEXT_DEFAULT = 112

    def __init__(self):
        File.__init__(self)
        self.idExternal = None
        self.idInternal = None
        self.idLocation = None
        self.idTutorial = None
        self.idHandler = None
        self.idBackgroundBs = None
        self.idBackgroundTs = None
        self.idReward = None

        self.idCharacterJudgeAnim = None

        self.textName = None
        self.textPrompt = None
        self.textPass = None
        self.textFail = None
        self.textHint = [None,None,None]

        self.flagEnableSubmit = False
        self.flagEnableBack = False
        
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
        self.idTutorial = reader.readUInt(1)
        self.decayPicarots = [reader.readUInt(1), reader.readUInt(1), reader.readUInt(1)]

        self.idCharacterJudgeAnim = reader.readUInt(1)
        self.unks[0] = self.idCharacterJudgeAnim & 0xf0
        self.idCharacterJudgeAnim = self.idCharacterJudgeAnim & 0x0f
        
        self.idLocation = reader.readUInt(1)
        self.idHandler = reader.readUInt(1)
        self.idBackgroundBs = reader.readUInt(1) 

        tempFlagByte = reader.readUInt(1)
        self.flagEnableBack = (tempFlagByte & 2 ^ 6) > 0
        self.flagEnableSubmit = (tempFlagByte & 2 ^ 4) > 0

        self.unks[1] = tempFlagByte     # Seems to be handler-related, as handlers often share the same unk here
        self.unks[2] = reader.read(1)   # Seems to be background related, as ranges between 1 and 4
        self.idBackgroundTs = reader.readUInt(1)
        self.idReward = reader.readInt(1)
        self.textPrompt = seekAndReadNullTerminatedString(reader.readU4() + offsetText, reader)
        self.textPass = seekAndReadNullTerminatedString(reader.readU4() + offsetText, reader)
        self.textFail = seekAndReadNullTerminatedString(reader.readU4() + offsetText, reader)
        for indexHint in range(3):
            self.textHint[indexHint] = seekAndReadNullTerminatedString(reader.readU4() + offsetText, reader)

    def save(self):
        # TODO - Checks for none

        writer = binary.BinaryWriter()
        writer.writeU2(self.idExternal)
        writer.writeU2(LaytonPuzzleData.OFFSET_TEXT_DEFAULT)
        writer.writePaddedString(self.textName, 48, 'shift-jis')
        writer.writeInt(self.idTutorial, 1)
        writer.writeIntList(self.decayPicarots, 1)
        
        # unk0
        writer.writeInt(self.idCharacterJudgeAnim, 1)  # Missing unk at 0xf0

        writer.writeInt(self.idLocation, 1)
        writer.writeInt(self.idHandler, 1)
        writer.writeInt(self.idBackgroundBs, 1)

        tempFlagByte = 0                # Unk: Suspicion
        if self.flagEnableSubmit:
            tempFlagByte += 2 ** 4
        
        writer.writeInt(tempFlagByte, 1) # Unk: handler

        writer.writeInt(1, 1)  # Unk: BG

        writer.writeInt(self.idBackgroundTs, 1)
        writer.writeInt(self.idReward, 1, signed=True)   # TODO - Abstraction

        textPointerOffset = writer.tell()
        textBankOffset = LaytonPuzzleData.OFFSET_TEXT_DEFAULT
        writer.align(textBankOffset)
        
        for indexText, text in enumerate([self.textPrompt, self.textPass, self.textFail, self.textHint[0], self.textHint[1], self.textHint[2]]):
            writer.insert((textBankOffset - LaytonPuzzleData.OFFSET_TEXT_DEFAULT).to_bytes(4, byteorder = 'little'), textPointerOffset + (indexText * 4))
            tempText = text.encode('shift-jis') + b'\x00'
            writer.write(tempText)
            textBankOffset += len(tempText)
        
        self.data = writer.data