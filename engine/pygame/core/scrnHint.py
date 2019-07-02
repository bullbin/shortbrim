import coreProp, coreAnim, coreState, pygame

class HintTab():
    def __init__(self):
        pass

class Screen(coreState.LaytonContext):

    buttonQuit = coreAnim.AnimatedImage("ani\\" + coreProp.LAYTON_ASSET_LANG + "\\buttons_modoru.png")
    buttonQuit.pos = (coreProp.LAYTON_SCREEN_WIDTH - buttonQuit.image.get_width(), coreProp.LAYTON_SCREEN_HEIGHT)

    def __init__(self, puzzleIndex):
        coreState.LaytonContext.__init__(self)
        self.screenIsOverlay        = True
        self.screenBlockInput       = True
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False

    def draw(self, gameDisplay):
        pygame.draw.rect(gameDisplay,
                         (255,255,255,255),
                         (0,coreProp.LAYTON_SCREEN_HEIGHT,coreProp.LAYTON_SCREEN_WIDTH,coreProp.LAYTON_SCREEN_HEIGHT))
        Screen.buttonQuit.draw(gameDisplay)

    def update(self):
        pass
    
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if Screen.buttonQuit.wasClicked(event.pos):
                self.isContextFinished = True
