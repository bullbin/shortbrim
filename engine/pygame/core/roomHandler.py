import coreState, coreProp, coreAnim, gdsLib, pygame

# Testing only
import ctypes; ctypes.windll.user32.SetProcessDPIAware()
pygame.init()

class LaytonRoomBackground(coreState.LaytonContext):

    def __init__(self, roomIndex, playerState):
        coreState.LaytonContext.__init__(self)
        
        # Set screen variables
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True

        try:
            self.backgroundBs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\room_" + str(roomIndex) + "_bg.png")
        except:
            self.backgroundBs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\en\\q_bg.png")

    def draw(self, gameDisplay):
        gameDisplay.blit(self.backgroundBs, (0,coreProp.LAYTON_SCREEN_HEIGHT))

class LaytonRoomUi(coreState.LaytonContext):
    def __init__(self, playerState):
        coreState.LaytonContext.__init__(self)
        self.screenIsOverlay        = True

class LaytonRoomGraphics(coreState.LaytonContext):
    def __init__(self):
        coreState.LaytonContext.__init__(self)
        self.screenBlockInput       = True
        self.screenIsBasicOverlay   = True

        self.animObjects = []
        self.drawnEvents = []
    
    def draw(self, gameDisplay):
        for sprite in self.animObjects:
            sprite.draw(gameDisplay)

    def executeCommand(self, command):
        if command.opcode == b'\x5c':
            if command.operands[2][-4:] == ".spr":
                command.operands[2] = command.operands[2][0:-4] + ".png"
            self.animObjects.append(coreAnim.AnimatedImage("ani\\" + command.operands[2],
                                    x = command.operands[0], y = command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT))
        elif command.opcode == b'\x50':
            if command.operands[4] not in self.drawnEvents:
                self.animObjects.append(coreAnim.AnimatedImage("ani\\obj_" + str(command.operands[4]) + ".png",
                                        x = command.operands[0], y = command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT))
                self.drawnEvents.append(command.operands[4])
        else:
            print("UnkCommand: " + str(command.opcode))

class LaytonRoomHandler(coreState.LaytonSubscreen):

    def __init__(self, roomIndex, playerState):
        coreState.LaytonSubscreen.__init__(self)

        self.addToStack(LaytonRoomBackground(roomIndex, playerState))
        self.addToStack(LaytonRoomGraphics())

        self.commandFocus = self.stack[-1]

        self.executeGdScript(gdsLib.gdScript(coreProp.LAYTON_ASSET_ROOT + "script\\rooms\\room" + str(roomIndex) + "_param.gds"))
        self.addToStack(LaytonRoomUi(playerState))

    def executeGdScript(self, puzzleScript):

        for command in puzzleScript.commands:
            if self.commandFocus == None:
                self.executeCommand(command)
            else:
                self.commandFocus.executeCommand(command)
    
    def executeCommand(self, command):
        print("CommandNoTarget: " + str(command.opcode))

def play(eventIndex, playerState):
    isActive = True
    gameDisplay = pygame.display.set_mode((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT * 2))
    gameClock = pygame.time.Clock()

    rootHandler = LaytonRoomHandler(eventIndex, playerState)

    while isActive:

        rootHandler.update()
        rootHandler.draw(gameDisplay)
        pygame.display.update()

        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                isActive = False
            else:
                rootHandler.handleEvent(event)
                
        gameClock.tick(coreProp.LAYTON_ENGINE_FPS)

playerState = coreState.LaytonPlayerState()
playerState.puzzleLoadData()
playerState.puzzleLoadNames()
playerState.remainingHintCoins = 10
play(1, playerState)    # 25:Match, 26:OnOff, 48:FreeButton