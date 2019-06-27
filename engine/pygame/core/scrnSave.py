import coreProp, coreAnim, coreState, pygame

class ScreenState():
    def __init__(self, bg):
        self.bg = bg
        self.indexSelected = None

    def draw(self, gameDisplay):
        gameDisplay.blit(self.bg, (0, coreProp.LAYTON_SCREEN_HEIGHT))

class ScreenSave(ScreenState):

    fileLoadImage = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\fileload_bg.png")
    fileLoadOverlayImages = [pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\" + coreProp.LAYTON_ASSET_LANG + "\\fileloading_bg1.png"),
                             pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\" + coreProp.LAYTON_ASSET_LANG + "\\fileloading_bg2.png"),
                             pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\" + coreProp.LAYTON_ASSET_LANG + "\\fileloading_bg3.png")]
    
    def __init__(self):
        ScreenState.__init__(self)
    
    def draw(self, gameDisplay):
        super().draw()
        pass

    def update(self):
        pass

    def handleEvent(self, event):
        pass

class ScreenLoad(ScreenState):
    
    fileSaveImage = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\filesave_bg.png")
    fileSaveOverlay = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\" + coreProp.LAYTON_ASSET_LANG + "\\filesaving_bg.png")

    def __init__(self):
        ScreenState.__init__(self)

    def handleEvent(self, event):
        pass
