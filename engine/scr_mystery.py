import pygame, conf, anim, state
from file import FileInterface

pygame.display.set_mode((conf.LAYTON_SCREEN_WIDTH, conf.LAYTON_SCREEN_HEIGHT * 2))

class Screen(state.LaytonContext):

    def __init__(self, playerState):
        state.LaytonContext.__init__(self)
        self.screenIsOverlay        = True
        self.screenBlockInput       = True
    
    