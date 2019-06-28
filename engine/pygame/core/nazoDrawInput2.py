import coreProp, coreAnim, pygame, nazoGeneric

class LaytonPuzzleHandler(nazoGeneric.LaytonPuzzleHandler):

    buttonEntry = coreAnim.AnimatedImage("ani\\" + coreProp.LAYTON_ASSET_LANG + "\\buttons_kotae.png")
    buttonEntry.pos = (60, coreProp.LAYTON_SCREEN_HEIGHT * 2 - buttonEntry.image.get_height())
    buttonClear = coreAnim.AnimatedImage("ani\\nazo\\drawinput\\" + coreProp.LAYTON_ASSET_LANG + r"\clear.png")
    buttonBack = coreAnim.AnimatedImage("ani\\nazo\\drawinput\\" + coreProp.LAYTON_ASSET_LANG + r"\back.png")
    buttonErase = coreAnim.AnimatedImage("ani\\nazo\\drawinput\\" + coreProp.LAYTON_ASSET_LANG + r"\erase.png")
    
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
        if self.modeQuestion:
            LaytonPuzzleHandler.buttonEntry.draw(gameDisplay)

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.puzzleEnable:
                if self.puzzleInputWaiting:
                    self.skip()
                    self.puzzleInputWaiting = False
                    
                elif not(self.drawTransitioning):
                    if self.modeQuestion:
                        if LaytonPuzzleHandler.buttonEntry.wasClicked(event.pos):
                            # self.drawTransitioning = True
                            # self.modeQuestion = False
                            print("Switch internal context: answer input!")
    
