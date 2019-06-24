# PyGame Implementation of Professor Layton Puzzle Game

import gdsLib, pygame
from os import path

pygame.init()

# CONSTANTS
LAYTON_ASSET_ROOT   = path.dirname(path.dirname(path.dirname(path.realpath(__file__)))) + r"\assets\\"
LAYTON_ASSET_LANG   = "en"
LAYTON_PUZZLE_FONT  = pygame.font.SysFont('freesansbold', 17)

class AnimatedImage():
    def __init__(self, imagePath, x=0,y=0):
        self.image = pygame.image.load(LAYTON_ASSET_ROOT + imagePath)
        self.pos = (x,y)
    def draw(self, gameDisplay):
        gameDisplay.blit(self.image, self.pos)

class AnimatedText():
    def __init__(self, initString = ""):
        self.text = initString
        self.textRender = LAYTON_PUZZLE_FONT.render(self.text,True,(0,0,0),None)
    def update(self):
        self.textRender = LAYTON_PUZZLE_FONT.render(self.text,True,(0,0,0),None)

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
            textRect = animText.textRender.get_rect()
            centX, centY = textRect.center
            centY += y; centX += x
            textRect.center = (centX, centY)
            gameDisplay.blit(animText.textRender, textRect)
            y += LAYTON_PUZZLE_FONT.get_height()

class LaytonPuzzleHandler():

    backgroundTs = pygame.image.load(LAYTON_ASSET_ROOT + "bg\\" + LAYTON_ASSET_LANG + r"\q_bg.png")
    
    def __init__(self, puzzleIndex):
        self.puzzleIndex = puzzleIndex
        self.backgroundBs = pygame.image.load(LAYTON_ASSET_ROOT + "bg\\" + LAYTON_ASSET_LANG + r"\q_bg.png")
        if puzzleIndex < 100:
            puzzlePath = LAYTON_ASSET_ROOT + "qtext\\" + LAYTON_ASSET_LANG + "\\q000\\"
        elif puzzleIndex < 200:
            puzzlePath = LAYTON_ASSET_ROOT + "qtext\\" + LAYTON_ASSET_LANG + "\\q100\\"
        else:
            puzzlePath = LAYTON_ASSET_ROOT + "qtext\\" + LAYTON_ASSET_LANG + "\\q200\\"
            
        # Load the puzzle qText
        with open(puzzlePath + "q_" + str(self.puzzleIndex) + ".txt", 'r') as qText:
            self.puzzleQText = TextScroller(qText.read())

    def update(self):
        self.puzzleQText.update()

    def draw(self, gameDisplay):
        gameDisplay.blit(LaytonPuzzleHandler.backgroundTs, (0,0))
        self.puzzleQText.draw(gameDisplay)

class LaytonPuzzlePlayer():
    def __init__(self, puzzleIndex):
        self.puzzleIndex = puzzleIndex
        self.gameDisplay = pygame.display.set_mode((256, 384))
        pygame.display.set_caption("Curious Future")
        self.clock = pygame.time.Clock()
        self.currentFrameStep = 0
    
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
                    
            self.clock.tick(60)
                    
puzzleInstance = LaytonPuzzlePlayer(25)
puzzleInstance.play()
