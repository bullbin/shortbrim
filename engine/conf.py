import pygame
from os import path

pygame.init()

# TODO - Set title text and icon from ROM, or assign dynamically
pygame.display.set_caption("LAYTON1")

LAYTON_1 = 0
LAYTON_2 = 1

ENGINE_FPS                      = 60
ENGINE_FRAME_INTERVAL           = 1000 / ENGINE_FPS
ENGINE_FORCE_BUSY_WAIT          = False     # Performance-intensive, but ensures stable frametimes; best with original timer
ENGINE_FORCE_USE_ALT_TIMER      = True     # Enforces alternate timer with lower overhead and support for arbitrary framerates
ENGINE_PERFORMANCE_MODE         = False    # Reduces graphical accuracy in favour of performance

ENGINE_GAME_VARIANT             = LAYTON_1

ENGINE_DEBUG_MODE               = True
ENGINE_DEBUG_FILESYSTEM_MODE    = True

# TODO - Use more widely
ENGINE_DEBUG_ENABLE_SEVERE      = False
ENGINE_DEBUG_ENABLE_LOG         = True

ENGINE_LOAD_FROM_ROM                = False      # Useful for development, but slow for playback

# TODO - Use these variables properly
ENGINE_LOAD_FROM_PATCH              = True
ENGINE_DECOMPRESS_WITH_ROM          = True
ENGINE_LOAD_FROM_DECOMPRESSED       = True

PATH_SAVE           = None
PATH_ROM            = path.dirname(path.dirname(path.realpath(__file__))) + "\\rom1.nds"
PATH_ASSET_ROOT     = path.dirname(path.dirname(path.realpath(__file__))) + "\\assets\\"

FILE_DECOMPRESSED_EXTENSION_IMAGE = ".png"

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

LAYTON_STRING_BOOLEAN = {"true":True, "false":False}