import coreState, coreProp, coreAnim, gdsLib, pygame

# Testing only
from os import path
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
            self.backgroundBs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\room_" + str(roomIndex) + "_bg.png").convert()
        except:
            self.backgroundBs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\en\\q_bg.png").convert()

    def draw(self, gameDisplay):
        gameDisplay.blit(self.backgroundBs, (0,coreProp.LAYTON_SCREEN_HEIGHT))

class LaytonRoomUi(coreState.LaytonContext):
    def __init__(self, playerState):
        coreState.LaytonContext.__init__(self)
        self.screenIsOverlay        = True

class LaytonRoomTapObject(coreState.LaytonContext):
    
    backgroundBs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "ani\\room_tobj.png").convert_alpha()
    backgroundPos = ((coreProp.LAYTON_SCREEN_WIDTH - backgroundBs.get_width()) // 2, ((coreProp.LAYTON_SCREEN_HEIGHT - backgroundBs.get_height()) // 2) + coreProp.LAYTON_SCREEN_HEIGHT)
    backgroundTransBs = backgroundBs.copy().convert()
    backgroundTransBsDuration = 250
    portraitPos = (backgroundPos[0] + 6, backgroundPos[1] + ((backgroundBs.get_height() - 24) // 2))
    cursorBs = coreAnim.AnimatedImage(coreProp.LAYTON_ASSET_ROOT + "ani\\", "cursor_wait")
    cursorBs.pos = ((backgroundPos[0] + backgroundBs.get_width()) - (cursorBs.dimensions[0] + 4), (backgroundPos[1] + backgroundBs.get_height()) - (cursorBs.dimensions[1] + 4))
    cursorBs.fromImages(coreProp.LAYTON_ASSET_ROOT + "ani\\cursor_wait.txt")

    def __init__(self, indexCharacter, indexTobj):
        coreState.LaytonContext.__init__(self)
        self.screenIsOverlay        = True
        self.transitionsEnableIn    = False         # The background actually fades in but the context switcher only supports fading to black
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True
        self.backgroundPortrait     = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "ani\\room_tobjp_" + str(indexCharacter) + ".png").convert_alpha()

        with open(coreProp.LAYTON_ASSET_ROOT + r"room\tobj\en\tobj\t_" + str(indexTobj) + ".txt", 'r') as tText:
            tobjFillText = tText.read()
        tobjTextPos = (LaytonRoomTapObject.portraitPos[0] + self.backgroundPortrait.get_width() + (LaytonRoomTapObject.portraitPos[0] - LaytonRoomTapObject.backgroundPos[0]),
                       LaytonRoomTapObject.backgroundPos[1] + ((LaytonRoomTapObject.backgroundBs.get_height() - (len(tobjFillText.split("\n")) * coreProp.LAYTON_PUZZLE_FONT.get_height())) // 2))
        self.tobjText               = coreAnim.TextScroller(tobjFillText, textPosOffset=tobjTextPos)
        self.tobjText.skip()

        LaytonRoomTapObject.cursorBs.setAnimationFromIndex(0)
        self.transitioning = True
        self.transitioningIn = True
        self.backgroundAlpha = 0
        self.transitioningTotal = 0

    def update(self, gameClockDelta):
        if self.transitioning == True:
            self.transitioningTotal += gameClockDelta
            if self.transitioningTotal >= LaytonRoomTapObject.backgroundTransBsDuration:
                self.transitioningTotal = LaytonRoomTapObject.backgroundTransBsDuration
                self.transitioning = False
                if self.transitioningIn:
                    self.transitioningIn = False
                else:
                    self.isContextFinished = True

            intensity = round((self.transitioningTotal / LaytonRoomTapObject.backgroundTransBsDuration) * 255)
            if self.transitioningIn:
                LaytonRoomTapObject.backgroundTransBs.set_alpha(intensity)
            else:
                LaytonRoomTapObject.backgroundTransBs.set_alpha(255 - intensity)
        else:
            LaytonRoomTapObject.cursorBs.update(gameClockDelta)

    def draw(self, gameDisplay):
        if self.transitioning:
            gameDisplay.blit(LaytonRoomTapObject.backgroundTransBs, LaytonRoomTapObject.backgroundPos)
        else:
            gameDisplay.blit(LaytonRoomTapObject.backgroundBs, LaytonRoomTapObject.backgroundPos)
            gameDisplay.blit(self.backgroundPortrait, LaytonRoomTapObject.portraitPos)
            LaytonRoomTapObject.cursorBs.draw(gameDisplay)
            self.tobjText.draw(gameDisplay)

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.transitioning == False:
            self.transitioning = True
            self.transitioningTotal = 0

class LaytonRoomTapRegion():
    def __init__(self, indexCharacter, pos, dimensions, indexTobj):
        self.pos = pos
        self.dimensions = dimensions
        self.indexTobj = indexTobj
        self.indexCharacter = indexCharacter

    def wasClicked(self, mousePos):
        if self.pos[0] + self.dimensions[0] >= mousePos[0] and mousePos[0] >= self.pos[0]:
            if self.pos[1] + self.dimensions[1] >= mousePos[1] and mousePos[1] >= self.pos[1]:
                return True
        return False

    def getContext(self):
        return LaytonRoomTapObject(self.indexCharacter, self.indexTobj)

class LaytonRoomEventSpawner():
    def __init__(self, indexObj):
        self.sprite = None

class LaytonRoomGraphics(coreState.LaytonContext):

    animTap = coreAnim.AnimatedImage(coreProp.LAYTON_ASSET_ROOT + "ani\\", "touch_icon")
    animTap.fromImages(coreProp.LAYTON_ASSET_ROOT + "ani\\touch_icon.txt")

    def __init__(self, playerState):
        coreState.LaytonContext.__init__(self)
        self.screenBlockInput       = True
        self.screenIsBasicOverlay   = True

        self.playerState = playerState

        self.animObjects = []
        self.drawnEvents = []
        self.eventTap  = []
        self.eventHint = []
        self.eventHintId = []
    
    def draw(self, gameDisplay):
        for sprite in self.animObjects:
            sprite.draw(gameDisplay)
        LaytonRoomGraphics.animTap.draw(gameDisplay)

    def update(self, gameClockDelta):
        for sprite in self.animObjects:
            sprite.update(gameClockDelta)
        LaytonRoomGraphics.animTap.update(gameClockDelta)

    def executeCommand(self, command):
        if command.opcode == b'\x43':                         # Add tobj
            self.eventTap.append(LaytonRoomTapRegion(command.operands[0], (command.operands[1], command.operands[2] + coreProp.LAYTON_SCREEN_HEIGHT),
                                                     (command.operands[3], command.operands[4]), command.operands[5]))
        elif command.opcode == b'\x5c':                       # Add animated image
            if command.operands[2][-4:] == ".spr":
                command.operands[2] = command.operands[2][0:-4]
            
            self.animObjects.append(coreAnim.AnimatedImage(coreProp.LAYTON_ASSET_ROOT + "ani\\", command.operands[2],
                                                           x = command.operands[0], y = command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT))
            if self.animObjects[-1].fromImages(coreProp.LAYTON_ASSET_ROOT + "ani\\" + command.operands[2] + ".txt"):
                self.animObjects[-1].setAnimationFromIndex(0)
            else:
                self.animObjects[-1].setActiveFrame(0)

        elif command.opcode == b'\x50':                     # Add interactable sprite
            if command.operands[4] not in self.drawnEvents and path.exists(coreProp.LAYTON_ASSET_ROOT + "ani\\obj_" + str(command.operands[4]) + ".png"):
                self.animObjects.append(coreAnim.AnimatedImage(coreProp.LAYTON_ASSET_ROOT + "ani\\", "obj_" + str(command.operands[4]),
                                                           x = command.operands[0], y = command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT))
                if self.animObjects[-1].fromImages(coreProp.LAYTON_ASSET_ROOT + "ani\\" + "obj_" + str(command.operands[4]) + ".txt"):
                    self.animObjects[-1].setAnimationFromIndex(0)
                else:
                    self.animObjects[-1].setActiveFrame(0)
                self.drawnEvents.append(command.operands[4])

        elif command.opcode == b'\x68' and command.operands[0] not in self.playerState.hintCoinsFound:
            self.eventHint.append(LaytonRoomTapRegion(3, (command.operands[1], command.operands[2] + coreProp.LAYTON_SCREEN_HEIGHT),
                                                      (command.operands[3], command.operands[4]), command.operands[5]))
            self.eventHintId.append(command.operands[0])
        else:
            print("UnkCommand: " + str(command.opcode))
    
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            eventTap = True
            for eventTobj in self.eventTap:
                if eventTobj.wasClicked(event.pos):
                    self.screenNextObject = eventTobj.getContext()
                    eventTap = False

            hintCoinIndex = 0
            for eventHintTobjIndex in range(len(self.eventHint)):
                if self.eventHint[hintCoinIndex].wasClicked(event.pos):
                    self.playerState.hintCoinsFound.append(self.eventHintId.pop(hintCoinIndex))
                    self.playerState.remainingHintCoins += 1
                    self.screenNextObject = self.eventHint.pop(hintCoinIndex).getContext()
                    eventTap = False
                    hintCoinIndex -= 1
                if hintCoinIndex < 0:
                    break
                hintCoinIndex += 1

            if eventTap:
                LaytonRoomGraphics.animTap.pos = (event.pos[0] - (LaytonRoomGraphics.animTap.dimensions[0] // 2),
                                                  event.pos[1] - (LaytonRoomGraphics.animTap.dimensions[1] // 2))
                LaytonRoomGraphics.animTap.setAnimationFromIndex(0)

class LaytonRoomHandler(coreState.LaytonSubscreen):

    def __init__(self, roomIndex, playerState):
        coreState.LaytonSubscreen.__init__(self)

        self.addToStack(LaytonRoomBackground(roomIndex, playerState))
        self.addToStack(LaytonRoomGraphics(playerState))

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
                
        gameClockDelta = gameClock.tick(coreProp.LAYTON_ENGINE_FPS)

playerState = coreState.LaytonPlayerState()
playerState.puzzleLoadData()
playerState.puzzleLoadNames()
playerState.remainingHintCoins = 10
play(6, playerState)