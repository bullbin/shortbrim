import pygame
from os import path

pygame.init()

LAYTON_ENGINE_FPS           = 30        # Game speed is tied to framerate
LAYTON_SAVE_PATH            = None
LAYTON_ASSET_ROOT           = path.dirname(path.dirname(path.dirname(path.dirname(path.realpath(__file__))))) + r"\assets\\"
LAYTON_ASSET_LANG           = "en"
#LAYTON_PUZZLE_FONT          = pygame.font.SysFont('consolas', 10)
LAYTON_PUZZLE_FONT          = pygame.font.SysFont('freesansmono', 17)
LAYTON_SCREEN_HEIGHT        = 192
LAYTON_SCREEN_WIDTH         = 256
