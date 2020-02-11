import pygame, state, conf, anim, script, han_event
from hat_io import asset_dat
from file import FileInterface
from os import path
pygame.init()

class AnimatedImageEvent(anim.AnimatedImage):
    def __init__(self, indexEvent, frameRootPath, frameName, frameRootExtension=conf.FILE_DECOMPRESSED_EXTENSION_IMAGE, x=0,y=0, importAnimPair=True, usesAlpha=True):
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
    ICON_BUTTONS = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "map", "icon_buttons") 
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
                    self.faderSurface.fill((0,0,0,255))
                    self.screenNextObject = han_event.LaytonEventHandler(self.indexEvent, self.playerState)
                    self.isContextFinished = True
            else:
                self.iconBounceWaitDuration += gameClockDelta
    
    def draw(self, gameDisplay):
        LaytonHelperEventHandlerSpawner.ICON_BUTTONS.draw(gameDisplay)
        self.faderSurface.fill((0,0,0,round(self.eventBlackoutFader.getStrength() * 255)))
        gameDisplay.blit(self.faderSurface, (0,0))

class LaytonRoomBackground(state.LaytonContext):

    POS_ROOM_TEXT = (170,13)
    POS_GOAL_TEXT = (128,178)

    def __init__(self, placeData, roomIndex, playerState):
        state.LaytonContext.__init__(self)
        
        # Set screen variables
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True
        self.backgroundTs = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "map/map" + str(placeData.mapTsId))
        self.backgroundBs = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "map/main" + str(placeData.mapBgId))

        roomIndexFillText = FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "nazo/" + conf.LAYTON_ASSET_LANG + "/jiten.plz", "p_" + str(roomIndex) + ".txt")
        if roomIndexFillText != None:
            roomIndexFillText = roomIndexFillText.decode('shift-jis')
        else:
            roomIndexFillText = ""

        goalFillText = FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "txt/" + conf.LAYTON_ASSET_LANG + "/txt2.plz", "goal_" + str(playerState.currentObjective) + ".txt")
        if goalFillText != None:
            goalFillText = goalFillText.decode('shift-jis')
        else:
            goalFillText = ""

        self.mapIcon = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "map", "mapicon", x=placeData.mapPos[0], y=placeData.mapPos[1])
        self.mapIcon.setAnimationFromName("gfx")
        self.mapIcon.setInitialFrameFromAnimation()
        self.mapText = anim.AnimatedText(playerState.getFont("fontevent"), initString=roomIndexFillText)
        self.mapTextPos = (LaytonRoomBackground.POS_ROOM_TEXT[0] - (self.mapText.textRender.get_width() // 2),
                           LaytonRoomBackground.POS_ROOM_TEXT[1] - (self.mapText.textRender.get_height() // 2))

        self.goalText = anim.AnimatedText(playerState.getFont("fontevent"), initString=goalFillText)
        self.goalTextPos = (LaytonRoomBackground.POS_GOAL_TEXT[0] - (self.goalText.textRender.get_width() // 2),
                           LaytonRoomBackground.POS_GOAL_TEXT[1] - (self.goalText.textRender.get_height() // 2))

    def draw(self, gameDisplay):
        gameDisplay.blit(self.backgroundTs, (0,0))
        gameDisplay.blit(self.backgroundBs, (0,conf.LAYTON_SCREEN_HEIGHT))
        self.mapIcon.draw(gameDisplay)
        self.mapText.draw(gameDisplay, location=(self.mapTextPos))
        self.goalText.draw(gameDisplay, location=(self.goalTextPos))

class LaytonRoomUi(state.LaytonContext):
    def __init__(self, playerState):
        state.LaytonContext.__init__(self)
        self.screenIsOverlay        = True

class LaytonRoomTapObject(state.LaytonContext):
    
    DURATION_BACKGROUND_TRANS_BS = 666
    BACKGROUND_BS = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "tobj", "window", usesAlpha=True)
    BACKGROUND_BS.pos = ((conf.LAYTON_SCREEN_WIDTH - BACKGROUND_BS.dimensions[0]) // 2, ((conf.LAYTON_SCREEN_HEIGHT - BACKGROUND_BS.dimensions[1]) // 2) + conf.LAYTON_SCREEN_HEIGHT)
    BACKGROUND_BS.setAnimationFromName("gfx")
    BACKGROUND_PORTRAIT = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "tobj", "icon", x=BACKGROUND_BS.pos[0] + 6, y=BACKGROUND_BS.pos[1] + ((BACKGROUND_BS.dimensions[1] - 24) // 2))
    CURSOR_BS = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI, "cursor_wait")
    CURSOR_BS.pos = ((BACKGROUND_BS.pos[0] + BACKGROUND_BS.dimensions[0]) - (CURSOR_BS.dimensions[0] + 4), (BACKGROUND_BS.pos[1] + BACKGROUND_BS.dimensions[1]) - (CURSOR_BS.dimensions[1] + 4))

    def __init__(self, indexCharacter, indexTobj, font):
        state.LaytonContext.__init__(self)
        self.screenIsOverlay        = True
        self.transitionsEnableIn    = False         # The background actually fades in but the context switcher only supports fading to black
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True
        self.backgroundPortrait     = LaytonRoomTapObject.BACKGROUND_PORTRAIT.setAnimationFromNameAndReturnInitialFrame(str(indexCharacter + 1))
        self.backgroundTransFader   = anim.AnimatedFader(LaytonRoomTapObject.DURATION_BACKGROUND_TRANS_BS, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False)
        
        if type(indexTobj) == int:
            tobjFillText = FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "place/" + conf.LAYTON_ASSET_LANG + "/tobj.plz", "tobj" + str(indexTobj) + ".txt")
        else:
            tobjFillText = FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "place/" + conf.LAYTON_ASSET_LANG + "/tobj.plz", str(indexTobj) + ".txt")
        if tobjFillText != None:
            tobjFillText = tobjFillText.decode('shift-jis')
        else:
            tobjFillText = ""

        if self.backgroundPortrait != None:
            if type(font) == anim.FontMap:
                tobjTextPos = (LaytonRoomTapObject.BACKGROUND_PORTRAIT.pos[0] + self.backgroundPortrait.get_width() + (LaytonRoomTapObject.BACKGROUND_PORTRAIT.pos[0] - LaytonRoomTapObject.BACKGROUND_BS.pos[0]),
                            LaytonRoomTapObject.BACKGROUND_BS.pos[1] + ((LaytonRoomTapObject.BACKGROUND_BS.dimensions[1] + font.getSpacing()[1] - (len(tobjFillText.split("\n")) * font.get_height())) // 2))
            else:
                tobjTextPos = (LaytonRoomTapObject.BACKGROUND_PORTRAIT.pos[0] + self.backgroundPortrait.get_width() + (LaytonRoomTapObject.BACKGROUND_PORTRAIT.pos[0] - LaytonRoomTapObject.BACKGROUND_BS.pos[0]),
                            LaytonRoomTapObject.BACKGROUND_BS.pos[1] + ((LaytonRoomTapObject.BACKGROUND_BS.dimensions[1] - (len(tobjFillText.split("\n")) * font.get_height())) // 2))
        else:
            tobjTextPos =  LaytonRoomTapObject.BACKGROUND_PORTRAIT.pos
        self.tobjText               = anim.NuvoTextScroller(font, tobjFillText, textPosOffset=tobjTextPos)
        self.tobjText.skip()

        LaytonRoomTapObject.CURSOR_BS.setAnimationFromName("touch")

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
            if self.backgroundPortrait != None:
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

    animTap = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "map", "touch_icon")
    animTap.loopingDisable()
    
    HINT_FLIP_FALLBACK_TIME = 500

    HINT_FLIP_BS = anim.AnimatedImageWithFadeInOutPerAnim(FileInterface.PATH_ASSET_ANI + "map", "hintcoin", HINT_FLIP_FALLBACK_TIME, False, anim.AnimatedFader.MODE_SINE_SMOOTH)
    if HINT_FLIP_BS.setAnimationFromName("gfx"):
        HINT_FLIP_TIME = HINT_FLIP_BS.animMap[HINT_FLIP_BS.animActive].getAnimLength()
    else:
        HINT_FLIP_TIME = 500
    HINT_FLIP_BS.durationCycle = HINT_FLIP_TIME // 10
    HINT_FLIP_DISTANCE = 25

    def __init__(self, placeData, roomIndex, playerState):
        state.LaytonContext.__init__(self)
        self.screenBlockInput       = True
        self.screenIsBasicOverlay   = True

        self.playerState = playerState
        self.placeData = placeData

        self.animObjects = []
        self.eventObjects = []
        self.eventObjectBoundaries = []

        self.drawnTobj   = []
        self.drawnEvents = []

        self.eventTap  = []
        self.eventHint = []
        self.eventHintId = []

        self.animTapDraw = False
        self.isHintCoinLocked = False
        self.hintCoinLockedIndex = None
        self.hintCoinSpawnLoc = None
        
        for animPos, animName in placeData.objAnim:
            self.animObjects.append(anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "bgani", animName[0:-4],
                                                       x = animPos[0], y = animPos[1] + conf.LAYTON_SCREEN_HEIGHT))
            self.animObjects[-1].setAnimationFromName("gfx")

        for eventData in placeData.objEvent:
            if eventData.idEventObj > 0:
                self.eventObjects.append(anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "eventobj", "obj_" + str(eventData.idEventObj),
                                                        x = eventData.bounding.posCorner[0], y = eventData.bounding.posCorner[1] + conf.LAYTON_SCREEN_HEIGHT))
                self.eventObjects[-1].setAnimationFromName("gfx")
        
        for hintIndex, hintZone in enumerate(placeData.hints):
            self.eventHint.append(LaytonRoomTapRegion(2, (hintZone.posCorner[0], hintZone.posCorner[1] + conf.LAYTON_SCREEN_HEIGHT),
                                                      hintZone.sizeBounding, "hintcoin"))
            self.eventHintId.append(hintIndex)
        
        for tObj in placeData.tObj:
            self.eventTap.append(LaytonRoomTapRegion(tObj.idChar, (tObj.bounding.posCorner[0], tObj.bounding.posCorner[1] + conf.LAYTON_SCREEN_HEIGHT),
                                                        tObj.bounding.sizeBounding, tObj.idTObj))
            self.drawnTobj.append(tObj.bounding.posCorner)
    
    def draw(self, gameDisplay):
        for sprite in self.animObjects:
            sprite.draw(gameDisplay)
        for sprite in self.eventObjects:
            sprite.draw(gameDisplay)
        if self.animTapDraw:
            LaytonRoomGraphics.animTap.draw(gameDisplay)
        
        if self.isHintCoinLocked:
            LaytonRoomGraphics.HINT_FLIP_BS.draw(gameDisplay)

    def update(self, gameClockDelta):

        # TODO - Potential game-speed issues if framerate is running too slow, as tObj anim starts without considering leftover fader time

        for sprite in self.animObjects:
            sprite.update(gameClockDelta)
        for sprite in self.eventObjects:
            sprite.update(gameClockDelta)
        if self.animTapDraw:
            LaytonRoomGraphics.animTap.update(gameClockDelta)

        if self.isHintCoinLocked:
            LaytonRoomGraphics.HINT_FLIP_BS.update(gameClockDelta)
            self.hintAnimFader.update(gameClockDelta)

            LaytonRoomGraphics.HINT_FLIP_BS.pos = (self.hintCoinSpawnLoc[0],
                                                   round(self.hintCoinSpawnLoc[1] - (LaytonRoomGraphics.HINT_FLIP_DISTANCE * self.hintAnimFader.getStrength())))

            if not(LaytonRoomGraphics.HINT_FLIP_BS.getActiveState()) and not(self.hintAnimFader.isActive):
                self.screenNextObject = self.eventHint.pop(self.hintCoinLockedIndex).getContext(self.playerState)
                self.hintCoinLockedIndex = None
                self.hintCoinSpawnLoc = None
                self.isHintCoinLocked = False
    
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and not(self.isHintCoinLocked):
            self.animTapDraw = True

            for animObject in self.placeData.objEvent:
                if animObject.bounding.wasClicked((event.pos[0], event.pos[1] - conf.LAYTON_SCREEN_HEIGHT)):
                    boundingBoxCenterPos = (animObject.bounding.posCorner[0] + animObject.bounding.sizeBounding[0] // 2, animObject.bounding.posCorner[1] + animObject.bounding.sizeBounding[1] // 2)
                    self.screenNextObject = LaytonHelperEventHandlerSpawner(animObject.idEvent, boundingBoxCenterPos, self.playerState)
                    state.debugPrint("WarnGraphicsCommand: Spawned event handler for ID " + str(animObject.idEvent))
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
                    self.hintCoinLockedIndex = hintCoinIndex
                    self.hintCoinSpawnLoc = (self.eventHint[hintCoinIndex].pos[0] + (self.eventHint[hintCoinIndex].dimensions[0] - LaytonRoomGraphics.HINT_FLIP_BS.dimensions[0]) // 2,
                                             self.eventHint[hintCoinIndex].pos[1] + (self.eventHint[hintCoinIndex].dimensions[1] - LaytonRoomGraphics.HINT_FLIP_BS.dimensions[1]) // 2)

                    LaytonRoomGraphics.HINT_FLIP_BS.setAnimationFromName("gfx")
                    LaytonRoomGraphics.HINT_FLIP_BS.loopingDisable()
                    self.hintAnimFader = anim.AnimatedFader(LaytonRoomGraphics.HINT_FLIP_TIME, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=True)

                    self.isHintCoinLocked = True
                    self.animTapDraw = False
                    hintCoinIndex -= 1
                    return True
                if hintCoinIndex < 0:
                    break
                hintCoinIndex += 1

            if self.animTapDraw:
                LaytonRoomGraphics.animTap.pos = (event.pos[0] - (LaytonRoomGraphics.animTap.dimensions[0] // 2),
                                                  event.pos[1] - (LaytonRoomGraphics.animTap.dimensions[1] // 2))
                LaytonRoomGraphics.animTap.setAnimationFromName("New Animation")
        return False

class LaytonRoomHandler(state.LaytonSubscreen):

    def __init__(self, roomIndex, roomSubIndex, playerState):
        state.LaytonSubscreen.__init__(self)
        self.transitionsEnableIn = False
        self.transitionsEnableOut = False
        self.screenBlockInput = True

        placeDataIndex = (roomIndex // 40) + 1
        if placeDataIndex > 1:
            placeDataIndex = 2

        placeData    = asset_dat.LaytonPlaceData()
        placeData.load(FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "place/plc_data" + str(placeDataIndex) + ".plz",
                                                      "n_place" + str(roomIndex) + "_" + str(roomSubIndex) + ".dat"))

        self.addToStack(LaytonRoomBackground(placeData, roomIndex, playerState))
        self.addToStack(LaytonRoomGraphics(placeData, roomIndex, playerState))
        self.addToStack(LaytonRoomUi(playerState))

if __name__ == '__main__':
    playerState = state.LaytonPlayerState()
    playerState.remainingHintCoins = 10
    state.play(LaytonRoomHandler(48, 0, playerState), playerState) # 48 hidden puzzle