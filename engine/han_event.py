import pygame, han_nazo, conf, state, script, anim, const, scr_mystery, han_room

from file import FileInterface, resolveEventIntegerAsString
from os import path
from hat_io import asset

pygame.init()

# TODO - For every handler, ensure that executeCommand returns False, as stack-like behaviour will be encouraged UNIVERSALLY

class LaytonCharacterController():
    def __init__(self, body, face):
        self.isFlipped = False
        self.isShown = True
        self.animBody = body
        self.animFace = face
        self.animBody.setAnimationFromName("b1 normal")
        self.animFace.setAnimationFromName("normal")
        self.lastOffsetFace = (0,0) # Hack for when game uses spaces in anim names which shouldn't be there

        self.screenFader = anim.AnimatedFader(LaytonTextOverlay.DURATION_FADE, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False, activeState=False)
        self.surfaceChar = anim.AlphaSurface(0, dimensions=self.animBody.dimensions)
    
    def setFlippedState(self, isFlipped):
        if self.isFlipped != isFlipped:
            self.fadeIn()
        elif not(self.screenFader.isActive) and self.surfaceChar.alpha != 255:
            self.fadeIn()
        self.isFlipped = isFlipped

    @staticmethod
    def loadFromIndex(index):
        body = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "eventchr", "chr" + str(index + 1))
        face = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "sub", "chr" + str(index + 1) + "_face")
        return LaytonCharacterController(body, face)
    
    def update(self, gameClockDelta):
        self.screenFader.update(gameClockDelta)
        self.surfaceChar.setAlpha(round(self.screenFader.getStrength() * 255))
        self.animBody.update(gameClockDelta)
        self.animFace.update(gameClockDelta)
    
    def draw(self, gameDisplay):
        if self.isShown and self.animBody.getImage() != None:
            outSurface = self.animBody.getImage().copy()
            if self.animFace.getImage() != None and self.animBody.getAnimObject() != None:
                self.lastOffsetFace = self.animBody.getAnimObject().offsetFace
                outSurface.blit(self.animFace.getImage(), self.animBody.getAnimObject().offsetFace)
            elif self.animFace.getImage() != None:
                outSurface.blit(self.animFace.getImage(), self.lastOffsetFace)
            
            self.surfaceChar.clear()

            if self.isFlipped:
                outSurface = pygame.transform.flip(outSurface, True, False)
                self.surfaceChar.surface.blit(outSurface, (0,0))
                self.surfaceChar.draw(gameDisplay, location=(0, gameDisplay.get_height() - outSurface.get_height()))
            else:
                self.surfaceChar.surface.blit(outSurface, (0,0))
                self.surfaceChar.draw(gameDisplay, location=(gameDisplay.get_width() - outSurface.get_width(), gameDisplay.get_height() - outSurface.get_height()))
        
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

    def __init__(self, imageCharacter, talkScript, voiceLine, characterControllerIndices, characterControllers, playerState):
        state.LaytonContext.__init__(self)
        self.screenIsOverlay = True

        self.screenOutSurface = anim.AlphaSurface(0)
        self.screenOutSurface.surface.fill((0,0,0,0))
        self.screenFader = anim.AnimatedFader(LaytonTextOverlay.DURATION_FADE, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False)
        self.tapFader = anim.AnimatedFader(LaytonTextOverlay.BANK_IMAGE_TAP_FADE_DURATION, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False, activeState=False)

        LaytonTextOverlay.BANK_IMAGE_WINDOW.setAnimationFromName("gfx")
        LaytonTextOverlay.BANK_IMAGE_WINDOW.setInitialFrameFromAnimation()

        talkScript = script.gdScript.fromData(talkScript)
        self.textTalk = anim.NuvoTextScroller(playerState.getFont("fontevent"), talkScript.commands[0].operands[3], textPosOffset=(10, 140 + conf.LAYTON_SCREEN_HEIGHT), targetFramerate=60)

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
                
                if self.indexCharacter - 1 in imageCharacter.keys():
                    self.arrowIsDrawn = True
                    self.targetAnimBody = characterControllers[characterControllerIndices[self.indexCharacter - 1]].animBody
                    self.targetAnimFace = characterControllers[characterControllerIndices[self.indexCharacter - 1]].animFace

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

                    self.setAnimPair("*" + self.animNameStart)

                    if talkScript.commands[0].operands[2] == 2:
                        LaytonTextOverlay.BANK_IMAGE_ARROW.setAnimationFromName("L")
                        characterControllers[characterControllerIndices[self.indexCharacter - 1]].setFlippedState(True)
                        LaytonTextOverlay.BANK_IMAGE_ARROW.pos = LaytonTextOverlay.BANK_IMAGE_ARROW_POS
                        LaytonTextOverlay.BANK_IMAGE_ARROW.setInitialFrameFromAnimation()
                    elif talkScript.commands[0].operands[2] == 3:
                        LaytonTextOverlay.BANK_IMAGE_ARROW.setAnimationFromName("R")
                        characterControllers[characterControllerIndices[self.indexCharacter - 1]].setFlippedState(False)
                        LaytonTextOverlay.BANK_IMAGE_ARROW.pos = (conf.LAYTON_SCREEN_WIDTH - LaytonTextOverlay.BANK_IMAGE_ARROW_POS[0] - LaytonTextOverlay.BANK_IMAGE_ARROW.dimensions[0],
                                                                LaytonTextOverlay.BANK_IMAGE_ARROW_POS[1])
                        LaytonTextOverlay.BANK_IMAGE_ARROW.setInitialFrameFromAnimation()
                    else:
                        self.arrowIsDrawn = False

    def faceAnimFromBodyAnim(self, animName):
        if animName[0] == "*":
            return "*" + animName.split(" ")[-1]
        return animName.split(" ")[-1]

    def setAnimPair(self, animName):
        if self.targetAnimBody != None:
            if not(self.targetAnimBody.setAnimationFromName(animName)):
                self.targetAnimBody.setAnimationFromName(animName + " ")
        if self.targetAnimFace != None:
            if not(self.targetAnimFace.setAnimationFromName(self.faceAnimFromBodyAnim(animName))):
                self.targetAnimFace.setAnimationFromName(self.faceAnimFromBodyAnim(animName + " "))

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
        self.stackOverrideEvents = []

        self.imagesCharacter = []
        self.pointerImagesCharacter = {}

        self.cacheVoiceline = None
        
        self.scriptNextEvent = None
        self.scriptNextEventMode = None
        self.scriptNextTalkBank = None
        self.nextIndexEvent = None
        self.nextIndexEventSub = None

        self.isReadyToKill = False

    def clearCharacterImages(self):
        self.imagesCharacter = []
        self.pointerImagesCharacter = {}
    
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
                self.scriptNextTalkBank = None
                self.scriptNextEvent = None
                self.indexEvent = self.nextIndexEvent
                self.indexEventSub = self.nextIndexEventSub
                self.nextIndexEvent = None
                self.nextIndexEventSub = None
                self.scriptNextEventMode = None
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

    def updateImagePositions(self):
        pass

    def executeGdScriptCommand(self, command):

        def fadeInBothScreens():
            self.faderSceneSurfaceTop.startFadeIn()
            self.faderSceneSurfaceBottom.startFadeIn()
        
        def fadeOutBothScreens():
            self.faderSceneSurfaceTop.startFadeOut()
            self.faderSceneSurfaceBottom.startFadeOut()
        
        def addCharacterToDrawList(charIndex):
            if charIndex in self.pointerImagesCharacter:
                self.imagesCharacter[self.pointerImagesCharacter[charIndex]] = LaytonCharacterController.loadFromIndex(charIndex)
            else:
                self.pointerImagesCharacter[charIndex] = len(self.imagesCharacter)
                self.imagesCharacter.append(LaytonCharacterController.loadFromIndex(charIndex))
            self.updateImagePositions()

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
                self.screenNextObject = LaytonTextOverlay(self.pointerImagesCharacter, tempScriptFile, self.cacheVoiceline, self.pointerImagesCharacter, self.imagesCharacter, self.playerState)
                return False
            else:
                state.debugPrint("ErrEventHandler: Invalid talk script 't" + self.indexEvent + "_" + self.indexEventSub + "_" + str(command.operands[0]) + ".gds'")

        elif command.opcode == b'\x05': # Set current room
            print("DbgEventHandler: Set active room to", command.operands[0])
            self.playerState.currentRoom = command.operands[0]

        # 06, 07 something to do with next handler.
        elif command.opcode == b'\x06':
            self.scriptNextEventMode = command.operands[0]
        elif command.opcode == b'\x07':
            # Seems to be for handlers that execute immediately and hold up the stack (eg movies)
            pass

        elif command.opcode == b'\x08':
            print("DbgEventHandler: Set movie index to", command.operands[0])
        elif command.opcode == b'\x09': # Link next script
            print("DbgEventHandler: Continue execution on", command.operands[0])
            setNextEvent(command.operands[0])
            
        elif command.opcode == b'\x9c':     # Link next script under condition
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
            self.addToStack(han_nazo.LaytonPuzzleHandler(command.operands[0], self.playerState))
            return False

        elif command.opcode == b'\x2a': # Load character image # Power, elegance and grace!!
            addCharacterToDrawList(command.operands[0])
        elif command.opcode == b'\x2b': # Unload character image
            if command.operands[0] in self.pointerImagesCharacter:
                for key in list(self.pointerImagesCharacter.keys()):
                    if self.pointerImagesCharacter[key] > self.pointerImagesCharacter[command.operands[0]]:
                        self.pointerImagesCharacter[key] -= 1
                self.imagesCharacter.pop(self.pointerImagesCharacter[command.operands[0]])
                del self.pointerImagesCharacter[command.operands[0]]
                self.updateImagePositions()
            else:
                state.debugPrint("ErrEventHandler: Character", command.operands[0], "cannot be unloaded as it doesn't exist in cache!")

        elif command.opcode == b'\x21' or command.opcode == b'\x22': # Background-related
            self.stack[0].executeCommand(command)

        # Is 31,32 outin waiting or fading?

        # TODO - On every fade operation, the dialogue box fades as well, and fades first
        # It may be best to just unify this all under one big handler :(

        # TODO - Everything goes below the main fader!
        
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

        # TODO - Write mystery screen
        elif command.opcode == b'\x71': # Spawn mystery screen and clear graphics
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
        
        elif command.opcode == b'\x72':
            self.faderSceneSurfaceTop.startFadeOut(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)
            self.faderSceneSurfaceBottom.startFadeOut(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)
        
        elif command.opcode == b'\x87': # Screen0 Fade out
            self.faderSceneSurfaceTop.startFadeOut(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)
        elif command.opcode == b'\x88': # Screen0 Fade in
            self.faderSceneSurfaceTop.startFadeIn(time=command.operands[0] * conf.ENGINE_FRAME_INTERVAL)

        # CURSED AUDIO CORNER
        # Sampled channel
        
        # 8a, 8b, 8e audio? SAD files match names
        # 98 yet another sadl 16050
        # 2c as characters switch

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
    # 11 170, 10 60, 11 100, 12 110, 14 010, 15 200, 16 010, 16 050, 18 440, 17 140, 17 150, 17 240, 18 450, 17 080,
    
    tempDebugExitLayer.addToStack(LaytonEventHandler(10110, playerState))
    state.play(tempDebugExitLayer, playerState)