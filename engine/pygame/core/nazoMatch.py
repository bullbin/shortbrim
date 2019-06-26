import coreProp, coreAnim, pygame, nazoGeneric

class LaytonPuzzleHandler(nazoGeneric.LaytonPuzzleHandler):

    matchImagePath = "ani\\match_match.png"
    
    def __init__(self, puzzleIndex, puzzleScript, puzzleEnable = True):
        
        self.matches = []
        nazoGeneric.LaytonPuzzleHandler.__init__(self, puzzleIndex, puzzleScript, puzzleEnable)

    def executeGdScript(self):
        for command in self.puzzleScript.commands:
            if command.opcode == b'\x0b':
                print("Replace background: " + command.operands[0])
            elif command.opcode == b'\x27':
                self.puzzleMoveLimit = command.operands[0]
                print(self.puzzleMoveLimit)
            elif command.opcode == b'\x2a':
                self.matches.append(coreAnim.AnimatedImage(LaytonPuzzleHandler.matchImagePath, x=command.operands[0], y=command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT))
    
    def load(self):
        super().load()

    def update(self):
        super().update()

    def skip(self):
        super().skip()

    def draw(self, gameDisplay):
        super().draw(gameDisplay)
        for match in self.matches:
            match.draw(gameDisplay)

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.puzzleEnable:
            self.skip()
            self.puzzleInputWaiting = False
