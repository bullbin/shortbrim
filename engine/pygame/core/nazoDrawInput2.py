import coreProp, coreAnim, pygame, nazoGeneric

class LaytonPuzzleHandler(nazoGeneric.LaytonPuzzleHandler):

    buttonEntry = None
    buttonClear = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "ani\\nazo\\drawinput\\" + coreProp.LAYTON_ASSET_LANG + r"\clear.png")
    buttonBack = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "ani\\nazo\\drawinput\\" + coreProp.LAYTON_ASSET_LANG + r"\back.png")
    buttonErase = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "ani\\nazo\\drawinput\\" + coreProp.LAYTON_ASSET_LANG + r"\erase.png")
    
    def __init__(self, playerState, puzzleIndex, puzzleScript, puzzleEnable = True):
        nazoGeneric.LaytonPuzzleHandler.__init__(self, playerState, puzzleIndex, puzzleScript, puzzleEnable)

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
