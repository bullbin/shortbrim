# PyGame Implementation of Professor Layton Puzzle Game

import gdsLib, pygame
from os import path

pygame.init()

# CONSTANTS
LAYTON_ENGINE_FPS           = 30        # Game speed is tied to framerate
LAYTON_ASSET_ROOT           = path.dirname(path.dirname(path.dirname(path.realpath(__file__)))) + r"\assets\\"
LAYTON_ASSET_LANG           = "en"
LAYTON_PUZZLE_FONT          = pygame.font.SysFont('freesansbold', 17)
LAYTON_PUZZLE_DATA          = {}

def getHintText():
    pass

def loadPuzzleNames():
    if len(LAYTON_PUZZLE_DATA) == 0:
        loadPuzzleData()
    qscript = gdsLib.gdScript(LAYTON_ASSET_ROOT + "script\\qinfo\\" + LAYTON_ASSET_LANG + "\\qscript.gds")
    for instruction in qscript.commands:
        if instruction.opcode == b'\xdc':
            # Set puzzle titles and formal categories
            try:
                LAYTON_PUZZLE_DATA[instruction.operands[0]].name = instruction.operands[2]
                LAYTON_PUZZLE_DATA[instruction.operands[0]].category = instruction.operands[1]
            except KeyError:
                LAYTON_PUZZLE_DATA[instruction.operands[0]] = LaytonPuzzleDataEntry([])
                LAYTON_PUZZLE_DATA[instruction.operands[0]].name = instruction.operands[2]
                LAYTON_PUZZLE_DATA[instruction.operands[0]].category = instruction.operands[1]

def loadPuzzleData():
    pscript = gdsLib.gdScript(LAYTON_ASSET_ROOT + "script\\pcarot\\pscript.gds")
    for instruction in pscript.commands:
        if instruction.opcode == b'\xc3':
            # Set picarot decay
            LAYTON_PUZZLE_DATA[instruction.operands[0]] = LaytonPuzzleDataEntry(instruction.operands[1:])

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

class AnimatedImage():
    def __init__(self, imagePath, x=0,y=0):
        self.image = pygame.image.load(LAYTON_ASSET_ROOT + imagePath)
        self.pos = (x,y)
    def draw(self, gameDisplay):
        gameDisplay.blit(self.image, self.pos)

class AnimatedText():
    def __init__(self, initString = "", colour=(0,0,0)):
        self.text = initString
        self.textColour = colour
        self.textRender = LAYTON_PUZZLE_FONT.render(self.text,True,colour,None)
    def update(self):
        self.textRender = LAYTON_PUZZLE_FONT.render(self.text,True,self.textColour,None)
    def draw(self, gameDisplay, location=(0,0)):
        textRect = self.textRender.get_rect()
        centX, centY = textRect.center
        x,y = location
        centY += y; centX += x
        textRect.center = (centX, centY)
        gameDisplay.blit(self.textRender, textRect)

class TextScroller():
    def __init__(self, textInput, textPosOffset=(4,24)):
         self.textInput = textInput
         self.textNewline = 0
         self.textPos = 0
         self.textPosOffset = textPosOffset
         self.textRects = []
         self.drawIncomplete = True

    def update(self):
        if self.drawIncomplete:
            if self.textInput[self.textPos] == "\n" or self.textPos == 0:
                self.textRects.append(AnimatedText())
                if self.textPos == 0:
                    self.textNewline = self.textPos
                else:
                    self.textNewline = self.textPos + 1
            else:
                self.textRects[-1].text = self.textInput[self.textNewline:self.textPos + 1]
                
            if self.textPos < len(self.textInput) -1:
                self.textPos += 1
            else:
                self.drawIncomplete = False

    def skip(self):
        if self.drawIncomplete:
            skipText = self.textInput.split("\n")
            self.textRects = []
            for line in skipText:
                self.textRects.append(AnimatedText(initString = line))
            self.drawIncomplete = False
    
    def draw(self, gameDisplay):
        x, y = self.textPosOffset
        for animText in self.textRects:
            animText.update()
            animText.draw(gameDisplay, location=(x,y))
            y += LAYTON_PUZZLE_FONT.get_height()

class LaytonPuzzleHandler():

    backgroundTs = pygame.image.load(LAYTON_ASSET_ROOT + "bg\\" + LAYTON_ASSET_LANG + r"\q_bg.png")
    buttonSkip = None
    
    def __init__(self, puzzleIndex, puzzleScript, puzzleEnable = True):
        
        try:
            with open(LAYTON_ASSET_ROOT + "bg\\q" + str(puzzleIndex) + "_bg.png", 'rb') as imgTest:
                pass
            self.backgroundBs = pygame.image.load(LAYTON_ASSET_ROOT + "bg\\q" + str(puzzleIndex) + "_bg.png")
        except FileNotFoundError:
            self.backgroundBs = LaytonPuzzleHandler.backgroundTs
            for command in puzzleScript.commands:
                if command.opcode == b'\x0b':
                    # Replace the background with script's stored alternative
                    print("Replace background: " + command.operands[0])
                    break
                
        self.puzzleEnable           = puzzleEnable
        self.puzzleScript           = puzzleScript
        self.puzzleIndex            = puzzleIndex
        self.puzzleInputWaiting     = True
        self.puzzleQText            = TextScroller("")
        self.puzzleIndexText        = AnimatedText(initString=str(self.puzzleIndex))
        self.puzzlePicarotsText     = AnimatedText(initString=str(LAYTON_PUZZLE_DATA[self.puzzleIndex].getValue()))
        
        self.load()
        
    def load(self):
        # Load a fresh puzzle state, useful when restarting the puzzle
        if self.puzzleIndex < 50:
            puzzlePath = LAYTON_ASSET_ROOT + "qtext\\" + LAYTON_ASSET_LANG + "\\q000\\"
        elif self.puzzleIndex < 100:
            puzzlePath = LAYTON_ASSET_ROOT + "qtext\\" + LAYTON_ASSET_LANG + "\\q050\\"
        else:
            puzzlePath = LAYTON_ASSET_ROOT + "qtext\\" + LAYTON_ASSET_LANG + "\\q100\\"
            
        # Load the puzzle qText
        with open(puzzlePath + "q_" + str(self.puzzleIndex) + ".txt", 'r') as qText:
            self.puzzleQText = TextScroller(qText.read())
            
        self.puzzleInputWaiting = True
        self.puzzlePicarotsText = AnimatedText(initString=str(LAYTON_PUZZLE_DATA[self.puzzleIndex].getValue()))
        
    def update(self):
        if self.puzzleEnable:
            self.puzzleQText.update()

    def skip(self):
        # Play the skip sound as well
        if self.puzzleEnable:
            self.puzzleQText.skip()
    
    def draw(self, gameDisplay):
        gameDisplay.blit(LaytonPuzzleHandler.backgroundTs, (0,0))
        gameDisplay.blit(self.backgroundBs, (0,192))
        self.puzzleIndexText.draw(gameDisplay, location=(30, 6))
        self.puzzlePicarotsText.draw(gameDisplay, location=(232,6))
        self.puzzleQText.draw(gameDisplay)
        if self.puzzleInputWaiting:
            # Draw the 'touch' waitscreen
            pass

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.puzzleEnable:
            self.skip()
            self.puzzleInputWaiting = False

    def drawFade(self):
        pass

    def hideFade(self):
        pass

class LaytonPuzzleDrawInput(LaytonPuzzleHandler):

    buttonEntry = None
    buttonClear = pygame.image.load(LAYTON_ASSET_ROOT + "ani\\nazo\\drawinput\\" + LAYTON_ASSET_LANG + r"\clear.png")
    buttonBack = pygame.image.load(LAYTON_ASSET_ROOT + "ani\\nazo\\drawinput\\" + LAYTON_ASSET_LANG + r"\back.png")
    buttonErase = pygame.image.load(LAYTON_ASSET_ROOT + "ani\\nazo\\drawinput\\" + LAYTON_ASSET_LANG + r"\erase.png")
    
    def __init__(self, puzzleIndex, puzzleScript, puzzleEnable = True):
        LaytonPuzzleHandler.__init__(self, puzzleIndex, puzzleScript, puzzleEnable)

        self.drawTransitioning = False
        self.modeEntry = False
        self.modeQuestion = True
        self.regions = []

    def load(self):
        super().load()

    def update(self):
        super().update()

    def skip(self):
        super().skip()

    def draw(self, gameDisplay):
        super().draw(gameDisplay)

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.puzzleEnable:
            self.skip()
            self.puzzleInputWaiting = False

class LaytonPuzzleSlidePuzzle(LaytonPuzzleHandler):
    
    def __init__(self, puzzleIndex, puzzleScript, puzzleEnable = True):
        LaytonPuzzleHandler.__init__(self, puzzleIndex, puzzleScript, puzzleEnable)

    def load(self):
        super().load()

    def update(self):
        super().update()

    def skip(self):
        super().skip()

    def draw(self, gameDisplay):
        super().draw(gameDisplay)

    def handleEvent(self, event):
        super().handleEvent(event)

class LaytonPuzzlePlayer():
    # This is only used to run the puzzle handler, each handler contains its own display code
    def __init__(self, puzzleIndex):
        self.puzzleIndex = puzzleIndex
        self.puzzleScript = gdsLib.gdScript(LAYTON_ASSET_ROOT + "script\\qscript\\q" + str(self.puzzleIndex) + "_param.gds")
        self.gameDisplay = pygame.display.set_mode((256, 384))
        self.gameClock = pygame.time.Clock()

        for command in self.puzzleScript.commands:
            if command.opcode == b'\x1b':
                if (command.operands[0]) == "Draw Input2":
                    print("Spawn DrawInput2")
                    self.puzzleHandler = LaytonPuzzleDrawInput(self.puzzleIndex, self.puzzleScript)
                elif (command.operands[0]) == "Slide Puzzle":
                    print("Spawn SlidePuzzle")
                    self.puzzleHandler = LaytonPuzzleSlidePuzzle(self.puzzleIndex, self.puzzleScript)
                else:
                    self.puzzleHandler = LaytonPuzzleHandler(self.puzzleIndex, self.puzzleScript)
                    print(command.operands[0])
                    print("Puzzle handler unknown!")
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
                    
            self.gameClock.tick(LAYTON_ENGINE_FPS)

loadPuzzleData()
loadPuzzleNames()
puzzleInstance = LaytonPuzzlePlayer(80)
puzzleInstance.play()
