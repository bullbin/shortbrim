import pygame

PARAM = "data"

ANIM_SET_ANIM                   = pygame.USEREVENT + 1
EVENT_WINDOW_UPDATE             = pygame.USEREVENT + 2
EVENT_TRIGGER_END_OF_CLIP       = pygame.USEREVENT + 3
EVENT_TRIGGER_WAIT_FOR_UP       = pygame.USEREVENT + 3

ENGINE_SKIP_CLOCK               = pygame.USEREVENT + 10
ENGINE_RESUME_EXECUTION_STACK   = pygame.USEREVENT + 11

CONF_UPDATE_ALL = pygame.USEREVENT + 20