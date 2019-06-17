# PyGame Implementation of Professor Layton Puzzle Game

import gdsLib, pygame

pygame.init()
pathLaytonAssetRoot = r"C:\Users\USERNAME\Documents\GitHub\curious_village\assets\\"

class TextScroller():
    def __init__(self, textInput):
        self.textInput = textInput
        self.textPos = 1
        self.drawIncomplete = True
    def update(self):
        if self.drawIncomplete:
            if self.textPos <= len(self.textInput):
                self.textPos += 1
        return self.textInput[0:self.textPos]

class LaytonPuzzle():
    def __init__(self, puzzleIndex):
        self.puzzleIndex = puzzleIndex
        self.background = pygame.image.load(pathLaytonAssetRoot + "bg\en\q_bg.png")
        with open(pathLaytonAssetRoot + r"qtext\en\q000\q_" + str(self.puzzleIndex) + ".txt", 'r') as qText:
            self.backgroundText = TextScroller(qText.read())

        print(self.backgroundText.textInput)
        self.textDrawIncomplete = True

    def draw(self, gameDisplay):
        if self.backgroundText.drawIncomplete:
            print(self.backgroundText.update())
            pass
        gameDisplay.blit(self.background, (0,0))

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
                if command.operands[0] in ["Draw Input2"]:
                    self.puzzle = PuzzleDrawInput2(puzzleIndex)
                else:
                    print(command.operands[0])
        
        self.clock = pygame.time.Clock()
        
    def play(self):
        isActive = True
        while isActive:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    isActive = False

                if self.puzzle != None:
                    self.puzzle.draw(self.gameDisplay)
                    pygame.display.update()
                    self.clock.tick(60)
                else:
                    pygame.display.quit()
                    pygame.quit()
                    isActive = False
                    
puzzleInstance = LaytonPuzzlePlayer(6)
puzzleInstance.play()
