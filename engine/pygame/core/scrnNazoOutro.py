import coreProp, coreAnim, coreState, pygame

class Screen(coreState.LaytonContext):
    def __init__(self, puzzleIndex):
        coreState.LaytonContext.__init__(self)
        self.screenBlockInput       = True
        self.transitionsEnableIn    = True
        self.transitionsEnableOut   = True

    def draw(self, gameDisplay):
        pass

    def update(self):
        pass
