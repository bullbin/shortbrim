import pygame, han_nazo, conf, state, script, anim, const
from os import path

import ctypes; ctypes.windll.user32.SetProcessDPIAware()
pygame.init()

class LaytonCharacterController():
    def __init__(self):
        self.isFlipped = False
        self.isFlippedMouth = False
        self.nameSurface = None
        self.animBody = None
        self.animMouth = None
    
    def setAnimBody(self, anim, animName=None):
        self.animBody = anim
        if animName != None:
            self.nameSurface = anim.AnimatedImage(conf.PATH_ASSET_ANI + conf.LAYTON_ASSET_LANG, animName + "_n")
            self.nameSurface = self.nameSurface.setAnimationFromNameAndReturnInitialFrame("gfx")
    
    def setAnimMouth(self, anim):
        self.animMouth = anim
    
    def changeBodyAnim(self, animName):
        if self.animBody != None:
            self.animBody.setAnimationFromName(animName)
    
    def changeMouthAnim(self, animName):
        if self.animMouth != None:
            self.animMouth.setAnimationFromName(animName)
        
    def draw(self, gameDisplay):
        if self.animBody != None and self.animBody.getImage() != None:
            if self.isFlipped and self.animBody.getImage() != None:
                gameDisplay.blit(pygame.transform.flip(self.animBody.getImage(), True, False), self.animBody.pos)
            else:
                self.animBody.draw(gameDisplay)
        if self.animMouth != None:
            if self.isFlippedMouth and self.animMouth.getImage() != None:
                gameDisplay.blit(pygame.transform.flip(self.animMouth.getImage(), True, False), self.animMouth.pos)
            else:
                self.animMouth.draw(gameDisplay)
    
    def update(self, gameClockDelta):
        if self.animBody != None:
            self.animBody.update(gameClockDelta)
        if self.animMouth != None:
            self.animMouth.update(gameClockDelta)

class LaytonCharacterAnimNamePacket():
    def __init__(self, indexChar, animName):
        self.animName = animName
        self.indexChar = indexChar

class LaytonEventTextController():

    CHAR_LEFT = 0
    CHAR_RIGHT = 1

    def __init__(self, direction, indexText, indexChar):
        self.direction = direction
        self.indexText = indexText
        self.indexChar = indexChar
        self.animNamePacketsBody = []
        self.animNamePacketsMouth = []
    
    def getAnimBody(self):
        return self.animNamePacketsBody
    def getAnimMouth(self):
        return self.animNamePacketsMouth

    def getText(self, indexEvent):
        if indexEvent < 100:
            textPathFolder = "000"
        elif indexEvent < 200:
            textPathFolder = "100"
        else:
            textPathFolder = "200"
        try:
            with open(conf.PATH_ASSET_ETEXT + conf.LAYTON_ASSET_LANG + "\\e" + textPathFolder + "\\e" + str(indexEvent) + "_t" + str(self.indexText) + ".txt", 'r') as eventDialogue:
                return eventDialogue.read()
        except FileNotFoundError:
            return ""

class LaytonEventBackground(state.LaytonContext):

    def __init__(self, playerState):
        state.LaytonContext.__init__(self)
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True
        self.backgroundBs = pygame.Surface((0,0))
        self.backgroundTs = pygame.Surface((0,0))
    
    def executeCommand(self, command):
        if command.opcode == b'\x0c':       # Draw image, TS
            if path.exists(conf.PATH_ASSET_BG + command.operands[0][0:-4] + ".png"):
                self.backgroundTs = pygame.image.load(conf.PATH_ASSET_BG + command.operands[0][0:-4] + ".png")
        elif command.opcode == b'\x0b':     # Draw image, BS. Note that the game does not use this image - it uses the darker version
            if path.exists(conf.PATH_ASSET_BG + command.operands[0][0:-4] + ".png"):
                if "room" in command.operands[0][0:-4] and path.exists(conf.PATH_ASSET_BG + "ebg_" + command.operands[0][0:-4].split("_")[1] + ".png"):
                    self.backgroundBs = pygame.image.load(conf.PATH_ASSET_BG + "ebg_" + command.operands[0][0:-4].split("_")[1] + ".png")   # Darkened image
                else:
                    self.backgroundBs = pygame.image.load(conf.PATH_ASSET_BG + command.operands[0][0:-4] + ".png")
        else:
            state.debugPrint("ErrUnkCommand: " + str(command.opcode))

    def draw(self, gameDisplay):
        gameDisplay.blit(self.backgroundTs, (0, 0))
        gameDisplay.blit(self.backgroundBs, (0, conf.LAYTON_SCREEN_HEIGHT))

class LaytonEventGraphics(state.LaytonContext):

    DURATION_TAP_FADE_IN = 500
    DURATION_TEXT_TRANSITION = 500
    DURATION_FADE_IN = 500
    
    def __init__(self, eventIndex, playerState):
        state.LaytonContext.__init__(self)
        self.screenIsOverlay = True

        self.playerState = playerState

        self.eventText              = []
        self.eventTextIndex         = 0
        self.eventTextLoadedIndex   = -1
        self.eventTextImageWindow   = anim.AnimatedImage(conf.PATH_ASSET_ANI, "event_window_1")
        self.eventTextScroller      = anim.TextScroller(playerState.getFont("fontevent"), "", targetFramerate=45)
        self.eventIndex             = eventIndex
        self.eventCharacters        = []
        self.eventCharactersBodyMouthLoadIndices    = [0,0]
        self.eventCharactersLeftRightActive         = [-1,-1]
        self.eventPuzzleHandler = None

        self.eventTextImageWindow.pos = ((conf.LAYTON_SCREEN_WIDTH - self.eventTextImageWindow.dimensions[0]) // 2,
                                         (conf.LAYTON_SCREEN_HEIGHT * 2) - self.eventTextImageWindow.dimensions[1] - 1)
        self.eventTextScroller.textPosOffset = (self.eventTextImageWindow.pos[0] + 12,
                                                self.eventTextImageWindow.pos[1] + 14)
        self.eventTextImageNamePos = (self.eventTextImageWindow.pos[0] + 2,
                                      self.eventTextImageWindow.pos[1] - 3)
        self.eventTextCursorTapAnim         = anim.AnimatedImage(conf.PATH_ASSET_ANI, "cursor_wait", usesAlpha=True)
        self.eventTextCursorTapAnim.pos     = (conf.LAYTON_SCREEN_WIDTH - round(self.eventTextCursorTapAnim.dimensions[0] * 1.5),
                                               conf.LAYTON_SCREEN_HEIGHT * 2 - round(self.eventTextCursorTapAnim.dimensions[1] * 1.25))
        self.eventTextCursorTapAnim.setAnimationFromName("touch")
        self.eventTextCursorTapAnimFader    = anim.AnimatedFader(LaytonEventGraphics.DURATION_TAP_FADE_IN, anim.AnimatedFader.MODE_SINE_SHARP, False, cycle=False)
        self.eventTextImageWindowFader = self.eventTextImageWindowFader = anim.AnimatedFader(LaytonEventGraphics.DURATION_TAP_FADE_IN, anim.AnimatedFader.MODE_TRIANGLE, False, cycle=False)
        self.eventTextSurface = anim.AlphaSurface(0)

        self.backgroundFader = anim.AnimatedFader(LaytonEventGraphics.DURATION_FADE_IN, anim.AnimatedFader.MODE_SINE_SMOOTH, False, cycle=False, inverted=True)
        self.workaroundDisableAdditionalEntries = False
        self.workaroundIntensiveInit = True

        self.clearTemps()
    
    def clearTemps(self):
        self.eventTempAnimControllersBody = []
        self.eventTempAnimControllersMouth = []

    def executeCommand(self, command):
        if command.opcode == b'\x48':           # Select puzzle
            if self.eventPuzzleHandler != None:
                state.debugPrint("WarnPuzzleOverridden: Cached puzzle " + str(self.eventPuzzleHandler.puzzleIndex) + " overriden with " + str(command.operands[0]))
            else:
                state.debugPrint("LogEventLoadedPuzzle: Cached puzzle" + str(command.operands[0]))
            self.eventPuzzleHandler = han_nazo.LaytonPuzzleHandler(command.operands[0], self.playerState)
        elif command.opcode == b'\x6c':           # Draw static image - usually a character
            if len(self.eventCharacters) > self.eventCharactersBodyMouthLoadIndices[0]: # If mouth has already been loaded
                self.eventCharacters[self.eventCharactersBodyMouthLoadIndices[0]].setAnimBody(anim.AnimatedImage(conf.PATH_ASSET_ANI, command.operands[2][0:-4],
                                                                                                                     x=command.operands[0],
                                                                                                                     y=command.operands[1]+conf.LAYTON_SCREEN_HEIGHT), command.operands[2][0:-4])
            else:
                self.eventCharacters.append(LaytonCharacterController())
                self.eventCharacters[-1].setAnimBody(anim.AnimatedImage(conf.PATH_ASSET_ANI, command.operands[2][0:-4], x=command.operands[0],
                                                                            y=command.operands[1]+conf.LAYTON_SCREEN_HEIGHT), command.operands[2][0:-4])
            if not(self.eventCharacters[self.eventCharactersBodyMouthLoadIndices[0]].animBody.setAnimationFromName(command.operands[3])):
                self.eventCharacters[self.eventCharactersBodyMouthLoadIndices[0]].animBody.setActiveFrame(0)
            self.eventCharactersBodyMouthLoadIndices[0] += 1
        elif command.opcode == b'\x6d':           # Draw animated image - usually the character mouth
            if len(self.eventCharacters) > self.eventCharactersBodyMouthLoadIndices[1]: # If mouth has already been loaded
                self.eventCharacters[self.eventCharactersBodyMouthLoadIndices[1]].setAnimMouth(anim.AnimatedImage(conf.PATH_ASSET_ANI, command.operands[2][0:-4],
                                                                                                                      x=command.operands[0],
                                                                                                                      y=command.operands[1]+conf.LAYTON_SCREEN_HEIGHT))
            else:
                self.eventCharacters.append(LaytonCharacterController())
                self.eventCharacters[-1].setAnimMouth(anim.AnimatedImage(conf.PATH_ASSET_ANI, command.operands[2][0:-4],
                                                                             x=command.operands[0], y=command.operands[1]+conf.LAYTON_SCREEN_HEIGHT))
            if not(self.eventCharacters[self.eventCharactersBodyMouthLoadIndices[1]].animMouth.setAnimationFromName(command.operands[3])):
                self.eventCharacters[self.eventCharactersBodyMouthLoadIndices[1]].animMouth.setActiveFrame(0)
            self.eventCharactersBodyMouthLoadIndices[1] += 1

        elif command.opcode == b'\x6e':
            self.eventTempAnimControllersBody.append(LaytonCharacterAnimNamePacket(command.operands[0], command.operands[1]))
        elif command.opcode == b'\x6f':
            self.eventTempAnimControllersMouth.append(LaytonCharacterAnimNamePacket(command.operands[0], command.operands[1]))

        elif command.opcode == b'\x9c' and not(self.workaroundDisableAdditionalEntries):
            self.eventText.append(LaytonEventTextController(LaytonEventTextController.CHAR_RIGHT, command.operands[0], command.operands[1]))
            if len(self.eventTempAnimControllersBody) > 0:
                self.eventText[-1].animNamePacketsBody = self.eventTempAnimControllersBody
            if len(self.eventTempAnimControllersMouth) > 0:
                self.eventText[-1].animNamePacketsMouth = self.eventTempAnimControllersMouth
            self.clearTemps()
            if len(command.operands) > 2:
                self.workaroundDisableAdditionalEntries = True
                state.debugPrint("WarnEventGraphics: Text workaround triggered!")
        elif command.opcode == b'\x9d' and not(self.workaroundDisableAdditionalEntries):
            self.eventText.append(LaytonEventTextController(LaytonEventTextController.CHAR_LEFT, command.operands[0], command.operands[1]))
            if len(self.eventTempAnimControllersBody) > 0:
                self.eventText[-1].animNamePacketsBody = self.eventTempAnimControllersBody
            if len(self.eventTempAnimControllersMouth) > 0:
                self.eventText[-1].animNamePacketsMouth = self.eventTempAnimControllersMouth
            self.clearTemps()
            if len(command.operands) > 2:
                self.workaroundDisableAdditionalEntries = True
                state.debugPrint("WarnEventGraphics: Text workaround triggered!")

        elif command.opcode == b'\xb4':
            if command.operands[0] >= len(self.eventCharacters):
                self.eventCharacters[command.operands[0] % len(self.eventCharacters)].isFlippedMouth = conf.LAYTON_STRING_BOOLEAN[command.operands[1]]
            else:
                self.eventCharacters[command.operands[0]].isFlipped = conf.LAYTON_STRING_BOOLEAN[command.operands[1]]
        else:
            state.debugPrint("ErrEventUnkCommand: " + str(command.opcode))
    
    def incrementEventText(self):
        if len(self.eventText) > 0 and self.eventTextIndex < len(self.eventText):
            self.eventTextScroller.textInput = self.eventText[self.eventTextIndex].getText(self.eventIndex)
            for bodyController in self.eventText[self.eventTextIndex].getAnimBody():
                self.eventCharacters[bodyController.indexChar].changeBodyAnim(bodyController.animName)
            for mouthController in self.eventText[self.eventTextIndex].getAnimMouth():
                self.eventCharacters[mouthController.indexChar].changeMouthAnim(mouthController.animName)
            self.eventTextScroller.reset()

    def update(self, gameClockDelta):
        if not(self.workaroundIntensiveInit) or self.workaroundIntensiveInit and gameClockDelta <= round(1000 / conf.ENGINE_FPS):   # Skip first init cycle if the engine just loaded a file, it will be huge
            if self.backgroundFader.isActive:
                self.backgroundFader.update(gameClockDelta)
            else:
                for event in self.eventCharacters:
                    event.update(gameClockDelta)
                if len(self.eventText) > 0 and self.eventTextIndex < len(self.eventText):   # Switch to signalling technique to reduce overhead when writing event code
                    if self.eventText[self.eventTextIndex].direction == LaytonEventTextController.CHAR_LEFT:
                        self.eventTextImageWindow.setAnimationFromNameIfNotActive("gfx2")
                    elif self.eventText[self.eventTextIndex].direction == LaytonEventTextController.CHAR_RIGHT:
                        self.eventTextImageWindow.setAnimationFromNameIfNotActive("gfx")
                    else:
                        self.eventTextImageWindow.setAnimationFromNameIfNotActive("gfx3")
                    
                    if self.eventTextImageWindowFader.inverted != self.eventTextImageWindowFader.initialInverted:
                        if self.eventText[self.eventTextIndex].direction == LaytonEventTextController.CHAR_LEFT:
                            self.eventCharactersLeftRightActive[0] = self.eventText[self.eventTextIndex].indexChar
                        elif self.eventText[self.eventTextIndex].direction == LaytonEventTextController.CHAR_RIGHT:
                            self.eventCharactersLeftRightActive[1] = self.eventText[self.eventTextIndex].indexChar
                    
                    if not(self.eventTextScroller.getDrawingState()):
                        self.eventTextCursorTapAnimFader.update(gameClockDelta)
                        self.eventTextCursorTapAnim.setAlpha(self.eventTextCursorTapAnimFader.getStrength() * 255)
                        self.eventTextCursorTapAnim.update(gameClockDelta)
                    else:
                        self.eventTextCursorTapAnim.reset()
                        self.eventTextCursorTapAnimFader.reset()

                    while self.eventTextLoadedIndex < self.eventTextIndex:
                        self.incrementEventText()
                        self.eventTextLoadedIndex += 1
                        if self.eventTextLoadedIndex > 0:
                            if self.eventTextLoadedIndex == len(self.eventText) - 1:
                                self.eventTextImageWindowFader = anim.AnimatedFader(LaytonEventGraphics.DURATION_TEXT_TRANSITION // 2, anim.AnimatedFader.MODE_SINE_SHARP, False, cycle=False, inverted=True)
                            else:
                                self.eventTextImageWindowFader = anim.AnimatedFader(LaytonEventGraphics.DURATION_TEXT_TRANSITION, anim.AnimatedFader.MODE_SINE_SHARP, False, inverted=True)
                            self.eventTextImageWindowFader.reset()

                    if (self.eventTextImageWindowFader.getStrength() == 1):
                        self.eventTextScroller.update(gameClockDelta)

                    self.eventTextImageWindowFader.update(gameClockDelta)
                    self.eventTextImageWindow.update(gameClockDelta)
        else:
            self.workaroundIntensiveInit = False

    def draw(self, gameDisplay):
        for indexChar in self.eventCharactersLeftRightActive:
            if indexChar != -1:
                self.eventCharacters[indexChar].draw(gameDisplay)

        if len(self.eventText) > 0 and self.eventTextIndex < len(self.eventText):
            if not(self.backgroundFader.isActive):
                self.eventTextSurface.setAlpha(self.eventTextImageWindowFader.getStrength() * 255)
                self.eventTextSurface.clear()
                self.eventTextImageWindow.draw(self.eventTextSurface.surface)

                if self.eventTextImageWindowFader.isActive and self.eventTextIndex > 0:
                    if self.eventTextImageWindowFader.initialInverted != self.eventTextImageWindowFader.inverted and self.eventCharacters[self.eventText[self.eventTextIndex].indexChar].nameSurface != None:
                        self.eventTextSurface.surface.blit(self.eventCharacters[self.eventText[self.eventTextIndex].indexChar].nameSurface, self.eventTextImageNamePos)
                    elif self.eventCharacters[self.eventText[self.eventTextIndex - 1].indexChar].nameSurface != None:
                        self.eventTextSurface.surface.blit(self.eventCharacters[self.eventText[self.eventTextIndex - 1].indexChar].nameSurface, self.eventTextImageNamePos)
                elif self.eventCharacters[self.eventText[self.eventTextIndex].indexChar].nameSurface != None:
                    self.eventTextSurface.surface.blit(self.eventCharacters[self.eventText[self.eventTextIndex].indexChar].nameSurface, self.eventTextImageNamePos)

                self.eventTextSurface.draw(gameDisplay)
                self.eventTextScroller.draw(gameDisplay)

        if not(self.eventTextScroller.getDrawingState()):
            self.eventTextCursorTapAnim.draw(gameDisplay)
        
        if self.backgroundFader.isActive:
            tempFaderSurface = pygame.Surface((conf.LAYTON_SCREEN_WIDTH, conf.LAYTON_SCREEN_HEIGHT * 2)).convert_alpha()
            tempFaderSurface.fill((0,0,0,round(self.backgroundFader.getStrength() * 255)))
            gameDisplay.blit(tempFaderSurface, (0,0))
    
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            if len(self.eventText) > 0:
                if (self.eventTextImageWindowFader.getStrength() == 1):
                    if self.eventTextScroller.isWaitingForTap:
                        self.eventTextScroller.isWaitingForTap = False
                    elif self.eventTextScroller.drawIncomplete:
                        self.eventTextScroller.skip()
                    else:
                        if self.eventTextIndex < len(self.eventText) - 1:
                            self.eventTextIndex += 1
                        if self.eventTextIndex == len(self.eventText) - 1 and self.eventPuzzleHandler != None:
                            self.screenNextObject = self.eventPuzzleHandler

        if event.type == const.ANIM_SET_ANIM:
            event.command = event.data.split(" ")
            state.debugPrint("LogEventCommand: Animation switched!")
            if self.eventCharacters[int(event.command[1])].animBody != None:
                self.eventCharacters[int(event.command[1])].animBody.setAnimationFromName(event.command[2])
            if self.eventCharacters[int(event.command[1])].animMouth != None:
                self.eventCharacters[int(event.command[1])].animMouth.setAnimationFromName(event.command[2])

class LaytonEventHandler(state.LaytonSubscreen):
    def __init__(self, eventIndex, playerState):
        state.LaytonSubscreen.__init__(self)
        self.transitionsEnableIn = False
        self.transitionsEnableOut = False
        self.screenBlockInput = True

        self.addToStack(LaytonEventBackground(playerState))
        self.addToStack(LaytonEventGraphics(eventIndex, playerState))
        self.commandFocus = self.stack[-1]
        self.executeGdScript(script.gdScript(conf.PATH_ASSET_SCRIPT + "event\\e" + str(eventIndex) + ".gds", playerState, enableBranching=True))

    def executeGdScript(self, puzzleScript):
        for command in puzzleScript.commands:
            if command.opcode == b'\x0b' or command.opcode == b'\x0c':
                self.stack[0].executeCommand(command)
            elif self.commandFocus == None:
                self.executeCommand(command)
            else:
                self.commandFocus.executeCommand(command)

if __name__ == '__main__':
    playerState = state.LaytonPlayerState()
    playerState.puzzleLoadData()
    playerState.puzzleLoadNames()
    playerState.remainingHintCoins = 10
    state.play(LaytonEventHandler(9, playerState), playerState)   # 57 is interesting, 45 has mouth layering issue, 48 causes a crash