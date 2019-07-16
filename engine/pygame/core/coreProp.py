import pygame
from os import path, environ

pygame.init()

ENGINE_FPS = 60
ENGINE_PERFORMANCE_MODE = False

PATH_SAVE = None
PATH_ASSET_ROOT     = environ['ONEDRIVE'] + "\\assets\\"
PATH_ASSET_ANI      = PATH_ASSET_ROOT + "ani\\"
PATH_ASSET_BG       = PATH_ASSET_ROOT + "bg\\"
PATH_ASSET_ETEXT    = PATH_ASSET_ROOT + "etext\\"
PATH_ASSET_FONT     = PATH_ASSET_ROOT + "font\\"
PATH_ASSET_QTEXT    = PATH_ASSET_ROOT + "qtext\\"
PATH_ASSET_ROOM     = PATH_ASSET_ROOT + "room\\"
PATH_ASSET_SCRIPT   = PATH_ASSET_ROOT + "script\\"

LAYTON_ASSET_LANG           = "en"

GRAPHICS_USE_GAME_FONTS = True

LAYTON_PUZZLE_HINT_COST     = 1
LAYTON_SCREEN_HEIGHT        = 192
LAYTON_SCREEN_WIDTH         = 256