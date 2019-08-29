import pygame
from os import path

pygame.init()
pygame.display.set_caption("LAYTON1")

ENGINE_FPS = 60
ENGINE_PERFORMANCE_MODE = False
ENGINE_DEBUG_MODE = True

PATH_SAVE = None
PATH_ASSET_ROOT     = path.dirname(path.dirname(path.dirname(path.dirname(path.realpath(__file__))))) + "\\assets\\"
PATH_ASSET_ANI      = PATH_ASSET_ROOT + "ani\\"
PATH_ASSET_BG       = PATH_ASSET_ROOT + "bg\\"
PATH_ASSET_ETEXT    = PATH_ASSET_ROOT + "etext\\"
PATH_ASSET_FONT     = PATH_ASSET_ROOT + "font\\"
PATH_ASSET_QTEXT    = PATH_ASSET_ROOT + "qtext\\"
PATH_ASSET_ROOM     = PATH_ASSET_ROOT + "room\\"
PATH_ASSET_SCRIPT   = PATH_ASSET_ROOT + "script\\"

LAYTON_ASSET_LANG           = "en"

GRAPHICS_USE_GAME_FONTS = True
GRAPHICS_FONT_CHAR_SUBSTITUTION = {"po":"£"}
GRAPHICS_FONT_COLOR_MAP = {"x":(0,0,0),
                           "r":(255,0,0),
                           "g":(0,255,0),
                           "b":(0,0,255),
                           "w":(255,255,255)}

LAYTON_PUZZLE_HINT_COST     = 1
LAYTON_SCREEN_HEIGHT        = 192
LAYTON_SCREEN_WIDTH         = 256
