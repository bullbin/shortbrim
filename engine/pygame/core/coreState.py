# State Components of LAYTON1

import coreProp, gdsLib

class LaytonPuzzleDataEntry():
    def __init__(self, decayValues):
        self.name = ""
        self.unlocked = True
        self.unlockedHintLevel = 0
        self.category = None
        self.decayState = 0
        self.decayValues = decayValues
    def getValue(self):
        if self.decayState > len(self.decayValues) - 1:
            return self.decayValues[-1]
        return self.decayValues[self.decayState]

class LaytonPlayerState():
    def __init__(self):
        self.name = "LT1_ENGINE"
        self.puzzleData = {}
        self.currentRoom = 0
        self.remainingHintCoins = 0

    def puzzleLoadNames(self):
        if len(self.puzzleData.keys()) == 0:
            self.loadPuzzleData()
        qscript = gdsLib.gdScript(coreProp.LAYTON_ASSET_ROOT + "script\\qinfo\\" + coreProp.LAYTON_ASSET_LANG + "\\qscript.gds")
        for instruction in qscript.commands:
            if instruction.opcode == b'\xdc':
                try:
                    self.puzzleData[instruction.operands[0]].name = instruction.operands[2]
                    self.puzzleData[instruction.operands[0]].category = instruction.operands[1]
                except KeyError:
                    self.puzzleData[instruction.operands[0]] = LaytonPuzzleDataEntry([])
                    self.puzzleData[instruction.operands[0]].name = instruction.operands[2]
                    self.puzzleData[instruction.operands[0]].category = instruction.operands[1]

    def puzzleLoadData(self):
        pscript = gdsLib.gdScript(coreProp.LAYTON_ASSET_ROOT + "script\\pcarot\\pscript.gds")
        for instruction in pscript.commands:
            if instruction.opcode == b'\xc3':
                # Set picarot decay
                self.puzzleData[instruction.operands[0]] = LaytonPuzzleDataEntry(instruction.operands[1:])

class LaytonContext():
    def __init__(self):
        self.screen = None
        self.isContextFinished = False
    def getContextState(self):
        return self.isContextFinished

class LaytonContextStack():
    # Stack used to hold Layton contexts, eg puzzle frames or faders
    def __init__(self):
        self.stack = []
    def getCurrentItem(self):
        return self.stack[-1]
