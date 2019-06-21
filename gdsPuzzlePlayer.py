# PyGame Implementation of Professor Layton Puzzle Game

import gdsLib, pygame

pygame.init()
pathLaytonAssetRoot = r"C:\Users\USERNAME\Documents\GitHub\layton1\assets\\"

class AnimatedImage():
    def __init__(self, imagePath, x=0,y=0):
        self.image = pygame.image.load(pathLaytonAssetRoot + imagePath)
        self.pos = (x,y)
    def draw(self, gameDisplay):
        gameDisplay.blit(self.image, self.pos)

class Fader():
    def __init__(self, colour):
        self.drawIncomplete = True
    def update(self):
        if self.drawIncomplete:
            pass

class TextScroller():
    def __init__(self, textInput):
        self.textInput = textInput
        self.lastNewline = 0
        self.textPos = 1
        self.drawIncomplete = True
        self.font = pygame.font.Font('freesansbold.ttf', 12)
        self.text = [self.font.render(self.textInput[0:self.textPos], True, (0,255,0), (0,0,255))]

    def draw(self, gameDisplay):
        if self.drawIncomplete:
            if self.textPos <= len(self.textInput):
                self.textPos += 1
            if self.textInput[self.textPos - 2] == "\n":
                self.text[-1] = self.font.render(self.textInput[self.lastNewline:self.textPos - 2], True, (0,255,0), (0,0,255))
                print(self.textInput[self.lastNewline:self.textPos - 1])
                self.text.append(self.font.render(self.textInput[self.lastNewline + 1:self.textPos], True, (0,255,0), (0,0,255)))
                self.lastNewline = self.textPos - 1
            else:
                self.text[-1] = self.font.render(self.textInput[self.lastNewline:self.textPos], True, (0,255,0), (0,0,255))

        y = 0
        for text in self.text:
            textRect = text.get_rect()
            centX, centY = textRect.center
            centY += y
            textRect.center = (centX, centY)
            gameDisplay.blit(text, textRect)
            y += 12

class LaytonPuzzle():
    def __init__(self, puzzleIndex):
        self.puzzleIndex = puzzleIndex
        self.backgroundTs = pygame.image.load(pathLaytonAssetRoot + "bg\en\q_bg.png")
        self.backgroundBs = pygame.image.load(pathLaytonAssetRoot + "bg\q" + str(self.puzzleIndex) + "_bg.png")
        with open(pathLaytonAssetRoot + r"qtext\en\q000\q_" + str(self.puzzleIndex) + ".txt", 'r') as qText:
            self.backgroundText = TextScroller(qText.read())

        self.textDrawIncomplete = True

    def draw(self, gameDisplay):
        self.backgroundText.draw(gameDisplay)
        #gameDisplay.blit(self.backgroundTs, (0,0))
        #gameDisplay.blit(self.backgroundBs, (0,192))

class PuzzleSliding(LaytonPuzzle):
    def __init__(self, puzzleIndex):
        LaytonPuzzle.__init__(self, puzzleIndex)

class PuzzleTrace(LaytonPuzzle):
    def __init__(self, puzzleIndex):
        LaytonPuzzle.__init__(self, puzzleIndex)

class PuzzleDrawInput2(LaytonPuzzle):
    def __init__(self, puzzleIndex):
        LaytonPuzzle.__init__(self, puzzleIndex)

class LaytonPuzzlePlayer():
    def __init__(self, puzzleIndex):
        self.gameDisplay = pygame.display.set_mode((256, 384))
        pygame.display.set_caption("LAYTON")
        self.script = gdsLib.gdScript(pathLaytonAssetRoot + r"\script\qscript\q" + str(puzzleIndex) + "_param.gds")
        
        self.puzzle = None
        for command in self.script.commands:
            if command.opcode == b'\x1b':
                if command.operands[0] in ["Draw Input2", "Match"]:
                    self.puzzle = PuzzleDrawInput2(puzzleIndex)
                else:
                    print(command.operands[0])
        
        self.clock = pygame.time.Clock()
        self.currentFrameStep = 0

    def loadIntroSequence(self):
        self.backgroundTs = AnimatedImage(r"\bg\en\judge_l114_bg.png")
        self.backgroundBs = AnimatedImage(r"\bg\en\picarat_bg.png")
        self.backgroundTs.pos = (0, 192)
        self.backgroundBs.pos = (0, 192)

    def update(self, drawIntro, drawIntroComplete):
        
        if self.puzzle != None:
            if drawIntro:
                resX, resY = self.backgroundTs.pos
                if resY > 0:
                    resY -= 12
                    self.backgroundTs.pos = (resX, resY)
                else:
                    drawIntroComplete = True
                    
                self.backgroundBs.draw(self.gameDisplay)
                self.backgroundTs.draw(self.gameDisplay)

                if drawIntroComplete:
                    drawIntro = False

            else:
                self.puzzle.draw(self.gameDisplay)
            pygame.display.update()
    
    def play(self):
        isActive = True
        
        drawIntro = False
        drawIntroComplete = False
        
        if drawIntro:
            self.loadIntroSequence()
        
        while isActive:
            
            self.update(drawIntro, drawIntroComplete)
            
            for event in pygame.event.get():
                
                if event.type == pygame.QUIT:
                    isActive = False
                    
            self.clock.tick(60)
                    
puzzleInstance = LaytonPuzzlePlayer(25)
puzzleInstance.play()
