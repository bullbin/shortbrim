import coreProp, coreAnim, pygame, nazoGeneric, scrnHint

class LaytonPuzzleHandler(nazoGeneric.LaytonPuzzleHandler):

    buttonEntry = coreAnim.AnimatedImage("ani\\" + coreProp.LAYTON_ASSET_LANG + "\\buttons_kotae.png")
    buttonEntry.pos = (60, coreProp.LAYTON_SCREEN_HEIGHT * 2 - buttonEntry.image.get_height())
    buttonClear = coreAnim.AnimatedImage("ani\\nazo\\drawinput\\" + coreProp.LAYTON_ASSET_LANG + r"\clear.png")
    buttonBack = coreAnim.AnimatedImage("ani\\nazo\\drawinput\\" + coreProp.LAYTON_ASSET_LANG + r"\back.png")
    buttonErase = coreAnim.AnimatedImage("ani\\nazo\\drawinput\\" + coreProp.LAYTON_ASSET_LANG + r"\erase.png")
    
    def __init__(self, playerState, puzzleIndex, puzzleScript, puzzleEnable = True):
        nazoGeneric.LaytonPuzzleHandler.__init__(self, playerState, puzzleIndex, puzzleScript, puzzleEnable)

        self.regions = []

    def load(self):
        super().load()

    def update(self):
        super().update()

    def skip(self):
        super().skip()

    def drawAsGameLogic(self, gameDisplay):
        super().drawAsGameLogic(gameDisplay)
        LaytonPuzzleHandler.buttonEntry.draw(gameDisplay)

    def handleEventAsGameLogic(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if LaytonPuzzleHandler.buttonEntry.wasClicked(event.pos):
                print("Switch internal context: answer input!")
                self.puzzleSubcontexts.stack.append(scrnHint.Screen(self.puzzleIndex))