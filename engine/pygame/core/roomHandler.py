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

class LaytonRoomTapObject(coreState.LaytonContext):
    
    backgroundBs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "ani\\room_tobj.png")
    backgroundPos = ((coreProp.LAYTON_SCREEN_WIDTH - backgroundBs.get_width()) // 2,
                     ((coreProp.LAYTON_SCREEN_HEIGHT - backgroundBs.get_height()) // 2) + coreProp.LAYTON_SCREEN_HEIGHT)
    portraitPos = (backgroundPos[0] + 4,
                   backgroundPos[1] + ((backgroundBs.get_height() - 24) // 2))
    cursorBs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "ani\\cursor_wait.png")
    cursorPos = ((backgroundPos[0] + backgroundBs.get_width()) - (cursorBs.get_width() + 4),
                 (backgroundPos[1] + backgroundBs.get_height()) - (cursorBs.get_height() + 4))

    def __init__(self, indexCharacter, indexTobj):
        coreState.LaytonContext.__init__(self)
        self.screenIsOverlay        = True
        self.transitionsEnableIn    = False         # The background actually fades in but the context switcher only supports fading to black
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True
        self.backgroundPortrait     = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "ani\\room_tobjp_" + str(indexCharacter) + ".png")

        with open(coreProp.LAYTON_ASSET_ROOT + r"room\tobj\en\tobj\t_" + str(indexTobj) + ".txt", 'r') as tText:
            self.tobjText               = coreAnim.TextScroller(tText.read(),
                                                                textPosOffset=(LaytonRoomTapObject.portraitPos[0] + self.backgroundPortrait.get_width() + (LaytonRoomTapObject.portraitPos[0] - LaytonRoomTapObject.backgroundPos[0]),
                                                                               LaytonRoomTapObject.backgroundPos[1]))

        self.tobjText.skip()
    
    def draw(self, gameDisplay):
        gameDisplay.blit(LaytonRoomTapObject.backgroundBs, LaytonRoomTapObject.backgroundPos)
        gameDisplay.blit(self.backgroundPortrait, LaytonRoomTapObject.portraitPos)
        gameDisplay.blit(LaytonRoomTapObject.cursorBs, LaytonRoomTapObject.cursorPos)
        self.tobjText.draw(gameDisplay)

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.isContextFinished = True

class LaytonRoomTapRegion():
    def __init__(self, indexCharacter, pos, dimensions, indexTobj):
        self.pos = pos
        self.dimensions = dimensions
        self.indexTobj = indexTobj
        self.indexCharacter = indexCharacter

    def wasClicked(self, mousePos):
        mX, mY = mousePos
        pX, pY = self.pos
        dX, dY = self.dimensions

        if pX + dX >= mX and mX >= pX:
            if pY + dY >= mY and mY >= pY:
                return True
        return False

    def getContext(self):
        return LaytonRoomTapObject(self.indexCharacter, self.indexTobj)

class LaytonRoomGraphics(coreState.LaytonContext):
    def __init__(self):
        coreState.LaytonContext.__init__(self)
        self.screenBlockInput       = True
        self.screenIsBasicOverlay   = True

        self.animObjects = []
        self.drawnEvents = []
        self.eventTap = []
    
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

        elif command.opcode == b'\x43':
            self.eventTap.append(LaytonRoomTapRegion(command.operands[0], (command.operands[1], command.operands[2] + coreProp.LAYTON_SCREEN_HEIGHT),
                                                     (command.operands[3], command.operands[4]), command.operands[5]))
            print(str(command.operands[1]) + ", " + str(command.operands[2] + coreProp.LAYTON_SCREEN_HEIGHT))

        else:
            print("UnkCommand: " + str(command.opcode))
    
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for eventTobj in self.eventTap:
                if eventTobj.wasClicked(event.pos):
                    self.screenNextObject = eventTobj.getContext()

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