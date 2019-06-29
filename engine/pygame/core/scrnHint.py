import coreProp, coreAnim, coreState, pygame

class HintTab():
    def __init__(self):
        pass

class Screen(coreState.LaytonContext):

    def __init__(self, puzzleIndex):
        coreState.LaytonContext.__init__(self)
        self.upCount = 0

    def draw(self, gameDisplay):
        pygame.draw.rect(gameDisplay,
                         (255,255,255,255),
                         (0,coreProp.LAYTON_SCREEN_HEIGHT,coreProp.LAYTON_SCREEN_WIDTH,coreProp.LAYTON_SCREEN_HEIGHT))

    def update(self):
        self.upCount += 1
        if self.upCount >= 10:
            self.isContextFinished = True
            print("Context finished!")
    
    def handleEvent(self, event):
        pass
