try:
    from . import binary
    from .asset import File
except ImportError:
    import binary
    from asset import File

from math import ceil

def calculateSaveChecksumFromBuffer(buffer, saveDataOffset, length):
    smallTotal = 0x0000ffff
    largeTotal = 0x0000ffff

    length = length >> 1
    while length != 0:
        chunkLength = min(length, 360)
        length -= chunkLength

        for _rep in range(chunkLength):
            smallTotal += int.from_bytes(buffer[saveDataOffset: saveDataOffset + 2], byteorder = 'little')
            largeTotal += smallTotal
            saveDataOffset += 2

        smallTotal = (smallTotal >> 0x10) + (smallTotal & 0xffff)
        largeTotal = (largeTotal >> 0x10) + (largeTotal & 0xffff)

    return (smallTotal >> 16) + (smallTotal & 0xffff) | ((largeTotal >> 16) + (largeTotal & 0xffff)) * 0x10000

def calculateSaveChecksumFromData(data):
    return calculateSaveChecksumFromBuffer(data, 0, len(data))

def fixChecksums(data):
    reader = binary.BinaryReader(data=data)
    output = binary.BinaryWriter()
    temp = binary.BinaryWriter()

    output.write(reader.read(16))
    reader.seek(4,1)
    temp.write(reader.read(196))
    output.writeU4(calculateSaveChecksumFromData(temp.data))
    output.write(temp.data)
    output.write(reader.read(56))
    for slot in range(3):
        reader.seek(4,1)
        temp = binary.BinaryWriter()
        temp.write(reader.read(796))
        output.writeU4(calculateSaveChecksumFromData(temp.data))
        output.write(temp.data)
        output.write(reader.read(80))
    output.write(reader.read(8192 - reader.tell()))
    return output.data

class PuzzleData():
    def __init__(self):
        self.wasEncountered = False
        self.wasSolved      = False
        self.wasPicked      = False
        self.levelDecay     = 0
        self.levelHint      = 0
    
    def setFromData(self, data):
        self.wasEncountered = ((data & 0x01) != 0) or ((data & 0x02) != 0)
        self.wasSolved = (data & 0x02) != 0
        self.wasPicked = (data & 0x80) != 0
        self.levelDecay = (data >> 2) & 0x03
        self.levelHint = (data >> 4) & 0x03

    @staticmethod
    def fromBytes(data):
        output = PuzzleData()
        output.setFromData(data)
        return output
    
    def toBytes(self):
        output = (self.wasPicked << 7) + (self.levelDecay << 2) + (self.levelHint << 4)
        if self.wasSolved:
            output += self.wasSolved << 1
        else:
            output += self.wasEncountered
        return output.to_bytes(1, byteorder = 'little')

class HintCoinRoomData():
    def __init__(self):
        self.hintsFound = [False, False, False, False]
    
    def setFromData(self, data):
        self.hintsFound = [data & 0x01 != False, data & 0x02 != False,
                           data & 0x04 != False, data & 0x08 != False]

    @staticmethod
    def fromBytes(data):
        output = HintCoinRoomData()
        output.setFromData(data)
        return output

    def toBytes(self):
        output = 0
        for hintIndex, hintFound in enumerate(self.hintsFound):
            if hintFound:
                output += (2 ** hintIndex)
        return output.to_bytes(1, byteorder = 'little')

class FlagsAsArray():
    def __init__(self, lenFlags, defaultState=False):
        self.flags = []
        for _index in range(lenFlags):
            self.flags.append(defaultState)
    
    def setSlot(self, state, slotIndex):
        if slotIndex > 0 and slotIndex < len(self.flags):
            self.flags[slotIndex] = state
    
    def getSlot(self, slotIndex):
        if slotIndex >= 0 and slotIndex < len(self.flags):
            return self.flags[slotIndex]
        return None

    def getLength(self):
        return len(self.flags)

    def clear(self):
        for flagIndex in range(len(self.flags)):
            self.flags[flagIndex] = False

    def __str__(self):
        output = ""
        for flagIndex, flagResult in enumerate(self.flags):
            output += "\n" + str(flagIndex) + "\t" + str(flagResult)
        if len(output) > 0:
            return output[1:]
        return output

    @staticmethod
    def fromBytes(data, maxLength=-1):
        if maxLength > 0:
            outLength = maxLength
        else:
            outLength = int(len(data) * 8)
        
        output = FlagsAsArray(outLength)
        tempData = int.from_bytes(data, byteorder = 'little')
        for power in range(outLength):
            if tempData & (2 ** power) != 0:
                output.flags[power] = True 
        
        return output

    def toBytes(self, outLength=-1):
        output = 0
        if outLength > 0:
            listLength = min(len(self.flags), outLength * 8)
        else:
            listLength = len(self.flags)

        for power in range(listLength):
            output += self.flags[power] * (2 ** power)
        
        outLength = max(listLength, outLength * 8)
        
        return output.to_bytes(ceil(outLength / 8), byteorder = 'little')

class EnableNewFlagState():
    def __init__(self, lenFlags):
        self.flagEnabled = FlagsAsArray(lenFlags)
        self.flagNew     = FlagsAsArray(lenFlags)
    
    @staticmethod
    def fromBytes(data, lenFlags, lenSlot):
        output = EnableNewFlagState(lenFlags)
        output.flagEnabled = FlagsAsArray.fromBytes(data[0:lenSlot], maxLength=lenFlags)
        output.flagNew     = FlagsAsArray.fromBytes(data[lenSlot:lenSlot + lenSlot], maxLength=lenFlags)
        return output
    
    def __str__(self):
        outStr = ""
        for index in range(self.flagEnabled.getLength()):
            outStr += "\n" + str(index) + "\t" + ["  ", "N "][self.flagNew.getSlot(index)] + ["Disabled", "Enabled"][self.flagEnabled.getSlot(index)]
        if len(outStr) > 0:
            return outStr[1:]
        return outStr

    def toBytes(self, outLength):
        output = bytearray(b'')
        output.extend(self.flagEnabled.toBytes(outLength=outLength))
        output.extend(self.flagNew.toBytes(outLength=outLength))
        return output

class HandlerTeaState():
    def __init__(self):
        self.flagElements   = FlagsAsArray(8)
        self.flagRecipes    = FlagsAsArray(12)
        self.flagCorrecct   = FlagsAsArray(24)
    
    def setElementsFromBytes(self, data):
        self.flagElements = FlagsAsArray.fromBytes(data, maxLength=8)
    
    def setRecipesFromBytes(self, data):
        self.flagRecipes = FlagsAsArray.fromBytes(data, maxLength=12)
    
    def setCorrectFromBytes(self, data):
        self.flagCorrecct = FlagsAsArray.fromBytes(data, maxLength=24)
    
    def getElementsBytes(self):
        return self.flagElements.toBytes(outLength=1)
    
    def getRecipesBytes(self):
        return self.flagRecipes.toBytes(outLength=2)
    
    def getCorrectBytes(self):
        return self.flagCorrecct.toBytes(outLength=3)

class HandlerMysteryState(EnableNewFlagState):
    def __init__(self):
        EnableNewFlagState.__init__(self, 10)
        self.flagSolved     = FlagsAsArray(10)

    #def enableMysteryState(self, slot, state):
    #    if self.isSlotValid(slot):
    #        if state:
    #            self.flagEnabled[slot]  = state
    #            self.flagNew[slot]      = False
    #            self.flagSolved[slot]   = False
    
    # TODO - More methods here

    @staticmethod
    def fromBytes(data):
        output              = HandlerMysteryState()
        output.flagEnabled  = FlagsAsArray.fromBytes(data[0:2], maxLength=10)
        output.flagNew      = FlagsAsArray.fromBytes(data[2:4], maxLength=10)
        output.flagSolved   = FlagsAsArray.fromBytes(data[4:6], maxLength=10)
        return output
    
    def toBytes(self):
        output = bytearray(b'')
        output.extend(self.flagEnabled.toBytes(outLength=2))
        output.extend(self.flagNew.toBytes(outLength=2))
        output.extend(self.flagSolved.toBytes(outLength=2))
        return output

class HandlerHamsterState():

    DEFAULT_NAME = "NO NAME"

    def __init__(self):
        self.grid = [[0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0],
                     [0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0], [0,0,0,0,0,0,0,0]]
        self.name = ""
        self.record = 0
        self.level = 5
        self.countItems = [0,0,0,0,0,0,0,0,0,0]
        self.isEnabled = False

    def setGridData(self, data):
        dataIndex = 0
        for y in range(6):
            for x in range(8):
                packedData = data[dataIndex // 2]
                if dataIndex % 2:
                    packedData = packedData >> 4
                self.grid[y][x] = packedData & 0x0f

                dataIndex += 1
                if dataIndex // 2 > len(data):
                    break
            if dataIndex // 2 > len(data):
                break

    def setName(self, name):
        self.name = name

    def setLevel(self, level):
        self.level = level
    
    def setLevelData(self, data):
        self.isEnabled = data > 0
        if self.isEnabled:
            self.level = 6 - data

    def setNameData(self, data):
        pass

    def setItemData(self, data):
        for indexItem in range(min(len(data), len(self.countItems))):
            self.countItems[indexItem] = data[indexItem]

    def setRecordData(self, data):
        self.record = data
    
    def getPackedGridBytes(self):
        if self.isEnabled:
            output = bytearray(b'')
            for y in range(len(self.grid)):
                for x in range(len(self.grid[y]) // 2):
                    lsbRoom = self.grid[y][x * 2]
                    msbRoom = self.grid[y][(x * 2) + 1] << 4
                    output.extend((lsbRoom + msbRoom).to_bytes(1, byteorder = 'little'))
            return output
        return b'\x00' * 24
    
    def getItemBytes(self):
        if self.isEnabled:
            output = bytearray(b'') 
            for count in self.countItems:
                output.extend(min(count, 255).to_bytes(1, byteorder = 'little'))
            return output
        return b'\x00' * 10
    
    def getRecordData(self):
        if self.isEnabled:
            return self.record
        return 0

    def getNameData(self):
        if self.isEnabled:
            return self.name
        return HandlerHamsterState.DEFAULT_NAME

    def getLevelBytes(self):
        output = 0
        if self.isEnabled:
            output = max(0, (6 - self.level))
        return output.to_bytes(1, byteorder = 'little')

class PhotoState():
    def __init__(self):
        self.flagCheck = FlagsAsArray(32)
        self.flagTake = FlagsAsArray(16)
        self.flagComplete = FlagsAsArray(16)
        self.countRemaining = 16
    
    def setFlagData(self, data):
        self.flagCheck = FlagsAsArray.fromBytes(data[0:4])
        self.flagTake = FlagsAsArray.fromBytes(data[4:6])
        self.flagComplete = FlagsAsArray.fromBytes(data[6:8])
    
    def setCountRemaining(self, count):
        self.countRemaining = max(0, min(16, count))
    
    def getFlagBytes(self):
        output = bytearray(b'')
        output.extend(self.flagCheck.toBytes(outLength=4))
        output.extend(self.flagTake.toBytes(outLength=2))
        output.extend(self.flagComplete.toBytes(outLength=2))
        return output
    
    def getCountRemainingData(self):
        return self.countRemaining

class CameraPiece():
    def __init__(self):
        self.deployed = False
        self.pos = (0,0)
        self.rot = 0
    
    def setFromPackedBytes(self, data):
        x = data[0] & 0x0f
        y = ((data[1] & 0x0f) << 2) + ((data[0] & 0xc0) >> 6)
        
        self.deployed = ((data[1] >> 6) & 0x01) != 0
        self.rot = ((data[1] & 0x30) >> 4)
        self.pos = (x, y)
    
    def getPackedBytes(self):
        x = self.pos[0] & 0x0f
        y = self.pos[1] & 0x0f

        if self.deployed:
            output = x
            output += y << 6
            output += self.rot << 12
            output += 1 << 14
        else:
            output = 0

        return output.to_bytes(2, byteorder = 'little')
    
    def __str__(self):
        return str(self.deployed) + "\t" + str(self.rot) + str(self.pos)

class HandlerCameraState():

    COUNT_CAMERA_PIECES = 10

    def __init__(self):
        self.cameraAvailableFlags   = FlagsAsArray(HandlerCameraState.COUNT_CAMERA_PIECES)
        self.cameraPieces           = []
        self.isEnabled              = True

        for _index in range(HandlerCameraState.COUNT_CAMERA_PIECES):
            self.cameraPieces.append(CameraPiece())
    
    def setCameraAvailableFlags(self, data):
        self.cameraAvailableFlags = FlagsAsArray.fromBytes(data, maxLength=10)
    
    def setCameraPiecesData(self, data):
        for index in range(HandlerCameraState.COUNT_CAMERA_PIECES):
            if index < len(data) // 2:
                self.cameraPieces[index].setFromPackedBytes(data[index * 2:(index * 2) + 2])
    
    def getCameraAvailableBytes(self):
        if self.isEnabled:
            return self.cameraAvailableFlags.toBytes(outLength=2)
        return b'\x00' * 2
    
    def getCameraPiecesBytes(self):
        if self.isEnabled:
            output = bytearray(b'')
            for piece in self.cameraPieces:
                output.extend(piece.getPackedBytes())
            return output
        return b'\x00' * 20

class PuzzleState():

    MAX_PUZZLE_COUNT = 216

    def __init__(self):
        self.puzzleBank = []
        for _puzzleIndex in range(PuzzleState.MAX_PUZZLE_COUNT):
            self.puzzleBank.append(PuzzleData())
    
    def getPuzzleData(self, internalIndex):
        if internalIndex >= 0 and internalIndex < PuzzleState.MAX_PUZZLE_COUNT:
            return self.puzzleBank[internalIndex]
        return None
    
    def setPuzzleBankFromBytes(self, data):
        for puzzleIndex, puzzleEncodedByte in enumerate(data):
            if puzzleIndex < PuzzleState.MAX_PUZZLE_COUNT:
                self.puzzleBank[puzzleIndex].setFromData(puzzleEncodedByte)
    
    def getPuzzleBankBytes(self):
        output = bytearray(b'')
        for puzzle in self.puzzleBank:
            output.extend(puzzle.toBytes())
        return output

class RoomHintState():

    MAX_ROOM_COUNT = 128

    def __init__(self):
        self.rooms = []
        for roomIndex in range(RoomHintState.MAX_ROOM_COUNT):
            self.rooms.append(HintCoinRoomData())
    
    def getRoomHintData(self, roomIndex):
        if roomIndex >= 0 and roomIndex < RoomHintState.MAX_ROOM_COUNT:
            return self.rooms[roomIndex]
        return None
    
    def setFromBytes(self, data):
        for index in range(min(len(data), RoomHintState.MAX_ROOM_COUNT // 2)):
            self.rooms[index * 2].setFromData(data[index] & 0x0f)
            self.rooms[(index * 2) + 1].setFromData((data[index] & 0xf0) >> 4)

    def getHintDataBytes(self):
        output = bytearray(b'')
        for index in range(RoomHintState.MAX_ROOM_COUNT // 2):
            lsbRoom = int.from_bytes(self.rooms[index * 2].toBytes(), byteorder = 'little')
            msbRoom = int.from_bytes(self.rooms[(index * 2) + 1].toBytes(), byteorder = 'little')
            packedData = lsbRoom + (msbRoom << 4)
            output.extend(packedData.to_bytes(1, byteorder = 'little'))
        return output

class Layton2SaveSlot():

    def __init__(self):
        self.isActive               = False
        self.isComplete             = False
        self.isTampered             = False
        self.name                   = "NO NAME"

        self.eventViewed            = FlagsAsArray(1024)
        self.storyFlag              = FlagsAsArray(128)

        self.headerPuzzleCountSolved        = 0
        self.headerPuzzleCountEncountered   = 0
        self.headerTimeElapsed              = 0
        self.headerRoomIndex                = 0

        self.puzzleData             = PuzzleState()
        self.roomHintData           = RoomHintState()
        self.hintCoinEncountered    = 10 # Regen these
        self.hintCoinAvailable      = 10
        self.picarots               = 0
        
        self.roomIndex              = 1
        self.roomSubIndex           = 1
        self.timeElapsed            = 0
        self.introEventIndex        = 0
        self.minigameTeaState       = HandlerTeaState()
        self.minigameHamsterState   = HandlerHamsterState()
        self.minigameCameraState    = HandlerCameraState()
        self.memoFlag               = EnableNewFlagState(60)    # Flags 0-59 in use, the rest not accessible (10 page limit)
        self.mysteryState           = HandlerMysteryState()
        self.photoState             = PhotoState()

        self.storyItemFlag          = FlagsAsArray(8)
        self.menuNewFlag            = FlagsAsArray(16)          # TODO - Read enabled state to disable any unwanted NEWs
        self.photoPieceFlag         = FlagsAsArray(16)
        self.tutorialFlag           = FlagsAsArray(16)

        self.anthonyDiaryState      = EnableNewFlagState(12)
        self.idImmediateEvent       = -1

        self.objective = 100
    
    def clear(self):
        self = Layton2SaveSlot()

    def fromBytes(self, data):
        reader = binary.BinaryReader(data = data)
        self.isTampered = self.isTampered or (reader.readUInt(4) != calculateSaveChecksumFromData(reader.read(796)))

        reader.seek(4)
        self.eventViewed = FlagsAsArray.fromBytes(reader.read(128))  # Something AutoEvent related, triggered whenever an AutoEvent plays
        self.storyFlag = FlagsAsArray.fromBytes(reader.read(16))

        reader.seek(24,1)

        self.photoState.setCountRemaining(reader.readUInt(1))

        reader.seek(103,1)

        self.puzzleData.setPuzzleBankFromBytes(reader.read(216))
        self.roomHintData.setFromBytes(reader.read(64))
        self.hintCoinAvailable      = reader.readU2()
        self.hintCoinEncountered    = reader.readU2()
        self.picarots               = reader.readU4()
        self.introEventIndex        = reader.readU4()
        self.roomIndex              = reader.readU4()
        self.roomSubIndex           = reader.readU4()

        reader.seek(4,1)
        
        self.timeElapsed            = reader.readU4()

        reader.seek(4,1)

        self.minigameCameraState.setCameraAvailableFlags(reader.read(2))    # CameraSolved
        self.minigameCameraState.setCameraPiecesData(reader.read(20))

        reader.seek(30,1)

        self.minigameTeaState.setElementsFromBytes(reader.read(1))
        self.minigameTeaState.setRecipesFromBytes(reader.read(2))
        self.minigameHamsterState.setLevelData(reader.readUInt(1))
        self.minigameHamsterState.setItemData(reader.read(10))
        self.minigameHamsterState.setGridData(reader.read(24))
        
        reader.seek(24,1)   # Unused?

        self.minigameHamsterState.setRecordData(reader.readUInt(1))

        reader.seek(4,1)

        self.memoFlag               = EnableNewFlagState.fromBytes(reader.read(32), 60, 16)
        self.mysteryState           = HandlerMysteryState.fromBytes(reader.read(6))
        self.photoState.setFlagData(reader.read(8))
        self.storyItemFlag          = FlagsAsArray.fromBytes(reader.read(1), maxLength=8)
        self.menuNewFlag            = FlagsAsArray.fromBytes(reader.read(2), maxLength=16)
        self.minigameTeaState.setCorrectFromBytes(reader.read(3))
        self.minigameHamsterState.setName(reader.readPaddedString(20, 'shift-jis'))

        self.photoPieceFlag         = FlagsAsArray.fromBytes(reader.read(2))
        self.tutorialFlag           = FlagsAsArray.fromBytes(reader.read(2))

        reader.seek(3,1)

        self.idImmediateEvent       = reader.readS2()
        self.anthonyDiaryState      = EnableNewFlagState.fromBytes(reader.read(4), 12, 2)

        reader.seek(4,1)

        self.objective              = reader.readU4()

        if self.roomIndex != self.headerRoomIndex:
            self.isTampered = True

        # 80 bytes remaining is padding to pad the save to 880 bytes
    
    def toBytes(self):
        writer = binary.BinaryWriter()
        if self.isActive:
            data = binary.BinaryWriter()

            data.write(self.eventViewed.toBytes(outLength=128))
            data.write(self.storyFlag.toBytes(outLength=16))

            data.pad(24, padChar=b'\x00')

            data.writeInt(self.photoState.getCountRemainingData(), 1)

            data.pad(103, padChar=b'\x00')
            
            # TODO - Validate this
            data.write(self.puzzleData.getPuzzleBankBytes())
            data.write(self.roomHintData.getHintDataBytes())
            data.writeU2(self.hintCoinAvailable)
            data.writeU2(self.hintCoinEncountered)
            data.writeU4(self.picarots)
            data.writeU4(self.introEventIndex)
            data.writeU4(self.roomIndex)
            data.writeU4(self.roomSubIndex)

            data.pad(4, padChar=b'\x00')

            data.writeU4(self.timeElapsed)
            
            data.pad(4, padChar = b'\x00')

            data.write(self.minigameCameraState.getCameraAvailableBytes())
            data.write(self.minigameCameraState.getCameraPiecesBytes())

            data.pad(30, padChar = b'\x00')

            data.write(self.minigameTeaState.getElementsBytes())
            data.write(self.minigameTeaState.getRecipesBytes())
            data.write(self.minigameHamsterState.getLevelBytes())
            data.write(self.minigameHamsterState.getItemBytes())
            data.write(self.minigameHamsterState.getPackedGridBytes())

            data.pad(24, padChar = b'\x00')

            data.writeInt(self.minigameHamsterState.getRecordData(), 1)

            data.pad(4, padChar = b'\x00')

            data.write(self.memoFlag.toBytes(16))
            data.write(self.mysteryState.toBytes())
            data.write(self.photoState.getFlagBytes())
            data.write(self.storyItemFlag.toBytes(outLength=1))
            data.write(self.menuNewFlag.toBytes(outLength=2))
            data.write(self.minigameTeaState.getCorrectBytes())
            data.writePaddedString(self.minigameHamsterState.getNameData(), 20, 'shift-jis')
            data.write(self.photoPieceFlag.toBytes(outLength=2))
            data.write(self.tutorialFlag.toBytes(outLength=2))

            data.pad(1, padChar = b'\x00')
            data.pad(2, padChar = b'\xff')

            data.writeInt(self.idImmediateEvent, 2, signed=True)
            data.write(self.anthonyDiaryState.toBytes(2))

            data.pad(4, padChar = b'\x00')

            data.writeInt(self.objective, 4)

            writer.writeU4(calculateSaveChecksumFromData(data.data))
            writer.write(data.data)
        else:
            writer.pad(800, padChar=b'\xff')

        writer.pad(80, padChar=b'\xff')
        return writer.data

    def getSolvedAndEncounteredPuzzleCount(self):
        solved      = 0
        encountered = 0
        for puzzleIndex in range(PuzzleState.MAX_PUZZLE_COUNT):
            puzzle = self.puzzleData.getPuzzleData(puzzleIndex)
            if puzzle.wasEncountered:
                if puzzle.wasSolved:
                    solved += 1
                encountered += 1
        
        return (solved, encountered)

    def getTrueHintCoinEncounteredValue(self):
        total = 10
        for roomIndex in range(RoomHintState.MAX_ROOM_COUNT):
            roomData = self.roomHintData.getRoomHintData(roomIndex)
            for hint in roomData.hintsFound:
                if hint:
                    total += 1
        return total

    def getTrueHintCoinRemainingValue(self):
        used = 0
        for puzzleIndex in range(PuzzleState.MAX_PUZZLE_COUNT):
            used += self.puzzleData.getPuzzleData(puzzleIndex).levelHint
        return max(0, self.getTrueHintCoinEncounteredValue() - used)

    def getTamperState(self):
        return self.isTampered

    def verify(self):
        pass

class Layton2SaveFile(File):

    SAVE_LENGTH = 8192

    def __init__(self):
        File.__init__(self)
        self._slots = [Layton2SaveSlot(),
                       Layton2SaveSlot(),
                       Layton2SaveSlot()]
    
    def getSlotData(self, slot):
        return self._slots[slot]

    def load(self, data):
        reader = binary.BinaryReader(data=data)
        if reader.readPaddedString(16, 'shift-jis') == "ATAMFIREBELLNY":
            isTampered = reader.readU4() != calculateSaveChecksumFromData(reader.read(196))
            reader.seek(20)

            activeSlots = reader.readUInt(1)
            reader.seek(3,1)    # Unused?
            for slotId in range(3):
                self.getSlotData(slotId).clear()
                self.getSlotData(slotId).isActive = (activeSlots & (2 ** slotId)) != 0
                if self.getSlotData(slotId).isActive:
                    self.getSlotData(slotId).isTampered = isTampered
                    self.getSlotData(slotId).name = reader.readPaddedString(20, 'shift-jis')
                    self.getSlotData(slotId).headerRoomIndex = reader.readUInt(1)
                    reader.seek(23,1)   # Bleed from string data, doesn't contain anything relevant
                    self.getSlotData(slotId).headerTimeElapsed = reader.readU4()
                    self.getSlotData(slotId).headerPuzzleCountSolved = reader.readU2()
                    self.getSlotData(slotId).headerPuzzleCountEncountered = reader.readU2()
                    self.getSlotData(slotId).isComplete = (reader.readUInt(1) == 1)
                    reader.seek(11,1)   # Unused?
                else:
                    reader.seek(64, 1)
            
            reader.seek(56,1)

            for slotId in range(3):
                if self.getSlotData(slotId).isActive:
                    self.getSlotData(slotId).fromBytes(reader.read(880))
                else:
                    reader.seek(880,1)

    def save(self):
        writer = binary.BinaryWriter()
        writer.writePaddedString("ATAMFIREBELLNY", 16, 'ascii')

        isSaveActive =  (self._slots[0].isActive +
                        (self._slots[1].isActive << 1) +
                        (self._slots[2].isActive << 2))

        if isSaveActive != 0:
            header = binary.BinaryWriter()
            header.writeInt(isSaveActive, 4)
            for saveSlot in self._slots:
                header.writePaddedString(saveSlot.name, 20, 'shift-jis')
                header.writeInt(saveSlot.roomIndex, 1)
                header.pad(23)  # Something triggers game to write string data to this instead
                header.writeInt(saveSlot.timeElapsed, 4)
                solved, encountered = saveSlot.getSolvedAndEncounteredPuzzleCount()
                header.writeInt(solved, 2)
                header.writeInt(encountered, 2)
                header.writeInt(saveSlot.isComplete, 1)
                header.pad(11)
            
            writer.writeInt(calculateSaveChecksumFromData(header.data), 4)
            writer.write(header.data)
            writer.pad(56, padChar=b'\xff')

            for saveSlot in self._slots:
                writer.write(saveSlot.toBytes())
        else:
            writer.pad(4, padChar=b'\xff')
            writer.pad(196, padChar=b'\x00')
        
        writer.pad(Layton2SaveFile.SAVE_LENGTH - writer.tell(), padChar=b'\xff')
        self.data = writer.data