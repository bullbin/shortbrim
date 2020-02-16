import pygame
from os import path

pygame.init()

LAYTON_1 = 0
LAYTON_2 = 1

ENGINE_FPS                      = 60
ENGINE_FRAME_INTERVAL           = 1000 / ENGINE_FPS

ENGINE_FORCE_BUSY_WAIT          = False     # Performance-intensive. Spins CPU instead of sleeping to ensure very stable frametimes.
ENGINE_FORCE_USE_ALT_TIMER      = True      # Enforces alternate timer with slightly lower overhead and support for arbitrary framerates.
ENGINE_USE_HYBRID_TIMER         = True      # Alt-Timer only. Balances CPU spinning and sleeping for stable frametimes and low CPU usage.
                                            # Recommended and prioritised over busy waiting.

ENGINE_PERFORMANCE_MODE         = False     # Reduces graphical accuracy in favour of performance
ENGINE_ENABLE_CLOCK_BYPASS      = True      # Decreases wait accuracy in favour of hiding engine stutter

ENGINE_GAME_VARIANT             = LAYTON_2

ENGINE_DEBUG_MODE               = True
ENGINE_DEBUG_FILESYSTEM_MODE    = True

# TODO - Use more widely
ENGINE_DEBUG_ENABLE_SEVERE      = False
ENGINE_DEBUG_ENABLE_ERROR       = True
ENGINE_DEBUG_ENABLE_LOG         = False

ENGINE_LOAD_FROM_ROM                = True      # Useful for development, but slow for playback

# TODO - Use these variables properly
ENGINE_LOAD_FROM_PATCH              = True
ENGINE_DECOMPRESS_WITH_ROM          = True
ENGINE_LOAD_FROM_DECOMPRESSED       = False

PATH_SAVE           = None
PATH_ROM            = path.dirname(path.dirname(path.realpath(__file__))) + "\\rom2.nds"
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
GRAPHICS_FONT_CHAR_SUBSTITUTION = {"po":"£",
                                   "-":"-",
                                   "''":'"'}
GRAPHICS_FONT_COLOR_MAP = {"x":(0,0,0),
                           "r":(255,0,0),
                           "g":(0,255,0),
                           "b":(0,0,255),
                           "w":(255,255,255)}

LAYTON_PUZZLE_HINT_COST     = 1
LAYTON_SCREEN_HEIGHT        = 192
LAYTON_SCREEN_WIDTH         = 256

LAYTON_STRING_BOOLEAN = {"true":True, "false":False}

if ENGINE_GAME_VARIANT == LAYTON_1:
    pygame.display.set_caption("LAYTON1")
elif ENGINE_GAME_VARIANT == LAYTON_2:
    pygame.display.set_caption("LAYTON2")
else:
    pygame.display.set_caption("UNKNOWN GAME_VER")
