import coreProp, coreAnim, coreState, pygame

class HintTab():
    def __init__(self):
        pass

class Screen(coreState.LaytonContext):

    def __init__(self, puzzleIndex):
        coreState.LaytonContext.__init__(self)

    def draw(self, gameDisplay):
        pygame.draw.rect(gameDisplay,
                         (255,255,255,255),
                         (0,0,256,256))

    def update(self):
        pass
    
    def handleEvent(self, event):
        pass
