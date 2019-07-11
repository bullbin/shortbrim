import pygame
from os import path, environ

pygame.init()

LAYTON_ENGINE_FPS           = 60                                        # Target system FPS
LAYTON_SAVE_PATH            = None
LAYTON_ASSET_ROOT           = environ['ONEDRIVE'] + "\\assets\\"        # Root of asset directory
LAYTON_ASSET_LANG           = "en"
LAYTON_PUZZLE_FONT          = pygame.font.SysFont('freesansmono', 17)
LAYTON_PUZZLE_HINT_COST     = 1
LAYTON_SCREEN_HEIGHT        = 192
LAYTON_SCREEN_WIDTH         = 256
LAYTON_PERFORMANCE_MODE     = False                                     # Prioritise speed over quality (disregard frame pacing)