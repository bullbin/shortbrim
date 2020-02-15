import pygame, han_nazo, conf, state, script, anim, const, scr_mystery, han_room

from file import FileInterface, resolveEventIntegerAsString
from os import path
from hat_io import asset, asset_dat

pygame.init()

# TODO - For every handler, ensure that executeCommand returns False, as stack-like behaviour will be encouraged UNIVERSALLY

class LaytonCharacterController():

    SLOT_OFFSET = {0:0, 1:0,
                   2:0, 3:0,
                   4:52}
    SLOT_LEFT  = [0,3,4]
    SLOT_RIGHT = [2]

    def __init__(self, body, face):
        self.isShown = True
        self.isFaceShown = True
        self.slot = None

        self.animBody = body
        self.animFace = face
        self.animBody.setAnimationFromName("b1 normal")
        self.animFace.setAnimationFromName("normal")
        self.lastOffsetFace = (0,0) # Hack for when game uses spaces in anim names which shouldn't be there

        self.screenFader = anim.AnimatedFader(LaytonTextOverlay.DURATION_FADE, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False, activeState=False)
        self.surfaceChar = anim.AlphaSurface(0, dimensions=self.animBody.dimensions)
        self.fadeIn()

    @staticmethod
    def loadFromIndex(index):
        body = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "eventchr", "chr" + str(index))
        face = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "sub", "chr" + str(index) + "_face")
        return LaytonCharacterController(body, face)
    
    def isCharacterFacingLeft(self):
        if self.slot in LaytonCharacterController.SLOT_LEFT:
            return True
        return False
    
    def isCharacterFacingRight(self):
        if self.slot in LaytonCharacterController.SLOT_RIGHT:
            return True
        return False

    def update(self, gameClockDelta):
        self.screenFader.update(gameClockDelta)
        self.surfaceChar.setAlpha(round(self.screenFader.getStrength() * 255))
        self.animBody.update(gameClockDelta)
        self.animFace.update(gameClockDelta)
    
    def draw(self, gameDisplay):
        if self.isShown and self.animBody.getImage() != None and self.slot in LaytonCharacterController.SLOT_OFFSET:
            outSurface = self.animBody.getImage().copy()
            if self.isFaceShown:
                if self.animFace.getImage() != None and self.animBody.getAnimObject() != None:
                    self.lastOffsetFace = self.animBody.getAnimObject().offsetFace
                    outSurface.blit(self.animFace.getImage(), self.animBody.getAnimObject().offsetFace)
                elif self.animFace.getImage() != None:
                    outSurface.blit(self.animFace.getImage(), self.lastOffsetFace)
            
            self.surfaceChar.clear()

            if self.isCharacterFacingLeft():
                outSurface = pygame.transform.flip(outSurface, True, False)
                self.surfaceChar.surface.blit(outSurface, (0,0))
                self.surfaceChar.draw(gameDisplay, location=(LaytonCharacterController.SLOT_OFFSET[self.slot], gameDisplay.get_height() - outSurface.get_height()))
            else:
                self.surfaceChar.surface.blit(outSurface, (0,0))
                self.surfaceChar.draw(gameDisplay, location=(gameDisplay.get_width() - outSurface.get_width() - LaytonCharacterController.SLOT_OFFSET[self.slot], gameDisplay.get_height() - outSurface.get_height()))
        
    def fadeIn(self):
        self.screenFader = anim.AnimatedFader(200, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False)

class LaytonEventBackground(state.LaytonContext):

    def __init__(self, playerState):
        state.LaytonContext.__init__(self)
        self.screenBlockInput       = True

        self.backgroundTs = None
        self.backgroundBs = None
    
    def executeCommand(self, command):
        if command.opcode == b'\x22':       # Draw image, TS
            self.backgroundTs = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + command.operands[0])
        elif command.opcode == b'\x21':     # Draw image, BS
            self.backgroundBs = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + command.operands[0])
        elif command.opcode == b'\x37' and self.backgroundBs != None:
            tempSurface = pygame.Surface((self.backgroundBs.get_width(), self.backgroundBs.get_height()))
            # TODO - Assumes top screen and bottom screen are same height
            # TODO - Unks
            tempSurface.set_alpha(command.operands[3])
            self.backgroundBs.blit(tempSurface, (0,0))
        else:
            super().executeCommand(command)
        return True

    def draw(self, gameDisplay):
        if self.backgroundBs != None:
            gameDisplay.blit(self.backgroundBs, (0, conf.LAYTON_SCREEN_HEIGHT))
        if self.backgroundTs != None:
            gameDisplay.blit(self.backgroundTs, (0, 0))
        
class LaytonTextOverlay(state.LaytonContext):

    DURATION_FADE = 500
    BANK_IMAGE_WINDOW = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "event", "twindow")
    BANK_IMAGE_WINDOW.pos = ((conf.LAYTON_SCREEN_WIDTH - BANK_IMAGE_WINDOW.dimensions[0]) // 2,
                             (conf.LAYTON_SCREEN_HEIGHT * 2) - BANK_IMAGE_WINDOW.dimensions[1] + 3)
    BANK_IMAGE_ARROW = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "sub", "arrow")
    BANK_IMAGE_ARROW_POS = (80, BANK_IMAGE_WINDOW.pos[1] + 1)

    BANK_IMAGE_TAP = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI, "cursor_wait")
    BANK_IMAGE_TAP_POS = (BANK_IMAGE_WINDOW.pos[0] + BANK_IMAGE_WINDOW.dimensions[0] - 16, BANK_IMAGE_WINDOW.pos[1] + BANK_IMAGE_WINDOW.dimensions[1] - 20)
    ALPHA_SURF_IMAGE_TAP = anim.AlphaSurface(255, dimensions=BANK_IMAGE_TAP.dimensions)
    BANK_IMAGE_TAP_FADE_DURATION = 500

    def __init__(self, talkScript, voiceLine, characterControllerIndices, characterControllers, playerState, animFunctionController=None):
        state.LaytonContext.__init__(self)
        self.screenIsOverlay = True

        self.screenOutSurface = anim.AlphaSurface(0)
        self.screenOutSurface.surface.fill((0,0,0,0))
        self.screenFader = anim.AnimatedFader(LaytonTextOverlay.DURATION_FADE, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False)
        self.tapFader = anim.AnimatedFader(LaytonTextOverlay.BANK_IMAGE_TAP_FADE_DURATION, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False, activeState=False)

        LaytonTextOverlay.BANK_IMAGE_WINDOW.setAnimationFromName("gfx")
        LaytonTextOverlay.BANK_IMAGE_WINDOW.setInitialFrameFromAnimation()

        talkScript = script.gdScript.fromData(talkScript)
        self.textTalk = anim.NuvoTextScroller(playerState.getFont("fontevent"), talkScript.commands[0].operands[3], textPosOffset=(10, 140 + conf.LAYTON_SCREEN_HEIGHT), targetFramerate=60, functionProcessor=animFunctionController)

        self.nameIsDrawn = False
        self.arrowIsDrawn = False
        self.tapIsDrawn = False
        self.targetAnimBody = None
        self.targetAnimFace = None
        self.animNameStart = "b1 normal"
        self.animNameEnd = "b1 normal"
        if len(talkScript.commands) > 0 and len(talkScript.commands[0].operands) == 4:
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
                    self.targetAnimBody = self.targetController.animBody
                    self.targetAnimFace = self.targetController.animFace

                    if talkScript.commands[0].operands[0] != "NONE":
                        self.animNameStart = talkScript.commands[0].operands[0]
                    else:
                        if self.targetAnimBody.getAnim() != None:
                            self.animNameStart = self.targetAnimBody.getAnim()
                    
                    if talkScript.commands[0].operands[1] != "NONE":
                        self.animNameEnd = talkScript.commands[0].operands[1]
                    elif talkScript.commands[0].operands[0] != "NONE":
                        self.animNameEnd = self.animNameStart
                    else:
                        self.animNameEnd = "b1 normal"

                    if self.isFormattedAsMultipartBody("*" + self.animNameStart):
                        self.setAnimPair("*" + self.animNameStart)
                    else:
                        self.setAnimPair(self.animNameStart)

                    if self.targetController.isShown and self.targetController.isCharacterFacingLeft():
                        LaytonTextOverlay.BANK_IMAGE_ARROW.setAnimationFromName("L")
                        LaytonTextOverlay.BANK_IMAGE_ARROW.pos = LaytonTextOverlay.BANK_IMAGE_ARROW_POS
                        LaytonTextOverlay.BANK_IMAGE_ARROW.setInitialFrameFromAnimation()
                    elif self.targetController.isShown and self.targetController.isCharacterFacingRight():
                        LaytonTextOverlay.BANK_IMAGE_ARROW.setAnimationFromName("R")
                        LaytonTextOverlay.BANK_IMAGE_ARROW.pos = (conf.LAYTON_SCREEN_WIDTH - LaytonTextOverlay.BANK_IMAGE_ARROW_POS[0] - LaytonTextOverlay.BANK_IMAGE_ARROW.dimensions[0],
                                                                LaytonTextOverlay.BANK_IMAGE_ARROW_POS[1])
                        LaytonTextOverlay.BANK_IMAGE_ARROW.setInitialFrameFromAnimation()
                    else:
                        self.arrowIsDrawn = False

    def isFormattedAsMultipartBody(self, animName):
        if animName[0] == "*":
            animName = animName[1:]
        animName = animName.split(" ")
        if len(animName) > 1 and animName[0][0] == "b":
            return True
        return False

    def faceAnimFromBodyAnim(self, animName):
        # Returns tuple, with first name being the specialised face anim name (if the body animation had an index),
        # and second without. If the first one is unavailable, use the general version
        tempAnimName = animName.split(" ")
        animNameIndex = tempAnimName[0].split("*")[-1][1:]
        if self.isFormattedAsMultipartBody(animName):
            if animName[0] == "*":
                return (True, "*" + tempAnimName[-1] + animNameIndex, "*" + tempAnimName[-1])
            return (True, tempAnimName[-1] + animNameIndex, tempAnimName[-1])
        else:
            return (False, None, None)

    def setAnimPair(self, animName):
        if self.targetAnimBody != None:
            if not(self.targetAnimBody.setAnimationFromName(animName)):
                self.targetAnimBody.setAnimationFromName(animName + " ")

        if self.targetAnimFace != None:
            drawFace, tempAnimNameSpecialised, tempAnimNameGeneral = self.faceAnimFromBodyAnim(animName)
            self.targetController.isFaceShown = drawFace
            if drawFace:
                faceAnims = [tempAnimNameSpecialised, tempAnimNameSpecialised + " ",
                            tempAnimNameGeneral, tempAnimNameGeneral + " "]

                for animName in faceAnims:
                    if self.targetAnimFace.setAnimationFromName(animName):
                        break

    def setNewAnim(self, animName):
        self.animNameStart = animName
        self.animNameEnd = animName
        if self.tapIsDrawn:
            self.setAnimPair(self.animNameStart)
        else:
            self.setAnimPair("*" + self.animNameStart)

    def triggerWait(self):
        self.tapIsDrawn = True
        self.tapFader = anim.AnimatedFader(LaytonTextOverlay.BANK_IMAGE_TAP_FADE_DURATION, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False)

        if self.textTalk.drawIncomplete:
            self.setAnimPair(self.animNameStart)
        else:
            self.setAnimPair(self.animNameEnd)
            
        LaytonTextOverlay.BANK_IMAGE_TAP.setAnimationFromName("touch")
        LaytonTextOverlay.ALPHA_SURF_IMAGE_TAP.setAlpha(0)

    def triggerUnwait(self):
        self.textTalk.isWaitingForTap = False
        self.tapIsDrawn = False
        if self.targetAnimFace != None:
            self.setAnimPair("*" + self.animNameStart)

    def update(self, gameClockDelta):
        if not(self.screenFader.isActive):
            self.textTalk.update(gameClockDelta)
            LaytonTextOverlay.BANK_IMAGE_WINDOW.update(gameClockDelta)
            LaytonTextOverlay.BANK_IMAGE_ARROW.update(gameClockDelta)
            LaytonTextOverlay.BANK_IMAGE_TAP.update(gameClockDelta)

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
    
    def draw(self, gameDisplay):
        LaytonTextOverlay.BANK_IMAGE_WINDOW.draw(self.screenOutSurface.surface)
        if self.arrowIsDrawn:
            LaytonTextOverlay.BANK_IMAGE_ARROW.draw(self.screenOutSurface.surface)
        if self.nameIsDrawn:
            self.imageName.draw(self.screenOutSurface.surface)
        
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
        self.dataEvent = asset_dat.LaytonEventData()
        if FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "event/ev_d" + extendedEventIndex + ".plz",
                                       "d" + indexEvent + "_" + indexEventSub + ".dat", version = 1) != None:
            self.dataEvent.load(FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "event/ev_d" + extendedEventIndex + ".plz",
                                                            "d" + indexEvent + "_" + indexEventSub + ".dat", version = 1))

        tempBgSurface = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "event/" + conf.LAYTON_ASSET_LANG + "/sub" + str(self.dataEvent.mapTsId))
        if tempBgSurface.get_width() == 0:
            tempBgSurface = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "event/sub" + str(self.dataEvent.mapTsId))
        self.commandFocus.backgroundTs = tempBgSurface

        self.commandFocus.backgroundBs = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "map/main" + str(self.dataEvent.mapBsId))
        self.imagesCharacter = []
        self.pointerImagesCharacter = {}

        # if self.dataEvent.faderTsActive:
        #     self.faderSceneSurfaceTop.startFadeIn()
        # else:
        #     self.faderSceneSurfaceTop.startFadeOut()
        # 
        # if self.dataEvent.faderBsActive:
        #     self.faderSceneSurfaceBottom.startFadeIn()
        # else:
        #     self.faderSceneSurfaceBottom.startFadeOut()

        for indexNewChar, charIndex in enumerate(self.dataEvent.characters):
            self.pointerImagesCharacter[charIndex] = len(self.imagesCharacter)
            self.imagesCharacter.append(LaytonCharacterController.loadFromIndex(charIndex))
            # print(charIndex, self.dataEvent.charactersShown[indexNewChar])
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
        state.debugPrint("WarnEventHandler: Unimplemented function", functionName)
        if function[0] == "setani":
            if function[1].isdigit() and int(function[1]) < len(self.imagesCharacter):
                pass
        
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
                self.screenNextObject = LaytonTextOverlay(tempScriptFile, self.cacheVoiceline, self.pointerImagesCharacter,
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

            isShown = command.operands[1] >= 0

            if command.operands[0] < len(self.imagesCharacter):
                self.imagesCharacter[command.operands[0]].isShown = isShown
            else:
                state.debugPrint("ErrEventHandler: Cannot change visibility properties on character", command.operands[0])
        
        elif command.opcode == b'\x30': # Rearrange characters
            if command.operands[0] < len(self.imagesCharacter):
                self.imagesCharacter[command.operands[0]].slot = command.operands[1]
            else:
                state.debugPrint("ErrEventHandler: Cannot change slot on character", command.operands[0])

        elif command.opcode == b'\x21' or command.opcode == b'\x22': # Background-related
            self.stack[0].executeCommand(command)

        # Is 31,32 outin waiting or fading?

        # TODO - On every fade operation, the dialogue box fades as well, and fades first
        # It may be best to just unify this all under one big handler :(

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
            self.stack[0].executeCommand(command)

        elif command.opcode == b'\x3f': # Set active body frame?
            if command.operands[0]  - 1 in self.pointerImagesCharacter:
                self.imagesCharacter[self.pointerImagesCharacter[command.operands[0] - 1]].animBody.setAnimationFromName(command.operands[1])
            else:
                state.debugPrint("ErrEventHandler: Character", command.operands[0], "doesn't exist to bind animation '" + command.operands[1] + "' to!")

        elif command.opcode == b'\x6a': # Screen shake
            pass

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
        
        elif command.opcode == b'\x80': # Screen 0,1 Timed fade in
            self.faderSceneSurfaceTop.startFadeIn(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)
            self.faderSceneSurfaceBottom.startFadeIn(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)
        
        # 84 - Unlock photo piece? 15230

        elif command.opcode == b'\x87': # Screen0 Timed fade out
            self.faderSceneSurfaceTop.startFadeOut(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)
        elif command.opcode == b'\x88': # Screen0 Timed fade in
            self.faderSceneSurfaceTop.startFadeIn(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)

        # CURSED AUDIO CORNER
        # Sampled channel
        elif command.opcode == b'\x5c': # Play voiceline
            self.cacheVoiceline = None
        elif command.opcode == b'\x5d': # Play sound effect (ST_<n>)
            pass
        elif command.opcode == b'\x5e': # Play sampled effect
            pass
        elif command.opcode == b'\x99': # Play sampled music
            pass

        # Synth channel
        elif command.opcode == b'\x62': # Play synthesized music
            pass

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
    # 10080, 15200, 13120, 13150, 13180, 12110, 12220, 12290, 14230, 14480, 14490, 15250, 15390

    # Working correctly
    # 10060, 11100, 14010, 16070, 17150, 17160, 16010, 11170, 17050, 13190, 12310, 11300

    # Almost working correctly
    # 17240, 17080, 13140, 11200, 11280, 30020, 14110, 14180, 15020

    # Missing features required to run correctly
    # 17140, 18440, 12190, 12240, 12270, 19070, 15260

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

    tempDebugExitLayer.addToStack(LaytonEventHandler(16010, playerState))
    state.play(tempDebugExitLayer, playerState)