import pygame
from os import path, environ

pygame.init()

LAYTON_ENGINE_FPS           = 30        # Game speed is tied to framerate
LAYTON_SAVE_PATH            = None
LAYTON_ASSET_ROOT           = environ['ONEDRIVE'] + "\\assets\\"
LAYTON_ASSET_LANG           = "en"
LAYTON_PUZZLE_FONT          = pygame.font.SysFont('freesansmono', 17)
LAYTON_SCREEN_HEIGHT        = 192
LAYTON_SCREEN_WIDTH         = 256
