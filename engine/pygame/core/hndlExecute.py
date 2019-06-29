# PyGame Implementation of Professor Layton Puzzle Game

import gdsLib, pygame, coreProp, coreState, coreAnim, nazoGeneric, nazoDrawInput2, nazoSlidePuzzle, nazoMatch, nazoFreeButton
from os import path

def getHintText():
    pass

class LaytonPuzzlePlayer():
    # This is only used to run the puzzle handler, each handler contains its own display code

    puzzleSpawner = {"Draw Input2":nazoDrawInput2.LaytonPuzzleHandler, "Slide Puzzle":nazoSlidePuzzle.LaytonPuzzleHandler, "Match":nazoMatch.LaytonPuzzleHandler,
                     "Free Button":nazoFreeButton.LaytonPuzzleHandler}
    
    def __init__(self, puzzleIndex):

        self.playerState = coreState.LaytonPlayerState()
        self.playerState.puzzleLoadData()
        self.playerState.puzzleLoadNames()
        self.playerState.remainingHintCoins = 50
        
        self.puzzleIndex = puzzleIndex
        self.puzzleScript = gdsLib.gdScript(coreProp.LAYTON_ASSET_ROOT + "script\\qscript\\q" + str(self.puzzleIndex) + "_param.gds")
        self.gameDisplay = pygame.display.set_mode((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT * 2))
        self.gameClock = pygame.time.Clock()

        for command in self.puzzleScript.commands:
            if command.opcode == b'\x1b':
                if command.operands[0] in LaytonPuzzlePlayer.puzzleSpawner.keys():
                    print(command.operands[0])
                    self.puzzleHandler = LaytonPuzzlePlayer.puzzleSpawner[command.operands[0]](self.playerState, self.puzzleIndex, self.puzzleScript)
                else:
                    self.puzzleHandler = nazoGeneric.LaytonPuzzleHandler(self.playerState, self.puzzleIndex, self.puzzleScript)
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

puzzleInstance = LaytonPuzzlePlayer(100)
puzzleInstance.play()
print(puzzleInstance.playerState.remainingHintCoins)
