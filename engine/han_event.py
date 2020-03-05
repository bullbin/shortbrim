import pygame, re
from os import path

# Bundled modules
import han_nazo, conf, state, script, anim, const, scr_mystery, han_room
from file import FileInterface, resolveEventIntegerAsString
from hat_io import asset, asset_dat
from random import randint

pygame.init()

# TODO - For every handler, ensure that executeCommand returns False, as stack-like behaviour will be encouraged UNIVERSALLY

# Item window
# Bank data_lt2/ani/menu/bag/item_icon.arc

class LaytonEventPopup(state.LaytonContext):

    DURATION_FADE = 500
    BANK_IMAGE_WINDOW = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "system", "prize_window2")
    BANK_IMAGE_WINDOW_POS = ((conf.LAYTON_SCREEN_WIDTH - BANK_IMAGE_WINDOW.dimensions[0]) // 2,
                             ((conf.LAYTON_SCREEN_HEIGHT - BANK_IMAGE_WINDOW.dimensions[1]) // 2) + conf.LAYTON_SCREEN_HEIGHT)

    BANK_IMAGE_TAP = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI, "cursor_wait")
    BANK_IMAGE_TAP_POS = (BANK_IMAGE_WINDOW.dimensions[0] - 16, BANK_IMAGE_WINDOW.dimensions[1] - 18)
    ALPHA_SURF_IMAGE_TAP = anim.AlphaSurface(255, dimensions=BANK_IMAGE_WINDOW.dimensions)
    BANK_IMAGE_TAP_FADE_DURATION = 500

    def __init__(self, textPopup, playerState):
        state.LaytonContext.__init__(self)
        self.screenIsOverlay = True
        self.screenOutSurface = anim.AlphaSurface(0)
        self.screenOutSurface.surface.fill((0,0,0,0))
        self.screenFader = anim.AnimatedFader(LaytonEventPopup.DURATION_FADE, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False)
        self.tapFader = anim.AnimatedFader(LaytonEventPopup.BANK_IMAGE_TAP_FADE_DURATION, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False, activeState=False)

        LaytonEventPopup.BANK_IMAGE_WINDOW.setAnimationFromName("gfx")
        LaytonEventPopup.BANK_IMAGE_WINDOW.setInitialFrameFromAnimation()
        LaytonEventPopup.BANK_IMAGE_TAP.setAnimationFromName("touch")

        self.textScroller = anim.NuvoTextScroller(playerState.getFont("fontevent"), textPopup, textPosOffset=(0, 0), targetFramerate=60)
        self.textScroller.skip()

    def drawItem(self, surface):
        pass

    def draw(self, gameDisplay):
        LaytonEventPopup.BANK_IMAGE_WINDOW.draw(self.screenOutSurface.surface)
        self.textScroller.draw(self.screenOutSurface.surface)
        self.drawItem(self.screenOutSurface.surface)
        LaytonEventPopup.ALPHA_SURF_IMAGE_TAP.clear()
        LaytonEventPopup.BANK_IMAGE_TAP.draw(LaytonEventPopup.ALPHA_SURF_IMAGE_TAP.surface)
        LaytonEventPopup.ALPHA_SURF_IMAGE_TAP.draw(self.screenOutSurface.surface, LaytonEventPopup.BANK_IMAGE_TAP_POS)

        self.screenOutSurface.draw(gameDisplay, location=LaytonEventPopup.BANK_IMAGE_WINDOW_POS)
    
    def update(self, gameClockDelta):
        if not(self.screenFader.isActive):
            LaytonEventPopup.BANK_IMAGE_WINDOW.update(gameClockDelta)
            LaytonEventPopup.BANK_IMAGE_TAP.update(gameClockDelta)
            LaytonTextOverlay.ALPHA_SURF_IMAGE_TAP.setAlpha(round(self.tapFader.getStrength() * 255))
            self.tapFader.update(gameClockDelta)
        else:
            self.screenFader.update(gameClockDelta)

        if self.screenFader.initialInverted and not(self.screenFader.isActive): # Kill if fade out is finished
            self.killWindow()
        else:
            self.screenOutSurface.setAlpha(round(self.screenFader.getStrength() * 255))
    
    def handleEvent(self, event):
        if not(self.screenFader.initialInverted) and not(self.screenFader.isActive):
            if event.type == pygame.MOUSEBUTTONUP:
                if self.screenFader.isActive:
                    self.screenFader.isActive = False
                else:
                    self.screenFader = anim.AnimatedFader(LaytonEventPopup.DURATION_FADE, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False, inverted=True)
                return True
        return False
    
    def killWindow(self):
        self.isContextFinished = True
        pygame.event.post(pygame.event.Event(const.ENGINE_RESUME_EXECUTION_STACK, {const.PARAM:None}))

class LaytonItemPopup(LaytonEventPopup):

    BANK_ITEM_IMAGE = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "menu/bag", "item_icon")
    POS_ITEM_IMAGE_Y = 6

    def __init__(self, indexItem, playerState):
        textItem = FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "txt/" + conf.LAYTON_ASSET_LANG + "/txt.plz", "item_" + str(indexItem) + ".txt", version=1)
        textPopup = FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "txt/" + conf.LAYTON_ASSET_LANG + "/txt2.plz", "tx_205.txt", version=1)

        self.imageItem = None

        if textItem != None and textPopup != None:
            textPopup = textPopup.decode('ascii')
            textItem = textItem.decode('ascii')
            textPopup = textPopup.replace(r"%s", textItem)

            tempImageItem = LaytonItemPopup.BANK_ITEM_IMAGE.setAnimationFromNameAndReturnInitialFrame(str(indexItem + 1))
            if tempImageItem != None:
                self.imageIcon = tempImageItem

            LaytonEventPopup.__init__(self, textPopup, playerState)
            self.textScroller.pos = (10, (LaytonItemPopup.POS_ITEM_IMAGE_Y * 2) + self.imageIcon.get_height())

        else:
            LaytonEventPopup.__init__(self, "", playerState)
            self.killWindow()
    
    def drawItem(self, surface):
        if self.imageIcon != None:
            surface.blit(self.imageIcon, ((surface.get_width() - self.imageIcon.get_width()) // 2, LaytonItemPopup.POS_ITEM_IMAGE_Y))

class LaytonPhotoPopup(LaytonEventPopup):
    def __init__(self, playerState):
        if len(playerState.indicesPhotosCollected) >= 10:
            textPopup = FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "txt/" + conf.LAYTON_ASSET_LANG + "/txt2.plz", "tx_222.txt", version=1)
        else:
            textPopup = FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "txt/" + conf.LAYTON_ASSET_LANG + "/txt2.plz", "tx_212.txt", version=1)
        if textPopup != None:
            textPopup = textPopup.decode('ascii')
            textPopup = textPopup.replace(r"%d", str(10 - len(playerState.indicesPhotosCollected)))
            LaytonEventPopup.__init__(self, textPopup, playerState)
        else:
            LaytonEventPopup.__init__(self, "", playerState)
            self.killWindow()

class LaytonCharacterController():

    SLOT_MAX = 6
    SLOT_OFFSET = {0:0,     1:0,
                   2:0,     3:0,
                   4:52,    5:52,
                   6:0}
    SLOT_LEFT  = [0,3,4]
    SLOT_RIGHT = [2,5,6]

    def __init__(self, body, face, indexSpawnAnim=None, debugIndex=0):
        self.isShown = True
        self.isFaceShown = False
        self.slot = None

        self.debugIndex = debugIndex
        self.animBody = body
        self.animFace = face

        self.animCurrent = None
        self.talkAnimModifierActive = False

        self.offset = (0,0)

        if body != None:
            tempAnimNames = list(body.animMap.keys())
            if indexSpawnAnim != None and indexSpawnAnim < len(tempAnimNames):
                self.setCurrentAnim(tempAnimNames[indexSpawnAnim])
            for var in body.variables:
                if var.name == "drawoff":
                    # TODO - Why is the first part of the drawoffset wrong?
                    self.offset = (round(var.data[0] * 3/5), var.data[1])
                    break

    @staticmethod
    def loadFromIndex(index, spawnAnimIndex=1, indexChar=1):
        body = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "eventchr", "chr" + str(index))
        face = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "sub", "chr" + str(index) + "_face")
        tempController = LaytonCharacterController(body, face, debugIndex=indexChar, indexSpawnAnim=spawnAnimIndex)

        return tempController
    
    def isCharacterPointingRight(self):
        if self.slot in LaytonCharacterController.SLOT_LEFT:
            return True
        return False
    
    def isCharacterPointingLeft(self):
        if self.slot in LaytonCharacterController.SLOT_RIGHT:
            return True
        return False

    def update(self, gameClockDelta):
        self.animBody.update(gameClockDelta)
        self.animFace.update(gameClockDelta)
    
    def draw(self, gameDisplay):

        def drawPointingRight(charSurface, x):
            outSurface = pygame.transform.flip(charSurface, True, False)
            gameDisplay.blit(outSurface, (x, gameDisplay.get_height() - outSurface.get_height() + self.offset[1]))
        
        def drawPointingLeft(charSurface, x):
            gameDisplay.blit(charSurface, (x, gameDisplay.get_height() - outSurface.get_height() + self.offset[1]))

        if self.isShown and self.animBody.getImage() != None:
            outSurface = self.animBody.getImage().copy()
            if self.isFaceShown:
                if self.animFace.getImage() != None and self.animBody.getAnimObject() != None:
                    outSurface.blit(self.animFace.getImage(), self.animBody.getAnimObject().offsetFace)

            if self.slot > LaytonCharacterController.SLOT_MAX:
                drawPointingLeft(outSurface, self.offset[0])
            elif self.slot not in LaytonCharacterController.SLOT_OFFSET: # Central
                drawPointingLeft(outSurface, (conf.LAYTON_SCREEN_WIDTH - (outSurface.get_width() + self.offset[0])) // 2)
            else:
                if self.isCharacterPointingRight():
                    drawPointingRight(outSurface, (LaytonCharacterController.SLOT_OFFSET[self.slot] - self.offset[0]))
                else:
                    drawPointingLeft(outSurface, gameDisplay.get_width() - outSurface.get_width() - LaytonCharacterController.SLOT_OFFSET[self.slot] - self.offset[0])
    
    def setTalkAnimState(self, newState):
        self.talkAnimModifierActive = newState
        self.updateCurrentAnim()

    def setCurrentAnim(self, animName):
        tempAnimName = animName

        # TODO - Validate strings sent by commands
        # TODO - Change this to validate immediately

        if self.animBody != None:
            
            if self.talkAnimModifierActive:
                talkAnimName = "*" + animName
                if talkAnimName in self.animBody.animMap:
                    animName = talkAnimName

            if animName in self.animBody.animMap:
                if self.animBody.animActive != animName:
                    self.animBody.setAnimationFromName(animName)
                    if self.animFace != None:
                        self.animFace.setAnimationFromIndex(self.animBody.getAnimObject().indexAnimFace)
                        if self.animBody.getAnimObject().indexAnimFace == 0:
                            self.isFaceShown = False
                        else:
                            self.isFaceShown = True
                self.animCurrent = tempAnimName
        
    def updateCurrentAnim(self):
        self.setCurrentAnim(self.animCurrent)

class LaytonEventBackground(state.LaytonContext):

    SHAKE_MAX_DELTA = 3

    def __init__(self, playerState):
        state.LaytonContext.__init__(self)
        self.screenBlockInput       = True

        self.backgroundTs = None
        self.backgroundBs = None

        self.bsShakeFader = anim.AnimatedFader(0, anim.AnimatedFader.MODE_TRIANGLE, False, cycle=False, inverted=False, activeState=False)
        self.tsShakeFader = anim.AnimatedFader(0, anim.AnimatedFader.MODE_TRIANGLE, False, cycle=False, inverted=False, activeState=False)
    
    @staticmethod
    def getBackgroundImageAndReturnIfValid(bgPath):
        tempSurface = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + bgPath)
        if tempSurface.get_width() == 0:
            return None
        return tempSurface

    def setBackgroundBottomScreen(self, bgPath):
        self.backgroundBs = LaytonEventBackground.getBackgroundImageAndReturnIfValid(bgPath)

        # TODO - Event 11360 -> 11370
        # When dimming is called twice, the image is double darkened because it was overwritten
    
    def setBackgroundTopScreen(self, bgPath):
        self.backgroundTs = LaytonEventBackground.getBackgroundImageAndReturnIfValid(bgPath)
    
    def setBottomScreenDimmingFactor(self, factor):
        if self.backgroundBs != None:
            tempSurface = pygame.Surface((self.backgroundBs.get_width(), self.backgroundBs.get_height()))
            tempSurface.set_alpha(factor)
            self.backgroundBs.blit(tempSurface, (0,0))

    def setTopScreenShake(self, duration):
        self.tsShakeFader = anim.AnimatedFader(duration, anim.AnimatedFader.MODE_TRIANGLE, False, cycle=False, inverted=False)

    def setBottomScreenShake(self, duration):
        self.bsShakeFader = anim.AnimatedFader(duration, anim.AnimatedFader.MODE_TRIANGLE, False, cycle=False, inverted=False)

    def update(self, gameClockDelta):
        self.bsShakeFader.update(gameClockDelta)
        self.tsShakeFader.update(gameClockDelta)

    def draw(self, gameDisplay):
        if self.backgroundBs != None:
            if self.bsShakeFader.isActive:
                outputImage = pygame.Surface((conf.LAYTON_SCREEN_WIDTH, conf.LAYTON_SCREEN_HEIGHT))
                outputImage.blit(self.backgroundBs, (randint(-LaytonEventBackground.SHAKE_MAX_DELTA, LaytonEventBackground.SHAKE_MAX_DELTA),
                                                     randint(-LaytonEventBackground.SHAKE_MAX_DELTA, LaytonEventBackground.SHAKE_MAX_DELTA)))
                gameDisplay.blit(outputImage, (0, conf.LAYTON_SCREEN_HEIGHT))
            else:
                gameDisplay.blit(self.backgroundBs, (0, conf.LAYTON_SCREEN_HEIGHT))
        if self.backgroundTs != None:
            if self.tsShakeFader.isActive:
                outputImage = pygame.Surface((conf.LAYTON_SCREEN_WIDTH, conf.LAYTON_SCREEN_HEIGHT))
                outputImage.blit(self.backgroundTs, (randint(-LaytonEventBackground.SHAKE_MAX_DELTA, LaytonEventBackground.SHAKE_MAX_DELTA),
                                                     randint(-LaytonEventBackground.SHAKE_MAX_DELTA, LaytonEventBackground.SHAKE_MAX_DELTA)))
                gameDisplay.blit(outputImage, (0,0))
            else:
                gameDisplay.blit(self.backgroundTs, (0, 0))

class LaytonTextOverlay(state.LaytonContext):

    DURATION_FADE = 500

    BANK_IMAGE_GOAL = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "event", "mokuteki_w")
    BANK_IMAGE_GOAL.pos = (0, (conf.LAYTON_SCREEN_HEIGHT * 2) - BANK_IMAGE_GOAL.dimensions[1])

    BANK_IMAGE_WINDOW = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "event", "twindow")
    BANK_IMAGE_WINDOW.pos = ((conf.LAYTON_SCREEN_WIDTH - BANK_IMAGE_WINDOW.dimensions[0]) // 2,
                             (conf.LAYTON_SCREEN_HEIGHT * 2) - BANK_IMAGE_WINDOW.dimensions[1] + 3)

    BANK_IMAGE_TAP = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI, "cursor_wait")
    BANK_IMAGE_TAP_POS = (BANK_IMAGE_WINDOW.pos[0] + BANK_IMAGE_WINDOW.dimensions[0] - 16, BANK_IMAGE_WINDOW.pos[1] + BANK_IMAGE_WINDOW.dimensions[1] - 20)

    ALPHA_SURF_IMAGE_TAP = anim.AlphaSurface(255, dimensions=BANK_IMAGE_TAP.dimensions)
    BANK_IMAGE_TAP_FADE_DURATION = 500

    TYPE_GOAL = 0
    TYPE_TEXT = 1

    def __init__(self, text, playerState, windowType = TYPE_TEXT, animFunctionController=None):
        state.LaytonContext.__init__(self)
        self.screenIsOverlay = True

        self.screenOutSurface = anim.AlphaSurface(0)
        self.screenOutSurface.surface.fill((0,0,0,0))
        self.screenFader = anim.AnimatedFader(LaytonTextOverlay.DURATION_FADE, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False)
        self.tapFader = anim.AnimatedFader(LaytonTextOverlay.BANK_IMAGE_TAP_FADE_DURATION, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False, activeState=False)

        if windowType == LaytonTextOverlay.TYPE_GOAL:
            self.bankImageWindow = LaytonTextOverlay.BANK_IMAGE_GOAL
        else:
            self.bankImageWindow = LaytonTextOverlay.BANK_IMAGE_WINDOW
        
        self.bankImageWindow.setAnimationFromName("gfx")
        self.bankImageWindow.setInitialFrameFromAnimation()

        self.tapIsDrawn = False
        self.textTalk = anim.NuvoTextScroller(playerState.getFont("fontevent"), text, textPosOffset=(10, 140 + conf.LAYTON_SCREEN_HEIGHT), targetFramerate=60, functionProcessor=animFunctionController)

    def triggerWait(self):
        self.tapIsDrawn = True
        self.tapFader = anim.AnimatedFader(LaytonTextOverlay.BANK_IMAGE_TAP_FADE_DURATION, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False)
            
        LaytonTextOverlay.BANK_IMAGE_TAP.setAnimationFromName("touch")
        LaytonTextOverlay.ALPHA_SURF_IMAGE_TAP.setAlpha(0)

    def triggerUnwait(self):
        self.textTalk.isWaitingForTap = False
        self.tapIsDrawn = False

    def updateBankImages(self, gameClockDelta):
        self.bankImageWindow.update(gameClockDelta)
        LaytonTextOverlay.BANK_IMAGE_TAP.update(gameClockDelta)

    def update(self, gameClockDelta):
        if not(self.screenFader.isActive):
            self.textTalk.update(gameClockDelta)
            self.updateBankImages(gameClockDelta)

            if self.tapIsDrawn:
                self.tapFader.update(gameClockDelta)
                LaytonTextOverlay.ALPHA_SURF_IMAGE_TAP.setAlpha(round(self.tapFader.getStrength() * 255))
            elif self.textTalk.isWaitingForTap or not(self.textTalk.drawIncomplete):
                self.triggerWait()
        else:
            self.screenFader.update(gameClockDelta)

        if self.screenFader.initialInverted and not(self.screenFader.isActive): # Kill if fade out is finished
            self.killWindow()
        else:
            self.screenOutSurface.setAlpha(round(self.screenFader.getStrength() * 255))
    
    def drawTransparencySurface(self, surface):
        pass

    def draw(self, gameDisplay):
        self.bankImageWindow.draw(self.screenOutSurface.surface)
        self.drawTransparencySurface(self.screenOutSurface.surface)
        
        self.textTalk.draw(self.screenOutSurface.surface)
        if self.tapIsDrawn:
            LaytonTextOverlay.ALPHA_SURF_IMAGE_TAP.clear()
            LaytonTextOverlay.BANK_IMAGE_TAP.draw(LaytonTextOverlay.ALPHA_SURF_IMAGE_TAP.surface)
            LaytonTextOverlay.ALPHA_SURF_IMAGE_TAP.draw(self.screenOutSurface.surface, LaytonTextOverlay.BANK_IMAGE_TAP_POS)

        self.screenOutSurface.draw(gameDisplay)

    def handleEvent(self, event):
        if not(self.screenFader.initialInverted) and not(self.screenFader.isActive):
            if event.type == pygame.MOUSEBUTTONUP:
                if self.screenFader.isActive:
                    self.screenFader.isActive = False
                elif not(self.textTalk.drawIncomplete):
                    self.screenFader = anim.AnimatedFader(LaytonTextOverlay.DURATION_FADE, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False, inverted=True)
                elif self.textTalk.isWaitingForTap:
                    self.triggerUnwait()
                else:
                    self.textTalk.skip()
                return True
        return False

    def killWindow(self):
        self.isContextFinished = True
        pygame.event.post(pygame.event.Event(const.ENGINE_RESUME_EXECUTION_STACK, {const.PARAM:None}))

class LaytonCharTextOverlay(LaytonTextOverlay):

    BANK_IMAGE_ARROW = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "sub", "arrow")
    BANK_IMAGE_ARROW_POS = (80, LaytonTextOverlay.BANK_IMAGE_WINDOW.pos[1] + 1)

    def __init__(self, talkScript, voiceLine, characterControllerIndices, characterControllers, playerState, animFunctionController=None):
        
        def correctAnimName(animName):
            nameCorrection = ""
            for nameCorrectionSection in animName.split(" "):
                if len(nameCorrectionSection) > 0:
                    if len(nameCorrection) == 0:
                        nameCorrection = nameCorrectionSection
                    else:
                        nameCorrection = nameCorrection + " " + nameCorrectionSection
            if nameCorrection == "":
                return "NONE"
            else:
                return nameCorrection

        talkScript = script.gdScript.fromData(talkScript)

        self.nameIsDrawn = False
        self.arrowIsDrawn = False
        self.targetController = None

        self.enableAnimChangeEnd = False
        self.animNameEnd = ""

        if talkScript != None and len(talkScript.commands) > 0 and len(talkScript.commands[0].operands) == 4:
            LaytonTextOverlay.__init__(self, talkScript.commands[0].operands[3], playerState, animFunctionController=animFunctionController)
            # Command has been validated, start using the script
            self.indexCharacter = int.from_bytes(talkScript.commands[0].opcode, byteorder = 'little')
            if self.indexCharacter > 0:
                self.nameIsDrawn = True
                self.imageName = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "eventchr/" + conf.LAYTON_ASSET_LANG,
                                                    "chr" + str(self.indexCharacter) + "_n")
                self.imageName.pos = (2, LaytonTextOverlay.BANK_IMAGE_WINDOW.pos[1] + 12 - self.imageName.dimensions[1])
                self.imageName.setAnimationFromName("gfx")
                self.imageName.setInitialFrameFromAnimation()
                
                if self.indexCharacter in characterControllerIndices.keys():
                    self.arrowIsDrawn = True
                    self.targetController = characterControllers[characterControllerIndices[self.indexCharacter]]

                    self.targetController.setTalkAnimState(True)
                    animNameStart = correctAnimName(talkScript.commands[0].operands[0])
                    animNameEnd = correctAnimName(talkScript.commands[0].operands[1])
                    if animNameStart != "NONE":        # Anim name on start
                        self.targetController.setCurrentAnim(animNameStart)
                    
                    if animNameEnd != "NONE":
                        self.enableAnimChangeEnd = True
                        self.animNameEnd = animNameEnd

                    if self.targetController.isShown and self.targetController.isCharacterPointingRight():
                        LaytonCharTextOverlay.BANK_IMAGE_ARROW.setAnimationFromName("L")
                        LaytonCharTextOverlay.BANK_IMAGE_ARROW.pos = LaytonCharTextOverlay.BANK_IMAGE_ARROW_POS
                        LaytonCharTextOverlay.BANK_IMAGE_ARROW.setInitialFrameFromAnimation()
                    elif self.targetController.isShown and self.targetController.isCharacterPointingLeft():
                        LaytonCharTextOverlay.BANK_IMAGE_ARROW.setAnimationFromName("R")
                        LaytonCharTextOverlay.BANK_IMAGE_ARROW.pos = (conf.LAYTON_SCREEN_WIDTH - LaytonCharTextOverlay.BANK_IMAGE_ARROW_POS[0] - LaytonCharTextOverlay.BANK_IMAGE_ARROW.dimensions[0],
                                                                LaytonCharTextOverlay.BANK_IMAGE_ARROW_POS[1])
                        LaytonCharTextOverlay.BANK_IMAGE_ARROW.setInitialFrameFromAnimation()
                    else:
                        self.arrowIsDrawn = False
        else:
            # TODO - Match game behaviour where background image path is bled into here
            LaytonTextOverlay.__init__(self, "NONE", playerState, animFunctionController=animFunctionController)
            self.killWindow()

    def drawTransparencySurface(self, surface):
        if self.arrowIsDrawn:
            LaytonCharTextOverlay.BANK_IMAGE_ARROW.draw(surface)
        if self.nameIsDrawn:
            self.imageName.draw(surface)

    def triggerWait(self):
        super().triggerWait()
        if self.targetController != None:
            self.targetController.setTalkAnimState(False)
            if not(self.textTalk.drawIncomplete) and self.enableAnimChangeEnd:
                self.targetController.setCurrentAnim(self.animNameEnd)
    
    def triggerUnwait(self):
        super().triggerUnwait()
        if self.targetController != None:
            self.targetController.setTalkAnimState(True)
    
    def updateBankImages(self, gameClockDelta):
        super().updateBankImages(gameClockDelta)
        LaytonCharTextOverlay.BANK_IMAGE_ARROW.update(gameClockDelta)

class LaytonGoalTextOverlay(LaytonTextOverlay):
    def __init__(self, text, playerState, animFunctionController=None):
        LaytonTextOverlay.__init__(self, text, playerState, windowType = LaytonTextOverlay.TYPE_GOAL, animFunctionController=animFunctionController)
        self.textTalk.skip()
    
    def triggerUnwait(self):
        super().triggerUnwait()
        self.textTalk.skip()

class LaytonEventHandler(state.LaytonSubscreenWithFader):

    def __init__(self, eventIndex, playerState, globalTsFader=None, globalBsFader=None):
        state.LaytonSubscreenWithFader.__init__(self)
        self.playerState = playerState

        self.addToStack(LaytonEventBackground(self.playerState))
        self.commandFocus = self.stack[-1]

        self.isScriptAwaitingExecution = True
        self.indexScriptCommand = 0

        self.indexEvent, extendedEventIndex, self.indexEventSub = resolveEventIntegerAsString(eventIndex)

        self.scriptTalkBank = asset.LaytonPack(version=1)
        self.scriptTalkBank.load(FileInterface.getData(FileInterface.PATH_ASSET_ROOT + "event/" + conf.LAYTON_ASSET_LANG + "/ev_t" + extendedEventIndex + ".plz"))
        self.scriptEvent = script.gdScript.fromData(FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "event/ev_d" + extendedEventIndex + ".plz",
                                                                                "e" + self.indexEvent + "_" + self.indexEventSub + ".gds", version = 1))

        self.imagesCharacter = []
        self.pointerImagesCharacter = {}
        self.loadEventData(self.indexEvent, extendedEventIndex, self.indexEventSub)

        self.stackOverrideEvents = []

        self.cacheVoiceline = None
        
        self.scriptNextEvent = None
        self.scriptNextEventMode = None
        self.scriptNextTalkBank = None
        self.nextIndexEvent = None
        self.nextIndexEventSub = None

        self.isReadyToKill = False
    
    def loadEventData(self, indexEvent, extendedEventIndex, indexEventSub):

        self.faderSceneSurfaceTop.startFadeIn()
        self.faderSceneSurfaceBottom.startFadeIn()

        self.dataEvent = asset_dat.LaytonEventData()
        if FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "event/ev_d" + extendedEventIndex + ".plz",
                                       "d" + indexEvent + "_" + indexEventSub + ".dat", version = 1) != None:
            self.dataEvent.load(FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "event/ev_d" + extendedEventIndex + ".plz",
                                                            "d" + indexEvent + "_" + indexEventSub + ".dat", version = 1))
        
        # TODO - Check if eventID in goal_inf.dlz, and update goal accordingly

        self.commandFocus.setBackgroundTopScreen("event/" + conf.LAYTON_ASSET_LANG + "/sub" + str(self.dataEvent.mapTsId))
        if self.commandFocus.backgroundTs == None:
            self.commandFocus.setBackgroundTopScreen("event/sub" + str(self.dataEvent.mapTsId))
        self.commandFocus.setBackgroundBottomScreen("map/main" + str(self.dataEvent.mapBsId))
        self.commandFocus.setBottomScreenDimmingFactor(120)
        
        self.imagesCharacter = []
        self.pointerImagesCharacter = {}

        for indexNewChar, charIndex in enumerate(self.dataEvent.characters):
            self.pointerImagesCharacter[charIndex] = len(self.imagesCharacter)
            self.imagesCharacter.append(LaytonCharacterController.loadFromIndex(charIndex, spawnAnimIndex=self.dataEvent.charactersInitialAnimationIndex[indexNewChar], indexChar=charIndex))
            self.imagesCharacter[indexNewChar].isShown = self.dataEvent.charactersShown[indexNewChar]
            self.imagesCharacter[indexNewChar].slot = self.dataEvent.charactersPosition[indexNewChar]
                    
    def clearCharacterImages(self):
        for character in self.imagesCharacter:
            character.isShown = False
    
    def doOnUpdateCleared(self, gameClockDelta):

        # Convert to update function so can be made normal on stack again.

        if self.indexScriptCommand < len(self.scriptEvent.commands):
            if self.isScriptAwaitingExecution or len(self.stackOverrideEvents) > 0:
                while not (self.isUpdateBlocked()) and len(self.stackOverrideEvents) > 0:
                    self.addToStack(self.stackOverrideEvents.pop(0))
                while not(self.isUpdateBlocked()) and (self.isScriptAwaitingExecution and self.indexScriptCommand < len(self.scriptEvent.commands)):
                    self.isScriptAwaitingExecution = self.executeGdScriptCommand(self.scriptEvent.commands[self.indexScriptCommand])
                    self.indexScriptCommand += 1
                pygame.event.post(pygame.event.Event(const.ENGINE_SKIP_CLOCK, {const.PARAM:None}))
                    
        elif self.isScriptAwaitingExecution:    # Script ready to execute more code, so all tasks are finished and fading can happen
            if self.scriptNextEvent != None:
                if self.scriptNextEventMode != "drama event":
                    state.debugPrint("WarnEventHandler: Unknown extension", self.scriptNextEventMode)
                
                self.indexScriptCommand = 0
                self.scriptEvent = self.scriptNextEvent
                self.scriptTalkBank = self.scriptNextTalkBank
                self.indexEvent = self.nextIndexEvent
                self.indexEventSub = self.nextIndexEventSub

                _tempIndexEvent, extendedEventIndex, _tempIndexEventSub = resolveEventIntegerAsString(int((int(self.indexEvent) * 1000) + int(self.indexEventSub)))
                self.loadEventData(self.indexEvent, extendedEventIndex, self.indexEventSub)

                self.nextIndexEvent = None
                self.nextIndexEventSub = None
                self.scriptNextEventMode = None
                self.scriptNextTalkBank = None
                self.scriptNextEvent = None
            else:
                if self.isReadyToKill:
                    if self.scriptNextEventMode != None:
                        if self.scriptNextEventMode == "room":
                            self.screenNextObject = han_room.LaytonRoomHandler(self.playerState.currentRoom, 0, self.playerState)
                        else:
                            state.debugPrint("WarnEventHandler: Ignored extension", self.scriptNextEventMode)
                        self.scriptNextEventMode = None
                    state.debugPrint("LogEventHandler: Terminated execution!")
                    self.isContextFinished = True
                else:
                    self.isReadyToKill = True
                    if self.faderSceneSurfaceTop.fader.getStrength() ^ self.faderSceneSurfaceBottom.fader.getStrength():
                        if self.faderSceneSurfaceTop.fader.getStrength():
                            self.faderSceneSurfaceTop.startFadeOut()
                        else:
                            self.faderSceneSurfaceBottom.startFadeOut()
                    elif self.faderSceneSurfaceTop.fader.getStrength() != 1.0:
                        self.faderSceneSurfaceTop.startFadeOut()
                        self.faderSceneSurfaceBottom.startFadeOut()

    def updateSubscreenMethods(self, gameClockDelta):
        for image in self.imagesCharacter:
            image.update(gameClockDelta)
            
    def draw(self, gameDisplay):
        super().draw(gameDisplay)
        for character in self.imagesCharacter:
            character.draw(gameDisplay)
        self.drawFaders(gameDisplay)

    def processScrollerFunction(self, functionName):
        function = functionName.split(" ")
        if function[0] == "setani":
            if function[1].isdigit() and int(function[1]) in self.pointerImagesCharacter.keys():
                self.imagesCharacter[self.pointerImagesCharacter[int(function[1])]].setCurrentAnim(function[2].replace("_", " "))
            else:
                state.debugPrint("WarnEventHandler: setani command incorrectly formatted! Sent", functionName)
        else:
            state.debugPrint("WarnEventHandler: Unimplemented function", functionName)
        
    def executeGdScriptCommand(self, command):

        def fadeInBothScreens():
            self.faderSceneSurfaceTop.startFadeIn()
            self.faderSceneSurfaceBottom.startFadeIn()
        
        def fadeOutBothScreens():
            self.faderSceneSurfaceTop.startFadeOut()
            self.faderSceneSurfaceBottom.startFadeOut()

        def setNextEvent(eventInt):
            self.nextIndexEvent, extendedEventIndex, self.nextIndexEventSub = resolveEventIntegerAsString(eventInt)
            self.scriptNextEvent = script.gdScript.fromData(FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "event/ev_d" + extendedEventIndex + ".plz",
                                                                                        "e" + self.nextIndexEvent + "_" + self.nextIndexEventSub + ".gds", version = 1))
            self.scriptNextTalkBank = asset.LaytonPack(version=1)
            self.scriptNextTalkBank.load(FileInterface.getData(FileInterface.PATH_ASSET_ROOT + "event/" + conf.LAYTON_ASSET_LANG + "/ev_t" + self.nextIndexEvent + ".plz"))

        if command.opcode == b'\x02': # Screen0,1 Fade in
            fadeInBothScreens()
        elif command.opcode == b'\x03': # Screen0,1 Fade out
            fadeOutBothScreens()

        elif command.opcode == b'\x04': # Talk overlay
            tempScriptFile = self.scriptTalkBank.getFile("t" + self.indexEvent + "_" + self.indexEventSub + "_" + str(command.operands[0]) + ".gds")
            if tempScriptFile != None and len(tempScriptFile) > 0:
                self.screenNextObject = LaytonCharTextOverlay(tempScriptFile, self.cacheVoiceline, self.pointerImagesCharacter,
                                                              self.imagesCharacter, self.playerState, animFunctionController=self.processScrollerFunction)
                return False
            else:
                state.debugPrint("ErrEventHandler: Invalid talk script 't" + self.indexEvent + "_" + self.indexEventSub + "_" + str(command.operands[0]) + ".gds'")

        elif command.opcode == b'\x05': # Set current room
            state.debugPrint("DbgEventHandler: Set active room to", command.operands[0])
            self.playerState.currentRoom = command.operands[0]

        # 06, 07 something to do with next handler.
        elif command.opcode == b'\x06':
            self.scriptNextEventMode = command.operands[0]
        elif command.opcode == b'\x07':
            # Seems to be for handlers that execute immediately and hold up the stack (eg movies)
            pass

        elif command.opcode == b'\x08':
            state.debugPrint("DbgEventHandler: Set movie index to", command.operands[0])
        elif command.opcode == b'\x09': # Link next script
            state.debugPrint("DbgEventHandler: Continue execution on", command.operands[0])
            setNextEvent(command.operands[0])
            
        elif command.opcode == b'\x9c': # Link next script under condition
            metCondition = False
            if command.operands[0] == 0 and self.playerState.getPuzzleSolvedCount() >= command.operands[1]:    # Condition: Puzzles solved
                metCondition = True
            
            if metCondition:
                setNextEvent(command.operands[2])
                state.debugPrint("DbgEventHandler: Conditional link to", self.nextIndexEvent, self.nextIndexEventSub)
            else:
                state.debugPrint("ErrEventHandler: Didn't satisfy condition", command.operands[0], command.operands[1], "for script", command.operands[2])

        elif command.opcode == b'\x0b': # Start puzzle
            # TODO - Program fade out
            if int(self.indexEvent) > 19:
                state.debugPrint("LogEventHandler: Puzzle has available linking event.")
            self.addToStack(han_nazo.LaytonPuzzleHandler(command.operands[0], self.playerState))
            return False

        elif command.opcode == b'\x21':
            self.commandFocus.setBackgroundBottomScreen(command.operands[0])
        elif command.opcode == b'\x22':
            self.commandFocus.setBackgroundTopScreen(command.operands[0])

        elif command.opcode == b'\x2a': # Show cached character
            if command.operands[0] < len(self.imagesCharacter):
                self.imagesCharacter[command.operands[0]].isShown = True
            else:
                state.debugPrint("ErrEventHandler: Tried to show character index", command.operands[0], "when not loaded!")

        elif command.opcode == b'\x2b': # Hide cached character
            if command.operands[0] < len(self.imagesCharacter):
                self.imagesCharacter[command.operands[0]].isShown = False
            else:
                state.debugPrint("ErrEventHandler: Tried to hide character index", command.operands[0], "when not loaded!")

        elif command.opcode == b'\x2c': # ?? Change visibility
            if command.operands[1] in [-2,2]:
                isShown = command.operands[1] >= 0

                if command.operands[0] < len(self.imagesCharacter):
                    self.imagesCharacter[command.operands[0]].isShown = isShown
                else:
                    state.debugPrint("ErrEventHandler: Cannot change visibility properties on character", command.operands[0])
            else:
                state.debugPrint("ErrEventHandler: Unknown character visibility property", command.operands[1])
        
        # 2d - 13000?

        elif command.opcode == b'\x30': # Rearrange characters
            if command.operands[0] < len(self.imagesCharacter):
                self.imagesCharacter[command.operands[0]].slot = command.operands[1]
            else:
                state.debugPrint("ErrEventHandler: Cannot change slot on character", command.operands[0])

        # WAIT CORNER
        elif command.opcode == b'\x31':
            self.waitFader = anim.AnimatedFader(command.operands[0] * conf.ENGINE_FRAME_INTERVAL, anim.AnimatedFader.MODE_TRIANGLE, False, cycle=False)
        elif command.opcode == b'\x6c': # Wait for audio? Maybe write a list mechanism for evaluating waits instead.
            self.waitFader = anim.AnimatedFader(command.operands[0] * conf.ENGINE_FRAME_INTERVAL, anim.AnimatedFader.MODE_TRIANGLE, False, cycle=False)
            self.waitFaderUntriggerReason = const.EVENT_TRIGGER_END_OF_CLIP

        elif command.opcode == b'\x32': # Screen1 Fade in
            self.faderSceneSurfaceBottom.startFadeIn()
        elif command.opcode == b'\x33': # Screen1 Fade out
            self.faderSceneSurfaceBottom.startFadeOut()

        elif command.opcode == b'\x37': # Set darkness
            self.commandFocus.setBottomScreenDimmingFactor(command.operands[3])

        elif command.opcode == b'\x3f': # Set active body frame?
            if command.operands[0] in self.pointerImagesCharacter.keys():
                self.imagesCharacter[self.pointerImagesCharacter[command.operands[0]]].setCurrentAnim(command.operands[1])
            else:
                state.debugPrint("ErrEventHandler: Character", command.operands[0], "doesn't exist to bind animation '" + command.operands[1] + "' to!")

        elif command.opcode == b'\x6a': # Bottom screen shake
            self.commandFocus.setBottomScreenShake(command.operands[0] * conf.ENGINE_FRAME_INTERVAL)
        elif command.opcode == b'\x6b': # Top screen shake
            self.commandFocus.setTopScreenShake(command.operands[0] * conf.ENGINE_FRAME_INTERVAL)

        elif command.opcode == b'\x69': # Wait for tap
            self.triggerWaitUntilTap()

        elif command.opcode == b'\x70': # Unlock entry in Layton's diary
            state.debugPrint("LogEventHandler: Unlocked Layton's diary entry number", command.operands[0])

        elif command.opcode == b'\x71': # Add mystery, spawn mystery screen and hide all characters
            self.faderSceneSurfaceTop.startFadeOut()
            self.faderSceneSurfaceBottom.startFadeOut()

            def terminateGraphicsAndFadeIn():
                self.clearCharacterImages()
                self.faderSceneSurfaceBottom.startFadeIn()
            
            def invertQuitCall():
                return not(self.isUpdateBlocked())
            
            self.playerState.setStatusMystery(command.operands[0] - 1, state.LaytonPlayerState.MYSTERY_WAITING_LOCK)
            self.stackOverrideEvents.append(scr_mystery.Screen(self.playerState, fadeOutCall=fadeOutBothScreens, canQuitCall=invertQuitCall, tsFadeInCall=self.faderSceneSurfaceTop.startFadeIn, bsFadeInCall=terminateGraphicsAndFadeIn))
            return False
        
        elif command.opcode == b'\x73': # Unlock tea, 30020
            state.debugPrint("LogEventHandler: Unlock tea minigame", command.operands[0])

        elif command.opcode == b'\x7d': # Solve mystery, spawn mystery screen and hide all characters
            self.faderSceneSurfaceTop.startFadeOut()
            self.faderSceneSurfaceBottom.startFadeOut()

            def terminateGraphicsAndFadeIn():
                self.clearCharacterImages()
                self.faderSceneSurfaceBottom.startFadeIn()
            
            def invertQuitCall():
                return not(self.isUpdateBlocked())
            
            self.playerState.setStatusMystery(command.operands[0] - 1, state.LaytonPlayerState.MYSTERY_WAITING_UNLOCK)
            self.stackOverrideEvents.append(scr_mystery.Screen(self.playerState, fadeOutCall=fadeOutBothScreens, canQuitCall=invertQuitCall, tsFadeInCall=self.faderSceneSurfaceTop.startFadeIn, bsFadeInCall=terminateGraphicsAndFadeIn))
            return False
        
        elif command.opcode == b'\x72': # Screen 0,1 Timed fade out
            self.faderSceneSurfaceTop.startFadeOut(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)
            self.faderSceneSurfaceBottom.startFadeOut(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)
        
        elif command.opcode == b'\x77':
            # TODO - Add item to inventory
            self.screenNextObject = LaytonItemPopup(command.operands[0], self.playerState)
            return False

        elif command.opcode == b'\x7f': # Present in 18440, another bottom screen fade out?
            self.faderSceneSurfaceBottom.startFadeOut(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)

        elif command.opcode == b'\x80': # Screen 0,1 Timed fade in
            self.faderSceneSurfaceTop.startFadeIn(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)
            self.faderSceneSurfaceBottom.startFadeIn(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)

        elif command.opcode == b'\x81': # Present in 18440, another bottom screen fade in?
            self.faderSceneSurfaceBottom.startFadeIn(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)

        elif command.opcode == b'\x84':
            if command.operands[0] not in self.playerState.indicesPhotosCollected:
                self.playerState.indicesPhotosCollected.append(command.operands[0])
            self.screenNextObject = LaytonPhotoPopup(self.playerState)
            return False
        
        elif command.opcode == b'\x87': # Screen0 Timed fade out
            self.faderSceneSurfaceTop.startFadeOut(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)
        elif command.opcode == b'\x88': # Screen0 Timed fade in
            self.faderSceneSurfaceTop.startFadeIn(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)

        elif command.opcode == b'\x8a': # 14100
            state.debugPrint("LogEventAudio: Fade out, parameters", command.operands)
        elif command.opcode == b'\x8b':
            state.debugPrint("LogEventAudio: Fade in, parameters", command.operands)

        elif command.opcode == b'\x92': # Goal popup in golden text
            tempTextGoal = FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "txt/" + conf.LAYTON_ASSET_LANG + "/txt2.plz", "next_" + str(self.playerState.currentObjective) + ".txt")
            if tempTextGoal != None:
                self.screenNextObject = LaytonGoalTextOverlay(tempTextGoal.decode('ascii'), self.playerState, animFunctionController=self.processScrollerFunction)
                return False
            else:
                state.debugPrint("ErrEventHandler: Goal text", "next_" + str(self.playerState.currentObjective) + ".txt", "doesn't exist!")

        # CURSED AUDIO CORNER
        # Sampled channel
        elif command.opcode == b'\x5c': # Play voiceline
            self.cacheVoiceline = None
            state.debugPrint("LogEventAudio: Voiceline", command.operands[0])
        elif command.opcode == b'\x5d': # Play sound effect (ST_<n>)
            state.debugPrint("LogEventAudio: ST_" + ("%03d" % command.operands[0]))
        elif command.opcode == b'\x5e': # Play sampled effect
            if command.operands[0] < 100:
                formalString = str(command.operands[0]) + " from GE_999"
            else:
                formalString = str(command.operands[0])
            state.debugPrint("LogEventAudio: Sampled effect", formalString)

        # elif command.opcode == b'\x99': # Play sampled music - Contradicted by 16010, supported by 14100
        #     state.debugPrint("LogEventAudio: Sampled music", command.operands)

        # Synth channel
        elif command.opcode == b'\x62': # Play synthesized music
            state.debugPrint("LogEventAudio: Synthesized music BG_" + ("%03d" % command.operands[0]) + "\n\tVolume", str(command.operands[1]) + "\n\tUnk", command.operands[2])

        else:
            return self.commandFocus.executeCommand(command)
        return True
    
    def handleEvent(self, event):
        if event.type == const.ENGINE_RESUME_EXECUTION_STACK:
            self.isScriptAwaitingExecution = True
        elif event.type == const.EVENT_TRIGGER_END_OF_CLIP:
            if self.waitFader.isActive and self.waitFaderUntriggerReason == event.type:
                self.waitFader.isActive = False
                self.waitFaderUntriggerReason = None
                state.debugPrint("LogEventHandler: Wait cancelled early!")
        else:
            return super().handleEvent(event)

if __name__ == '__main__':
    playerState = state.LaytonPlayerState()
    playerState.remainingHintCoins = 10
    tempDebugExitLayer = state.LaytonSubscreenWithFader()
    
    # Working perfectly
    # 10080, 15200, 13120, 13150, 13180, 12110, 12220, 12290, 14230, 14480, 14490, 15250, 15390, 10035, 16070, 11100, 11300, 13140

    # Working correctly
    # 10060, 14010, 17150, 17160, 16010, 11170, 17050, 13190, 12310, 15020, 15260, 18440

    # Almost working correctly
    # 17240, 17080, 11200, 11280, 30020, 14110, 14180, 12190

    # Missing features required to run correctly
    # 17140, 12240, 12270, 19070

    # Understanding required to implement properly
    # 12280, 12281, 15160

    # e24
    # 0 - Initial puzzle event
    # 1 - Retry event
    # 2 - Click once solved event
    # 3 - Solved event
    # 4 - Quit event

    # e26 - Layton's Challenges

    # e30 - Tea
    # 0 - Initial tea event
    # 1 - Good tea
    # 2 - Bad tea
    # 3 - Quit
    # 4 - Retry

    # e18 - The Story so Far...
    # 14180, 10030 (end), 11100, 11300, 13140, 14110
    tempDebugExitLayer.addToStack(LaytonEventHandler(15020, playerState))
    state.play(tempDebugExitLayer, playerState)