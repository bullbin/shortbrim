import coreProp, coreAnim, pygame, nazoGeneric

class Match():

    SHADOW_OFFSET = 2
    
    def __init__(self, surfaceMatch, surfaceShadow, posX, posY, rot):
        self.surfaceMatch = surfaceMatch
        self.surfaceShadow = surfaceShadow
        self.pos = (posX, posY)
        self.rot = rot
        self.region = 32
        self.drawShadow = True

    def draw(self, gameDisplay):
        if self.drawShadow:
            appliedSurface = pygame.transform.rotate(self.surfaceShadow, self.rot)
            x,y = self.pos
            x += Match.SHADOW_OFFSET; y += Match.SHADOW_OFFSET 
            appliedSurfaceRect = appliedSurface.get_rect(center=(x,y))
            gameDisplay.blit(appliedSurface, (appliedSurfaceRect.x, appliedSurfaceRect.y))
        appliedSurface = pygame.transform.rotate(self.surfaceMatch, self.rot)
        appliedSurfaceRect = appliedSurface.get_rect(center=self.pos)
        gameDisplay.blit(appliedSurface, (appliedSurfaceRect.x, appliedSurfaceRect.y))
    
class LaytonPuzzleHandler(nazoGeneric.LaytonPuzzleHandler):

    matchImage = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "ani\\match_match.png")
    matchShadowImage = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "ani\\match_shadow.png")
    
    def __init__(self, playerState, puzzleIndex, puzzleScript, puzzleEnable = True):
        
        self.matches = []
        nazoGeneric.LaytonPuzzleHandler.__init__(self, playerState, puzzleIndex, puzzleScript, puzzleEnable)

        self.puzzleMoveLimit = coreAnim.AnimatedText(initString=str(self.puzzleMoveLimit))

    def executeGdScript(self):
        for command in self.puzzleScript.commands:
            if command.opcode == b'\x0b':
                print("Replace background: " + command.operands[0])
            elif command.opcode == b'\x27':
                self.puzzleMoveLimit = command.operands[0]
                print(self.puzzleMoveLimit)
            elif command.opcode == b'\x2a':
                #self.matches.append(coreAnim.StaticImage(LaytonPuzzleHandler.matchImagePath, x=command.operands[0], y=command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT))
                self.matches.append(Match(LaytonPuzzleHandler.matchImage, LaytonPuzzleHandler.matchShadowImage,
                                          command.operands[0],
                                          command.operands[1]+coreProp.LAYTON_SCREEN_HEIGHT,
                                          command.operands[2]))
    
    def load(self):
        super().load()

    def update(self):
        super().update()

    def skip(self):
        super().skip()

    def draw(self, gameDisplay):
        super().draw(gameDisplay)
        self.puzzleMoveLimit.draw(gameDisplay, location=(46, coreProp.LAYTON_SCREEN_HEIGHT + 176))
        for match in self.matches:
            match.draw(gameDisplay)

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.puzzleEnable:
            self.skip()
            self.puzzleInputWaiting = False
