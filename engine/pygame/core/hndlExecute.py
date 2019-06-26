# PyGame Implementation of Professor Layton Puzzle Game

import gdsLib, pygame, coreProp, coreAnim, nazoGeneric, nazoDrawInput2, nazoSlidePuzzle, nazoMatch
from os import path

def getHintText():
    pass

def loadPuzzleNames():
    if len(coreProp.LAYTON_PUZZLE_DATA) == 0:
        loadPuzzleData()
    qscript = gdsLib.gdScript(coreProp.LAYTON_ASSET_ROOT + "script\\qinfo\\" + coreProp.LAYTON_ASSET_LANG + "\\qscript.gds")
    for instruction in qscript.commands:
        if instruction.opcode == b'\xdc':
            # Set puzzle titles and formal categories
            try:
                coreProp.LAYTON_PUZZLE_DATA[instruction.operands[0]].name = instruction.operands[2]
                coreProp.LAYTON_PUZZLE_DATA[instruction.operands[0]].category = instruction.operands[1]
            except KeyError:
                coreProp.LAYTON_PUZZLE_DATA[instruction.operands[0]] = LaytonPuzzleDataEntry([])
                coreProp.LAYTON_PUZZLE_DATA[instruction.operands[0]].name = instruction.operands[2]
                coreProp.LAYTON_PUZZLE_DATA[instruction.operands[0]].category = instruction.operands[1]

def loadPuzzleData():
    pscript = gdsLib.gdScript(coreProp.LAYTON_ASSET_ROOT + "script\\pcarot\\pscript.gds")
    for instruction in pscript.commands:
        if instruction.opcode == b'\xc3':
            # Set picarot decay
            coreProp.LAYTON_PUZZLE_DATA[instruction.operands[0]] = LaytonPuzzleDataEntry(instruction.operands[1:])

class LaytonPuzzleDataEntry():
    def __init__(self, decayValues):
        self.name = ""
        self.category = None
        self.decayState = 0
        self.decayValues = decayValues
    def getValue(self):
        if self.decayState > len(self.decayValues) - 1:
            return self.decayValues[-1]
        return self.decayValues[self.decayState]

class LaytonPuzzlePlayer():
    # This is only used to run the puzzle handler, each handler contains its own display code

    puzzleSpawner = {"Draw Input2":nazoDrawInput2.LaytonPuzzleHandler, "Slide Puzzle":nazoSlidePuzzle.LaytonPuzzleHandler, "Match":nazoMatch.LaytonPuzzleHandler}
    
    def __init__(self, puzzleIndex):
        self.puzzleIndex = puzzleIndex
        self.puzzleScript = gdsLib.gdScript(coreProp.LAYTON_ASSET_ROOT + "script\\qscript\\q" + str(self.puzzleIndex) + "_param.gds")
        self.gameDisplay = pygame.display.set_mode((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT * 2))
        self.gameClock = pygame.time.Clock()

        for command in self.puzzleScript.commands:
            if command.opcode == b'\x1b':
                if command.operands[0] in LaytonPuzzlePlayer.puzzleSpawner.keys():
                    print(command.operands[0])
                    self.puzzleHandler = LaytonPuzzlePlayer.puzzleSpawner[command.operands[0]](self.puzzleIndex, self.puzzleScript)
                else:
                    self.puzzleHandler = nazoGeneric.LaytonPuzzleHandler(self.puzzleIndex, self.puzzleScript)
                    print("No handler defined: " + command.operands[0])
                break
        
        pygame.display.set_caption("Curious Village")
        
    def play(self):
        isActive = True
        while isActive:

            self.puzzleHandler.update()
            self.puzzleHandler.draw(self.gameDisplay)
            pygame.display.update()

            for event in pygame.event.get():
                
                if event.type == pygame.QUIT:
                    isActive = False
                else:
                    self.puzzleHandler.handleEvent(event)
                    
            self.gameClock.tick(coreProp.LAYTON_ENGINE_FPS)

loadPuzzleData()
loadPuzzleNames()
puzzleInstance = LaytonPuzzlePlayer(25)
puzzleInstance.play()
