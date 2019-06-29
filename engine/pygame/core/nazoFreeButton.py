import coreProp, coreAnim, pygame, nazoGeneric

class LaytonPuzzleHandler(nazoGeneric.LaytonPuzzleHandler):
    
    def __init__(self, playerState, puzzleIndex, puzzleScript, puzzleEnable = True):

        self.interactableElements = []
        self.drawFlagsInteractableElements = []
        self.solutionElements = []
        
        nazoGeneric.LaytonPuzzleHandler.__init__(self, playerState, puzzleIndex, puzzleScript, puzzleEnable)

        self.playerState.remainingHintCoins = 0

    def executeGdScript(self):
        for command in self.puzzleScript.commands:
            if command.opcode == b'\x5d':
                imageName = command.operands[2]
                if imageName[-4:] == ".spr":
                    imageName = imageName[0:-4] + ".png"

                if command.operands[3] == 1:
                    self.solutionElements.append(len(self.interactableElements))
                
                self.interactableElements.append(coreAnim.AnimatedImage("ani\\" + imageName,
                                                 x=command.operands[0],
                                                 y=command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT))
                self.drawFlagsInteractableElements.append(False)
                self.interactableElements[-1].setAnimation(command.operands[4])
                
            
    def load(self):
        super().load()

    def update(self):
        super().update()

    def skip(self):
        super().skip()
    
    def drawAsGameLogic(self, gameDisplay):
        super().drawAsGameLogic(gameDisplay)
        for elementIndex in range(len(self.interactableElements)):
            if self.drawFlagsInteractableElements[elementIndex]:
                self.interactableElements[elementIndex].draw(gameDisplay)

    def handleEventAsGameLogic(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for elementIndex in range(len(self.interactableElements)):
                if self.interactableElements[elementIndex].wasClicked(event.pos):
                    self.drawFlagsInteractableElements[elementIndex] = True
                        
        elif event.type == pygame.MOUSEBUTTONUP:
            for elementIndex in range(len(self.interactableElements)):
                if self.drawFlagsInteractableElements[elementIndex] == 1:
                    if elementIndex in self.solutionElements:
                        self.setVictory()
                    else:
                        self.setLoss()
                self.drawFlagsInteractableElements[elementIndex] = False