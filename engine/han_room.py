import pygame, state, conf, anim, script, han_event, file
from os import path
pygame.init()

class AnimatedImageEvent(anim.AnimatedImage):
    def __init__(self, indexEvent, frameRootPath, frameName, frameRootExtension="png", x=0,y=0, importAnimPair=True, usesAlpha=True):
        anim.AnimatedImage.__init__(self, frameRootPath, frameName, frameRootExtension=frameRootExtension, x=x, y=y, importAnimPair=importAnimPair, usesAlpha=usesAlpha)
        self.indexEvent = indexEvent
        self.bounding = [0,0]
    
    def wasClicked(self, mousePos):
        if self.pos[0] + self.bounding[0] >= mousePos[0] and mousePos[0] >= self.pos[0]:
            if self.pos[1] + self.bounding[1] >= mousePos[1] and mousePos[1] >= self.pos[1]:
                return True
        return False

class LaytonHelperEventHandlerSpawner(state.LaytonContext):

    DURATION_EVENT_FADE_OUT = 500
    DURATION_EVENT_ICON_JUMP = 333
    DURATION_EVENT_ICON_JUMP_PAUSE = 333
    HEIGHT_EVENT_ICON_JUMP = 20
    ICON_BUTTONS = anim.AnimatedImage(conf.PATH_ASSET_ANI, "icon_buttons") 
    ICON_BUTTONS.setAnimationFromName("found")

    def __init__(self, indexEvent, pos, playerState):
        state.LaytonContext.__init__(self)
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True
        self.screenIsOverlay        = True

        self.indexEvent = indexEvent
        self.playerState = playerState
        self.faderSurface = pygame.Surface((conf.LAYTON_SCREEN_WIDTH, conf.LAYTON_SCREEN_HEIGHT * 2)).convert_alpha()
        self.eventBlackoutFader = anim.AnimatedFader(LaytonHelperEventHandlerSpawner.DURATION_EVENT_FADE_OUT,
                                                         anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False)
        self.iconBounceFader = anim.AnimatedFader(LaytonHelperEventHandlerSpawner.DURATION_EVENT_ICON_JUMP,
                                                      anim.AnimatedFader.MODE_SINE_SHARP, False)
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
                if not(self.eventBlackoutFader.isActive) and self.eventBlackoutFader.getStrength() == 1:
                    self.screenNextObject = han_event.LaytonEventHandler(self.indexEvent, self.playerState)
                    self.isContextFinished = True
            else:
                self.iconBounceWaitDuration += gameClockDelta
    
    def draw(self, gameDisplay):
        LaytonHelperEventHandlerSpawner.ICON_BUTTONS.draw(gameDisplay)
        self.faderSurface.fill((0,0,0,round(self.eventBlackoutFader.getStrength() * 255)))
        gameDisplay.blit(self.faderSurface, (0,0))

class LaytonRoomBackground(state.LaytonContext):

    def __init__(self, roomIndex, playerState):
        state.LaytonContext.__init__(self)
        
        # Set screen variables
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True

        try:
            self.backgroundBs = pygame.image.load(conf.PATH_ASSET_BG + "room_" + str(roomIndex) + "_bg.png").convert()
        except:
            self.backgroundBs = pygame.image.load(conf.PATH_ASSET_BG + conf.LAYTON_ASSET_LANG + "\\q_bg.png").convert()

    def draw(self, gameDisplay):
        gameDisplay.blit(self.backgroundBs, (0,conf.LAYTON_SCREEN_HEIGHT))

class LaytonRoomUi(state.LaytonContext):
    def __init__(self, playerState):
        state.LaytonContext.__init__(self)
        self.screenIsOverlay        = True

class LaytonRoomTapObject(state.LaytonContext):
    
    DURATION_BACKGROUND_TRANS_BS = 500
    BACKGROUND_BS = anim.AnimatedImage(conf.PATH_ASSET_ANI, "room_tobj", usesAlpha=True)
    BACKGROUND_BS.pos = ((conf.LAYTON_SCREEN_WIDTH - BACKGROUND_BS.dimensions[0]) // 2, ((conf.LAYTON_SCREEN_HEIGHT - BACKGROUND_BS.dimensions[1]) // 2) + conf.LAYTON_SCREEN_HEIGHT)
    BACKGROUND_BS.setAnimationFromName("gfx")
    BACKGROUND_PORTRAIT = anim.AnimatedImage(conf.PATH_ASSET_ANI, "room_tobjp", x=BACKGROUND_BS.pos[0] + 6, y=BACKGROUND_BS.pos[1] + ((BACKGROUND_BS.dimensions[1] - 24) // 2))
    CURSOR_BS = anim.AnimatedImage(conf.PATH_ASSET_ANI, "cursor_wait")
    CURSOR_BS.pos = ((BACKGROUND_BS.pos[0] + BACKGROUND_BS.dimensions[0]) - (CURSOR_BS.dimensions[0] + 4), (BACKGROUND_BS.pos[1] + BACKGROUND_BS.dimensions[1]) - (CURSOR_BS.dimensions[1] + 4))

    def __init__(self, indexCharacter, indexTobj, font):
        state.LaytonContext.__init__(self)
        self.screenIsOverlay        = True
        self.transitionsEnableIn    = False         # The background actually fades in but the context switcher only supports fading to black
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True
        self.backgroundPortrait     = LaytonRoomTapObject.BACKGROUND_PORTRAIT.setAnimationFromNameAndReturnInitialFrame(str(indexCharacter))
        self.backgroundTransFader   = anim.AnimatedFader(LaytonRoomTapObject.DURATION_BACKGROUND_TRANS_BS, anim.AnimatedFader.MODE_SINE_SHARP, False, cycle=False)

        with open(conf.PATH_ASSET_ROOM + "tobj\\" + conf.LAYTON_ASSET_LANG + "\\tobj\\t_" + str(indexTobj) + ".txt", 'r') as tText:
            tobjFillText = tText.read()
        
        if type(font) == anim.FontMap:
            tobjTextPos = (LaytonRoomTapObject.BACKGROUND_PORTRAIT.pos[0] + self.backgroundPortrait.get_width() + (LaytonRoomTapObject.BACKGROUND_PORTRAIT.pos[0] - LaytonRoomTapObject.BACKGROUND_BS.pos[0]),
                           LaytonRoomTapObject.BACKGROUND_BS.pos[1] + ((LaytonRoomTapObject.BACKGROUND_BS.dimensions[1] + font.getSpacing()[1] - (len(tobjFillText.split("\n")) * font.get_height())) // 2))
        else:
            tobjTextPos = (LaytonRoomTapObject.BACKGROUND_PORTRAIT.pos[0] + self.backgroundPortrait.get_width() + (LaytonRoomTapObject.BACKGROUND_PORTRAIT.pos[0] - LaytonRoomTapObject.BACKGROUND_BS.pos[0]),
                           LaytonRoomTapObject.BACKGROUND_BS.pos[1] + ((LaytonRoomTapObject.BACKGROUND_BS.dimensions[1] - (len(tobjFillText.split("\n")) * font.get_height())) // 2))
        self.tobjText               = anim.TextScroller(font, tobjFillText, textPosOffset=tobjTextPos)
        self.tobjText.skip()

        LaytonRoomTapObject.CURSOR_BS.setAnimationFromIndex(0)

    def update(self, gameClockDelta):
        LaytonRoomTapObject.BACKGROUND_BS.update(gameClockDelta)
        self.backgroundTransFader.update(gameClockDelta)
        LaytonRoomTapObject.BACKGROUND_BS.setAlpha(self.backgroundTransFader.getStrength() * 255)
        if not(self.backgroundTransFader.isActive) and self.backgroundTransFader.getStrength() == 0:
            self.isContextFinished = True
        else:
            LaytonRoomTapObject.CURSOR_BS.update(gameClockDelta)

    def draw(self, gameDisplay):
        LaytonRoomTapObject.BACKGROUND_BS.draw(gameDisplay)
        if not(self.backgroundTransFader.isActive):
            gameDisplay.blit(self.backgroundPortrait, LaytonRoomTapObject.BACKGROUND_PORTRAIT.pos)
            LaytonRoomTapObject.CURSOR_BS.draw(gameDisplay)
            self.tobjText.draw(gameDisplay)

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONUP and not(self.backgroundTransFader.isActive):
            self.backgroundTransFader.initialInverted = True
            self.backgroundTransFader.reset()

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

    def getContext(self, playerState):
        return LaytonRoomTapObject(self.indexCharacter, self.indexTobj, playerState.getFont("fontevent"))

class LaytonRoomGraphics(state.LaytonContext):

    animTap = anim.AnimatedImage(conf.PATH_ASSET_ANI, "touch_icon")

    def __init__(self, playerState):
        state.LaytonContext.__init__(self)
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
                self.eventTap.append(LaytonRoomTapRegion(command.operands[0], (command.operands[1], command.operands[2] + conf.LAYTON_SCREEN_HEIGHT),
                                                        (command.operands[3], command.operands[4]), command.operands[5]))
                self.drawnTobj.append((command.operands[1], command.operands[2]))
            else:
                state.debugPrint("ErrGraphicsTobjFatal: Tobj overshoot, number " + str(command.operands[5]))
        elif command.opcode == b'\x5c':                       # Add animated image
            if command.operands[2][-4:] == ".spr":
                command.operands[2] = command.operands[2][0:-4]
            
            self.animObjects.append(anim.AnimatedImage(conf.PATH_ASSET_ANI, command.operands[2],
                                                           x = command.operands[0], y = command.operands[1] + conf.LAYTON_SCREEN_HEIGHT))
            if not(self.animObjects[-1].setAnimationFromIndex(0)):
                    self.animObjects[-1].setActiveFrame(0)

        elif command.opcode == b'\x50':                     # Add interactable sprite
            if command.operands[4] not in self.drawnEvents and (path.exists(conf.PATH_ASSET_ANI + "obj_" + str(command.operands[4]) + ".png")
                                                                or path.exists(conf.PATH_ASSET_ANI + "obj_" + str(command.operands[4]) + "_0.png")):
                self.eventObjects.append(AnimatedImageEvent(command.operands[5], conf.PATH_ASSET_ANI, "obj_" + str(command.operands[4]),
                                                           x = command.operands[0], y = command.operands[1] + conf.LAYTON_SCREEN_HEIGHT))
                self.eventObjects[-1].bounding = [command.operands[2], command.operands[3]]
                if not(self.eventObjects[-1].setAnimationFromIndex(0)):
                    self.eventObjects[-1].setActiveFrame(0)
                self.drawnEvents.append(command.operands[4])

        elif command.opcode == b'\x68' and command.operands[0] not in self.playerState.hintCoinsFound:
            self.eventHint.append(LaytonRoomTapRegion(3, (command.operands[1], command.operands[2] + conf.LAYTON_SCREEN_HEIGHT),
                                                      (command.operands[3], command.operands[4]), command.operands[5]))
            self.eventHintId.append(command.operands[0])
        else:
            state.debugPrint("ErrGraphicsUnkCommand: " + str(command.opcode))
    
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.animTapDraw = True
            for animObject in self.eventObjects:
                if animObject.wasClicked(event.pos):
                    boundingBoxCenterPos = (animObject.pos[0] + animObject.bounding[0] // 2, animObject.pos[1] + animObject.bounding[1] // 2)
                    self.screenNextObject = LaytonHelperEventHandlerSpawner(animObject.indexEvent, boundingBoxCenterPos, self.playerState)
                    state.debugPrint("WarnGraphicsCommand: Spawned event handler for ID " + str(animObject.indexEvent))
                    self.animTapDraw = False
                    return True
            for eventTobj in self.eventTap:
                if eventTobj.wasClicked(event.pos):
                    self.screenNextObject = eventTobj.getContext(self.playerState)
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

class LaytonRoomHandler(state.LaytonSubscreen):

    def __init__(self, roomIndex, playerState):
        state.LaytonSubscreen.__init__(self)
        self.transitionsEnableIn = False
        self.transitionsEnableOut = False
        self.screenBlockInput = True

        self.addToStack(LaytonRoomBackground(roomIndex, playerState))
        self.addToStack(LaytonRoomGraphics(playerState))
        self.commandFocus = self.stack[-1]
        self.executeGdScript(script.gdScript(conf.PATH_ASSET_SCRIPT + "rooms\\room" + str(roomIndex) + "_param.gds", playerState))
        self.addToStack(LaytonRoomUi(playerState))

    def executeGdScript(self, puzzleScript):

        for command in puzzleScript.commands:
            if command.opcode == b'\x0b':
                self.stack[0].backgroundBs = pygame.image.load(conf.PATH_ASSET_BG + command.operands[0][0:-3] + "png").convert()
            elif self.commandFocus == None:
                self.executeCommand(command)
            else:
                self.commandFocus.executeCommand(command)
    
    def executeCommand(self, command):
        state.debugPrint("CommandNoTarget: " + str(command.opcode))

if __name__ == '__main__':
    playerState = state.LaytonPlayerState()
    playerState.puzzleLoadData()
    playerState.puzzleLoadNames()
    playerState.remainingHintCoins = 10
    state.play(LaytonRoomHandler(50, playerState), playerState)