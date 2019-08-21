import coreProp, coreState, coreLib, coreAnim, pygame
from os import path

import ctypes; ctypes.windll.user32.SetProcessDPIAware()
pygame.init()

class LaytonEventBackground(coreState.LaytonContext):
    def __init__(self, playerState):
        coreState.LaytonContext.__init__(self)
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True
        self.backgroundBs = pygame.Surface((0,0))
        self.backgroundTs = pygame.Surface((0,0))
    
    def executeCommand(self, command):
        if command.opcode == b'\x0c':       # Draw image, TS
            if path.exists(coreProp.PATH_ASSET_BG + command.operands[0][0:-4] + ".png"):
                self.backgroundTs = pygame.image.load(coreProp.PATH_ASSET_BG + command.operands[0][0:-4] + ".png")
        elif command.opcode == b'\x0b':
            if path.exists(coreProp.PATH_ASSET_BG + command.operands[0][0:-4] + ".png"):
                self.backgroundBs = pygame.image.load(coreProp.PATH_ASSET_BG + command.operands[0][0:-4] + ".png")
        else:
            print("ErrUnkCommand: " + str(command.opcode))
    
    def draw(self, gameDisplay):
        gameDisplay.blit(self.backgroundTs, (0, 0))
        gameDisplay.blit(self.backgroundBs, (0, coreProp.LAYTON_SCREEN_HEIGHT))

class LaytonEventGraphics(coreState.LaytonContext):
    def __init__(self, playerState):
        coreState.LaytonContext.__init__(self)
        self.screenIsOverlay = True
        self.drawnEvents = []
        self.drawnAnimEvents = []
    
    def executeCommand(self, command):
        if command.opcode == b'\x6c':           # Draw static image
            self.drawnEvents.append(coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, command.operands[2][0:-4], x=command.operands[0], y=command.operands[1]+coreProp.LAYTON_SCREEN_HEIGHT))
            if not(self.drawnEvents[-1].setAnimationFromName(command.operands[3])):
                self.drawnEvents[-1].setActiveFrame(0)

        elif command.opcode == b'\x6d':           # Draw animated image
            self.drawnAnimEvents.append(coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, command.operands[2][0:-4], x=command.operands[0], y=command.operands[1]+coreProp.LAYTON_SCREEN_HEIGHT))
            if not(self.drawnAnimEvents[-1].setAnimationFromName(command.operands[3])):
                self.drawnAnimEvents[-1].setActiveFrame(0)
            # SpwnFrame not handled
        else:
            print("ErrUnkCommand: " + str(command.opcode))
    
    def update(self, gameClockDelta):
        for event in self.drawnEvents:
            event.update(gameClockDelta)
        for event in self.drawnAnimEvents:
            event.update(gameClockDelta)

    def draw(self, gameDisplay):
        for event in self.drawnEvents:
            event.draw(gameDisplay)
        for event in self.drawnAnimEvents:
            event.draw(gameDisplay)

class LaytonEventHandler(coreState.LaytonSubscreen):

    def __init__(self, eventIndex, playerState):
        coreState.LaytonSubscreen.__init__(self)

        self.addToStack(LaytonEventBackground(playerState))
        self.addToStack(LaytonEventGraphics(playerState))

        self.commandFocus = self.stack[-1]

        self.executeGdScript(coreLib.gdScript(playerState, coreProp.PATH_ASSET_SCRIPT + "event\\e" + str(eventIndex) + ".gds", enableBranching=True))

    def executeGdScript(self, puzzleScript):

        for command in puzzleScript.commands:
            if command.opcode == b'\x0b' or command.opcode == b'\x0c':
                self.stack[0].executeCommand(command)
            elif self.commandFocus == None:
                self.executeCommand(command)
            else:
                self.commandFocus.executeCommand(command)
    
    def executeCommand(self, command):
        print("CommandNoTarget: " + str(command.opcode))

def play(eventIndex, playerState):
    isActive = True
    gameDisplay = pygame.display.set_mode((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT * 2))
    gameClock = pygame.time.Clock()

    rootHandler = LaytonEventHandler(eventIndex, playerState)

    gameClockDelta = 0

    while isActive:

        rootHandler.update(gameClockDelta)
        rootHandler.draw(gameDisplay)
        pygame.display.update()

        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                isActive = False
            else:
                rootHandler.handleEvent(event)
                
        gameClockDelta = gameClock.tick(coreProp.ENGINE_FPS)

playerState = coreState.LaytonPlayerState()
playerState.puzzleLoadData()
playerState.puzzleLoadNames()
playerState.remainingHintCoins = 10
play(1, playerState)