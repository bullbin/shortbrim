import pygame, coreState, coreProp, coreAnim, coreLib, eventHandler
from os import path
pygame.init()

class AnimatedImageEvent(coreAnim.AnimatedImage):
    def __init__(self, indexEvent, frameRootPath, frameName, frameRootExtension="png", x=0,y=0, importAnimPair=True, usesAlpha=True):
        coreAnim.AnimatedImage.__init__(self, frameRootPath, frameName, frameRootExtension=frameRootExtension, x=x, y=y, importAnimPair=importAnimPair, usesAlpha=usesAlpha)
        self.indexEvent = indexEvent
        self.bounding = [0,0]
    
    def wasClicked(self, mousePos):
        if self.pos[0] + self.bounding[0] >= mousePos[0] and mousePos[0] >= self.pos[0]:
            if self.pos[1] + self.bounding[1] >= mousePos[1] and mousePos[1] >= self.pos[1]:
                return True
        return False

class LaytonHelperEventHandlerSpawner(coreState.LaytonContext):

    DURATION_EVENT_FADE_OUT = 333
    DURATION_EVENT_ICON_JUMP = 444
    DURATION_EVENT_ICON_JUMP_PAUSE = 222
    HEIGHT_EVENT_ICON_JUMP = 25
    ICON_BUTTONS = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, "icon_buttons") 
    ICON_BUTTONS.setAnimationFromName("found")

    def __init__(self, indexEvent, pos, playerState):
        coreState.LaytonContext.__init__(self)
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True
        self.screenIsOverlay        = True

        self.indexEvent = indexEvent
        self.playerState = playerState
        self.faderSurface = pygame.Surface((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT * 2)).convert_alpha()
        self.eventBlackoutFader = coreAnim.AnimatedFader(LaytonHelperEventHandlerSpawner.DURATION_EVENT_FADE_OUT,
                                                         coreAnim.AnimatedFader.MODE_SINE_SHARP, False, cycle=False)
        self.iconBounceFader = coreAnim.AnimatedFader(LaytonHelperEventHandlerSpawner.DURATION_EVENT_ICON_JUMP,
                                                      coreAnim.AnimatedFader.MODE_SINE_SMOOTH, False)
        self.iconBounceWaitDuration = 0                          
        self.iconBounceCenter = (pos[0] - (LaytonHelperEventHandlerSpawner.ICON_BUTTONS.dimensions[0] // 2),
                                 pos[1] - (LaytonHelperEventHandlerSpawner.ICON_BUTTONS.dimensions[1] // 2))
        LaytonHelperEventHandlerSpawner.ICON_BUTTONS.reset()
    
    def update(self, gameClockDelta):
        self.iconBounceFader.update(gameClockDelta)
        LaytonHelperEventHandlerSpawner.ICON_BUTTONS.update(gameClockDelta)
        LaytonHelperEventHandlerSpawner.ICON_BUTTONS.pos = (self.iconBounceCenter[0],
                                                            self.iconBounceCenter[1] - round(LaytonHelperEventHandlerSpawner.HEIGHT_EVENT_ICON_JUMP * self.iconBounceFader.getStrength()))
        if not(self.iconBounceFader.isActive):
            if self.iconBounceWaitDuration >= LaytonHelperEventHandlerSpawner.DURATION_EVENT_ICON_JUMP_PAUSE:
                self.eventBlackoutFader.update(gameClockDelta)
                if self.eventBlackoutFader.getStrength() == 1:
                    self.screenNextObject = eventHandler.LaytonEventHandler(self.indexEvent, self.playerState)
                    self.isContextFinished = True
            else:
                self.iconBounceWaitDuration += gameClockDelta
    
    def draw(self, gameDisplay):
        LaytonHelperEventHandlerSpawner.ICON_BUTTONS.draw(gameDisplay)
        self.faderSurface.fill((0,0,0,round(self.eventBlackoutFader.getStrength() * 255)))
        gameDisplay.blit(self.faderSurface, (0,0))

class LaytonRoomBackground(coreState.LaytonContext):

    def __init__(self, roomIndex, playerState):
        coreState.LaytonContext.__init__(self)
        
        # Set screen variables
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True

        try:
            self.backgroundBs = pygame.image.load(coreProp.PATH_ASSET_BG + "room_" + str(roomIndex) + "_bg.png").convert()
        except:
            self.backgroundBs = pygame.image.load(coreProp.PATH_ASSET_BG + coreProp.LAYTON_ASSET_LANG + "\\q_bg.png").convert()

    def draw(self, gameDisplay):
        gameDisplay.blit(self.backgroundBs, (0,coreProp.LAYTON_SCREEN_HEIGHT))

class LaytonRoomUi(coreState.LaytonContext):
    def __init__(self, playerState):
        coreState.LaytonContext.__init__(self)
        self.screenIsOverlay        = True

class LaytonRoomTapObject(coreState.LaytonContext):
    
    backgroundBs = pygame.image.load(coreProp.PATH_ASSET_ANI + "room_tobj_0.png").convert_alpha()
    backgroundPos = ((coreProp.LAYTON_SCREEN_WIDTH - backgroundBs.get_width()) // 2, ((coreProp.LAYTON_SCREEN_HEIGHT - backgroundBs.get_height()) // 2) + coreProp.LAYTON_SCREEN_HEIGHT)
    backgroundTransBs = backgroundBs.copy().convert()
    backgroundTransBsDuration = 250
    portraitPos = (backgroundPos[0] + 6, backgroundPos[1] + ((backgroundBs.get_height() - 24) // 2))
    cursorBs = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, "cursor_wait")
    cursorBs.pos = ((backgroundPos[0] + backgroundBs.get_width()) - (cursorBs.dimensions[0] + 4), (backgroundPos[1] + backgroundBs.get_height()) - (cursorBs.dimensions[1] + 4))

    def __init__(self, indexCharacter, indexTobj, font):
        coreState.LaytonContext.__init__(self)
        self.screenIsOverlay        = True
        self.transitionsEnableIn    = False         # The background actually fades in but the context switcher only supports fading to black
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True
        self.backgroundPortrait     = pygame.image.load(coreProp.PATH_ASSET_ANI + "room_tobjp_" + str(indexCharacter) + ".png").convert_alpha()

        with open(coreProp.PATH_ASSET_ROOM + "tobj\\" + coreProp.LAYTON_ASSET_LANG + "\\tobj\\t_" + str(indexTobj) + ".txt", 'r') as tText:
            tobjFillText = tText.read()
        
        if type(font) == coreAnim.FontMap:
            tobjTextPos = (LaytonRoomTapObject.portraitPos[0] + self.backgroundPortrait.get_width() + (LaytonRoomTapObject.portraitPos[0] - LaytonRoomTapObject.backgroundPos[0]),
                           LaytonRoomTapObject.backgroundPos[1] + ((LaytonRoomTapObject.backgroundBs.get_height() + font.getSpacing()[1] - (len(tobjFillText.split("\n")) * font.get_height())) // 2))
        else:
            tobjTextPos = (LaytonRoomTapObject.portraitPos[0] + self.backgroundPortrait.get_width() + (LaytonRoomTapObject.portraitPos[0] - LaytonRoomTapObject.backgroundPos[0]),
                           LaytonRoomTapObject.backgroundPos[1] + ((LaytonRoomTapObject.backgroundBs.get_height() - (len(tobjFillText.split("\n")) * font.get_height())) // 2))
        self.tobjText               = coreAnim.TextScroller(font, tobjFillText, textPosOffset=tobjTextPos)
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

            if self.transitioningIn:
                intensity = round((self.transitioningTotal / LaytonRoomTapObject.backgroundTransBsDuration) * 255)
            else:
                intensity = 255 - round((self.transitioningTotal / LaytonRoomTapObject.backgroundTransBsDuration) * 255)
            
            if coreProp.ENGINE_PERFORMANCE_MODE:
                LaytonRoomTapObject.backgroundTransBs.set_alpha(intensity)
            else:
                LaytonRoomTapObject.backgroundTransBs = LaytonRoomTapObject.backgroundBs.copy().convert_alpha()
                LaytonRoomTapObject.backgroundTransBs.fill((255, 255, 255, intensity), None, pygame.BLEND_RGBA_MULT)
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
        self.indexCharacter = indexCharacter - 1

    def wasClicked(self, mousePos):
        if self.pos[0] + self.dimensions[0] >= mousePos[0] and mousePos[0] >= self.pos[0]:
            if self.pos[1] + self.dimensions[1] >= mousePos[1] and mousePos[1] >= self.pos[1]:
                return True
        return False

    def getContext(self, playerState):
        return LaytonRoomTapObject(self.indexCharacter, self.indexTobj, playerState.getFont("fontevent"))

class LaytonRoomGraphics(coreState.LaytonContext):

    animTap = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, "touch_icon")

    def __init__(self, playerState):
        coreState.LaytonContext.__init__(self)
        self.screenBlockInput       = True
        self.screenIsBasicOverlay   = True

        self.playerState = playerState

        self.animObjects = []
        self.eventObjects = []
        self.drawnTobj   = []
        self.drawnEvents = []
        self.eventTap  = []
        self.eventHint = []
        self.eventHintId = []

        self.animTapDraw = False
    
    def draw(self, gameDisplay):
        for sprite in self.animObjects:
            sprite.draw(gameDisplay)
        for sprite in self.eventObjects:
            sprite.draw(gameDisplay)
        if self.animTapDraw:
            LaytonRoomGraphics.animTap.draw(gameDisplay)

    def update(self, gameClockDelta):
        for sprite in self.animObjects:
            sprite.update(gameClockDelta)
        for sprite in self.eventObjects:
            sprite.update(gameClockDelta)
        if self.animTapDraw:
            LaytonRoomGraphics.animTap.update(gameClockDelta)

    def executeCommand(self, command):
        if command.opcode == b'\x43':                         # Add tobj
            if ((command.operands[1], command.operands[2])) not in self.drawnTobj:
                self.eventTap.append(LaytonRoomTapRegion(command.operands[0], (command.operands[1], command.operands[2] + coreProp.LAYTON_SCREEN_HEIGHT),
                                                        (command.operands[3], command.operands[4]), command.operands[5]))
                self.drawnTobj.append((command.operands[1], command.operands[2]))
            else:
                coreState.debugPrint("ErrGraphicsTobjFatal: Tobj overshoot, number " + str(command.operands[5]))
        elif command.opcode == b'\x5c':                       # Add animated image
            if command.operands[2][-4:] == ".spr":
                command.operands[2] = command.operands[2][0:-4]
            
            self.animObjects.append(coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, command.operands[2],
                                                           x = command.operands[0], y = command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT))
            if not(self.animObjects[-1].setAnimationFromIndex(0)):
                    self.animObjects[-1].setActiveFrame(0)

        elif command.opcode == b'\x50':                     # Add interactable sprite
            if command.operands[4] not in self.drawnEvents and (path.exists(coreProp.PATH_ASSET_ANI + "obj_" + str(command.operands[4]) + ".png")
                                                                or path.exists(coreProp.PATH_ASSET_ANI + "obj_" + str(command.operands[4]) + "_0.png")):
                self.eventObjects.append(AnimatedImageEvent(command.operands[5], coreProp.PATH_ASSET_ANI, "obj_" + str(command.operands[4]),
                                                           x = command.operands[0], y = command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT))
                self.eventObjects[-1].bounding = [command.operands[2], command.operands[3]]
                if not(self.eventObjects[-1].setAnimationFromIndex(0)):
                    self.eventObjects[-1].setActiveFrame(0)
                self.drawnEvents.append(command.operands[4])

        elif command.opcode == b'\x68' and command.operands[0] not in self.playerState.hintCoinsFound:
            self.eventHint.append(LaytonRoomTapRegion(3, (command.operands[1], command.operands[2] + coreProp.LAYTON_SCREEN_HEIGHT),
                                                      (command.operands[3], command.operands[4]), command.operands[5]))
            self.eventHintId.append(command.operands[0])
        else:
            coreState.debugPrint("ErrGraphicsUnkCommand: " + str(command.opcode))
    
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.animTapDraw = True
            for eventTobj in self.eventTap:
                if eventTobj.wasClicked(event.pos):
                    self.screenNextObject = eventTobj.getContext(self.playerState)
                    self.animTapDraw = False
                    return True
            for animObject in self.eventObjects:
                if animObject.wasClicked(event.pos):
                    self.screenNextObject = LaytonHelperEventHandlerSpawner(animObject.indexEvent, event.pos, self.playerState)
                    coreState.debugPrint("WarnGraphicsCommand: Spawned event handler for ID " + str(animObject.indexEvent))
                    self.animTapDraw = False
                    return True

            hintCoinIndex = 0
            for _eventHintTobjIndex in range(len(self.eventHint)):
                if self.eventHint[hintCoinIndex].wasClicked(event.pos):
                    self.playerState.hintCoinsFound.append(self.eventHintId.pop(hintCoinIndex))
                    self.playerState.remainingHintCoins += 1
                    self.screenNextObject = self.eventHint.pop(hintCoinIndex).getContext(self.playerState)
                    self.animTapDraw = False
                    hintCoinIndex -= 1
                    return True
                if hintCoinIndex < 0:
                    break
                hintCoinIndex += 1

            if self.animTapDraw:
                LaytonRoomGraphics.animTap.pos = (event.pos[0] - (LaytonRoomGraphics.animTap.dimensions[0] // 2),
                                                  event.pos[1] - (LaytonRoomGraphics.animTap.dimensions[1] // 2))
                LaytonRoomGraphics.animTap.setAnimationFromIndex(0)
                LaytonRoomGraphics.animTap.reset()    
        return False

class LaytonRoomHandler(coreState.LaytonSubscreen):

    def __init__(self, roomIndex, playerState):
        coreState.LaytonSubscreen.__init__(self)
        self.transitionsEnableIn = False
        self.transitionsEnableOut = False
        self.screenBlockInput = True

        self.addToStack(LaytonRoomBackground(roomIndex, playerState))
        self.addToStack(LaytonRoomGraphics(playerState))
        self.commandFocus = self.stack[-1]
        self.executeGdScript(coreLib.gdScript(coreProp.PATH_ASSET_SCRIPT + "rooms\\room" + str(roomIndex) + "_param.gds", playerState))
        self.addToStack(LaytonRoomUi(playerState))

    def executeGdScript(self, puzzleScript):

        for command in puzzleScript.commands:
            if command.opcode == b'\x0b':
                self.stack[0].backgroundBs = pygame.image.load(coreProp.PATH_ASSET_BG + command.operands[0][0:-3] + "png").convert()
            elif self.commandFocus == None:
                self.executeCommand(command)
            else:
                self.commandFocus.executeCommand(command)
    
    def executeCommand(self, command):
        coreState.debugPrint("CommandNoTarget: " + str(command.opcode))

if __name__ == '__main__':
    playerState = coreState.LaytonPlayerState()
    playerState.puzzleLoadData()
    playerState.puzzleLoadNames()
    playerState.remainingHintCoins = 10
    coreState.play(LaytonRoomHandler(4, playerState), playerState)