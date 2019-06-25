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

def loadPuzzleNames():
    if len(LAYTON_PUZZLE_DATA) == 0:
        loadPuzzleData()
    qscript = gdsLib.gdScript(LAYTON_ASSET_ROOT + "script\\qinfo\\" + LAYTON_ASSET_LANG + "\\qscript.gds")
    for instruction in qscript.commands:
        if instruction.opcode == b'\xdc':
            # Set puzzle titles and handlers (not required as puzzle scripts contain handler)
            try:
                LAYTON_PUZZLE_DATA[instruction.operands[0]].name = instruction.operands[2]
                LAYTON_PUZZLE_DATA[instruction.operands[0]].handler = instruction.operands[1]
            except KeyError:
                LAYTON_PUZZLE_DATA[instruction.operands[0]] = LaytonPuzzleDataEntry([])
                LAYTON_PUZZLE_DATA[instruction.operands[0]].name = instruction.operands[2]
                LAYTON_PUZZLE_DATA[instruction.operands[0]].handler = instruction.operands[1]

def loadPuzzleData():
    pscript = gdsLib.gdScript(LAYTON_ASSET_ROOT + "script\\pcarot\\pscript.gds")
    for instruction in pscript.commands:
        if instruction.opcode == b'\xc3':
            # Set picarot decay
            LAYTON_PUZZLE_DATA[instruction.operands[0]] = LaytonPuzzleDataEntry(instruction.operands[1:])

class LaytonPuzzleDataEntry():
    def __init__(self, decayValues):
        self.name = ""
        self.handler = None
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
    
    def __init__(self, puzzleIndex, puzzleEnable = True):
        
        self.backgroundBs = pygame.image.load(LAYTON_ASSET_ROOT + "bg\\q" + str(puzzleIndex) + "_bg.png")
        
        self.puzzleEnable           = puzzleEnable
        self.puzzleIndex            = puzzleIndex
        self.puzzleInputWaiting     = True
        self.puzzleQText            = TextScroller("")
        self.puzzleIndexText        = AnimatedText(initString=str(self.puzzleIndex))
        self.puzzlePicarotsText     = AnimatedText(initString=str(LAYTON_PUZZLE_DATA[self.puzzleIndex].getValue()))
        
        self.load()
        
    def load(self):
        # Load a fresh puzzle state, useful when restarting the puzzle
        if self.puzzleIndex < 100:
            puzzlePath = LAYTON_ASSET_ROOT + "qtext\\" + LAYTON_ASSET_LANG + "\\q000\\"
        elif self.puzzleIndex < 200:
            puzzlePath = LAYTON_ASSET_ROOT + "qtext\\" + LAYTON_ASSET_LANG + "\\q100\\"
        else:
            puzzlePath = LAYTON_ASSET_ROOT + "qtext\\" + LAYTON_ASSET_LANG + "\\q200\\"
            
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

class LaytonPuzzlePlayer():
    # This is only used to run the puzzle handler, each handler contains its own display code
    def __init__(self, puzzleIndex):
        self.puzzleIndex = puzzleIndex
        self.gameDisplay = pygame.display.set_mode((256, 384))
        pygame.display.set_caption("Curious Future")
        self.clock = pygame.time.Clock()
        
    def play(self):
        isActive = True
        testHandler = LaytonPuzzleHandler(self.puzzleIndex)
        
        while isActive:

            testHandler.update()
            testHandler.draw(self.gameDisplay)
            pygame.display.update()
            
            for event in pygame.event.get():
                
                if event.type == pygame.QUIT:
                    isActive = False
                else:
                    testHandler.handleEvent(event)
                    
            self.clock.tick(LAYTON_ENGINE_FPS)

loadPuzzleData()
loadPuzzleNames()
puzzleInstance = LaytonPuzzlePlayer(25)
puzzleInstance.play()
