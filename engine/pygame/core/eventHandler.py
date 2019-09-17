import pygame, nazoHandler, coreProp, coreState, coreLib, coreAnim, constUserEvent
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
            self.nameSurface = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG, animName + "_n")
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
            with open(coreProp.PATH_ASSET_ETEXT + coreProp.LAYTON_ASSET_LANG + "\\e" + textPathFolder + "\\e" + str(indexEvent) + "_t" + str(self.indexText) + ".txt", 'r') as eventDialogue:
                return eventDialogue.read()
        except FileNotFoundError:
            return ""

class LaytonEventBackground(coreState.LaytonContext):
    def __init__(self, playerState):
        coreState.LaytonContext.__init__(self)
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True
        self.backgroundBs = pygame.Surface((0,0))
        self.backgroundTs = pygame.Surface((0,0))
    
    def executeCommand(self, command):
        if command.opcode == b'\x0c':       # Draw image, TS
            if path.exists(coreProp.PATH_ASSET_BG + command.operands[0][0:-4] + ".png"):
                self.backgroundTs = pygame.image.load(coreProp.PATH_ASSET_BG + command.operands[0][0:-4] + ".png")
        elif command.opcode == b'\x0b':     # Draw image, BS. Note that the game does not use this image - it uses the darker version
            if path.exists(coreProp.PATH_ASSET_BG + command.operands[0][0:-4] + ".png"):
                if "room" in command.operands[0][0:-4] and path.exists(coreProp.PATH_ASSET_BG + "ebg_" + command.operands[0][0:-4].split("_")[1] + ".png"):
                    self.backgroundBs = pygame.image.load(coreProp.PATH_ASSET_BG + "ebg_" + command.operands[0][0:-4].split("_")[1] + ".png")   # Darkened image
                else:
                    self.backgroundBs = pygame.image.load(coreProp.PATH_ASSET_BG + command.operands[0][0:-4] + ".png")
        else:
            print("ErrUnkCommand: " + str(command.opcode))
    
    def draw(self, gameDisplay):
        gameDisplay.blit(self.backgroundTs, (0, 0))
        gameDisplay.blit(self.backgroundBs, (0, coreProp.LAYTON_SCREEN_HEIGHT))

class LaytonEventGraphics(coreState.LaytonContext):

    def __init__(self, eventIndex, playerState):
        coreState.LaytonContext.__init__(self)
        self.screenIsOverlay = True

        self.playerState = playerState

        self.eventText              = []
        self.eventTextIndex         = 0
        self.eventTextLoadedIndex   = -1
        self.eventTextImageWindow   = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, "event_window_1")
        self.eventTextScroller      = coreAnim.TextScroller(playerState.getFont("fontevent"), "", targetFramerate=60)
        self.eventIndex             = eventIndex
        self.eventCharacters        = []
        self.eventCharactersBodyMouthLoadIndices    = [0,0]
        self.eventCharactersLeftRightActive         = [-1,-1]
        self.eventPuzzleHandler = None

        self.eventTextImageWindow.pos = ((coreProp.LAYTON_SCREEN_WIDTH - self.eventTextImageWindow.dimensions[0]) // 2,
                                         (coreProp.LAYTON_SCREEN_HEIGHT * 2) - self.eventTextImageWindow.dimensions[1] - 1)
        self.eventTextScroller.textPosOffset = (self.eventTextImageWindow.pos[0] + 12,
                                                self.eventTextImageWindow.pos[1] + 14)
        self.eventTextImageNamePos = (self.eventTextImageWindow.pos[0] + 2,
                                      self.eventTextImageWindow.pos[1] - 3)

        self.clearTemps()
    
    def clearTemps(self):
        self.eventTempAnimControllersBody = []
        self.eventTempAnimControllersMouth = []

    def executeCommand(self, command):
        if command.opcode == b'\x48':           # Select puzzle
            if self.eventPuzzleHandler != None:
                print("WarnPuzzleOverridden: Cached puzzle", self.eventPuzzleHandler.puzzleIndex, "overriden with", command.operands[0])
            else:
                print("LogEventLoadedPuzzle: Cached puzzle", command.operands[0])
            self.eventPuzzleHandler = nazoHandler.LaytonPuzzleHandler(command.operands[0], playerState)
        elif command.opcode == b'\x6c':           # Draw static image - usually a character
            if len(self.eventCharacters) > self.eventCharactersBodyMouthLoadIndices[0]: # If mouth has already been loaded
                self.eventCharacters[self.eventCharactersBodyMouthLoadIndices[0]].setAnimBody(coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, command.operands[2][0:-4],
                                                                                                                     x=command.operands[0],
                                                                                                                     y=command.operands[1]+coreProp.LAYTON_SCREEN_HEIGHT), command.operands[2][0:-4])
            else:
                self.eventCharacters.append(LaytonCharacterController())
                self.eventCharacters[-1].setAnimBody(coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, command.operands[2][0:-4], x=command.operands[0],
                                                                            y=command.operands[1]+coreProp.LAYTON_SCREEN_HEIGHT), command.operands[2][0:-4])
            if not(self.eventCharacters[self.eventCharactersBodyMouthLoadIndices[0]].animBody.setAnimationFromName(command.operands[3])):
                self.eventCharacters[self.eventCharactersBodyMouthLoadIndices[0]].animBody.setActiveFrame(0)
            self.eventCharactersBodyMouthLoadIndices[0] += 1
        elif command.opcode == b'\x6d':           # Draw animated image - usually the character mouth
            if len(self.eventCharacters) > self.eventCharactersBodyMouthLoadIndices[1]: # If mouth has already been loaded
                self.eventCharacters[self.eventCharactersBodyMouthLoadIndices[1]].setAnimMouth(coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, command.operands[2][0:-4],
                                                                                                                      x=command.operands[0],
                                                                                                                      y=command.operands[1]+coreProp.LAYTON_SCREEN_HEIGHT))
            else:
                self.eventCharacters.append(LaytonCharacterController())
                self.eventCharacters[-1].setAnimMouth(coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, command.operands[2][0:-4],
                                                                             x=command.operands[0], y=command.operands[1]+coreProp.LAYTON_SCREEN_HEIGHT))
            if not(self.eventCharacters[self.eventCharactersBodyMouthLoadIndices[1]].animMouth.setAnimationFromName(command.operands[3])):
                self.eventCharacters[self.eventCharactersBodyMouthLoadIndices[1]].animMouth.setActiveFrame(0)
            self.eventCharactersBodyMouthLoadIndices[1] += 1

        elif command.opcode == b'\x6e':
            self.eventTempAnimControllersBody.append(LaytonCharacterAnimNamePacket(command.operands[0], command.operands[1]))
        elif command.opcode == b'\x6f':
            self.eventTempAnimControllersMouth.append(LaytonCharacterAnimNamePacket(command.operands[0], command.operands[1]))

        elif command.opcode == b'\x9c':
            self.eventText.append(LaytonEventTextController(LaytonEventTextController.CHAR_RIGHT, command.operands[0], command.operands[1]))
            if len(self.eventTempAnimControllersBody) > 0:
                self.eventText[-1].animNamePacketsBody = self.eventTempAnimControllersBody
            if len(self.eventTempAnimControllersMouth) > 0:
                self.eventText[-1].animNamePacketsMouth = self.eventTempAnimControllersMouth
            self.clearTemps()
        elif command.opcode == b'\x9d':
            self.eventText.append(LaytonEventTextController(LaytonEventTextController.CHAR_LEFT, command.operands[0], command.operands[1]))
            if len(self.eventTempAnimControllersBody) > 0:
                self.eventText[-1].animNamePacketsBody = self.eventTempAnimControllersBody
            if len(self.eventTempAnimControllersMouth) > 0:
                self.eventText[-1].animNamePacketsMouth = self.eventTempAnimControllersMouth
            self.clearTemps()
        elif command.opcode == b'\xb4':
            if command.operands[0] >= len(self.eventCharacters):
                self.eventCharacters[command.operands[0] % len(self.eventCharacters)].isFlippedMouth = coreProp.LAYTON_STRING_BOOLEAN[command.operands[1]]
            else:
                self.eventCharacters[command.operands[0]].isFlipped = coreProp.LAYTON_STRING_BOOLEAN[command.operands[1]]
        else:
            print("ErrEventUnkCommand: " + str(command.opcode))
    
    def incrementEventText(self):
        if len(self.eventText) > 0 and self.eventTextIndex < len(self.eventText):
            self.eventTextScroller.textInput = self.eventText[self.eventTextIndex].getText(self.eventIndex)
            for bodyController in self.eventText[self.eventTextIndex].getAnimBody():
                self.eventCharacters[bodyController.indexChar].changeBodyAnim(bodyController.animName)
            for mouthController in self.eventText[self.eventTextIndex].getAnimMouth():
                self.eventCharacters[mouthController.indexChar].changeMouthAnim(mouthController.animName)
            self.eventTextScroller.reset()

    def update(self, gameClockDelta):
        for event in self.eventCharacters:
            event.update(gameClockDelta)
        if len(self.eventText) > 0 and self.eventTextIndex < len(self.eventText):   # Switch to signalling technique to reduce overhead when writing event code
            if self.eventText[self.eventTextIndex].direction == LaytonEventTextController.CHAR_LEFT:
                self.eventCharactersLeftRightActive[0] = self.eventText[self.eventTextIndex].indexChar
                self.eventTextImageWindow.setAnimationFromNameIfNotActive("gfx2")
            elif self.eventText[self.eventTextIndex].direction == LaytonEventTextController.CHAR_RIGHT:
                self.eventCharactersLeftRightActive[1] = self.eventText[self.eventTextIndex].indexChar
                self.eventTextImageWindow.setAnimationFromNameIfNotActive("gfx")
            else:
                self.eventTextImageWindow.setAnimationFromNameIfNotActive("gfx3")
            self.eventTextImageWindow.update(gameClockDelta)
            self.eventTextScroller.update(gameClockDelta)

            while self.eventTextLoadedIndex < self.eventTextIndex:
                self.incrementEventText()
                self.eventTextLoadedIndex += 1

    def draw(self, gameDisplay):
        for indexChar in self.eventCharactersLeftRightActive:
            if indexChar != -1:
                self.eventCharacters[indexChar].draw(gameDisplay)
        if len(self.eventText) > 0 and self.eventTextIndex < len(self.eventText):
            self.eventTextImageWindow.draw(gameDisplay)
            self.eventTextScroller.draw(gameDisplay)
            if self.eventCharacters[self.eventText[self.eventTextIndex].indexChar].nameSurface != None:
                gameDisplay.blit(self.eventCharacters[self.eventText[self.eventTextIndex].indexChar].nameSurface, self.eventTextImageNamePos)
    
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            if self.eventTextScroller.isWaitingForTap:
                self.eventTextScroller.isWaitingForTap = False
            elif self.eventTextScroller.drawIncomplete:
                self.eventTextScroller.skip()
            else:
                if self.eventTextIndex < len(self.eventText) - 1:
                    self.eventTextIndex += 1
                elif len(self.eventText) > 0 and self.eventPuzzleHandler != None:
                    self.screenNextObject = self.eventPuzzleHandler

        if event.type == constUserEvent.ANIM_SET_ANIM:
            event.command = event.data.split(" ")
            print("LogEventCommand: Animation switched!")
            if self.eventCharacters[int(event.command[1])].animBody != None:
                self.eventCharacters[int(event.command[1])].animBody.setAnimationFromName(event.command[2])
            if self.eventCharacters[int(event.command[1])].animMouth != None:
                self.eventCharacters[int(event.command[1])].animMouth.setAnimationFromName(event.command[2])

class LaytonEventHandler(coreState.LaytonSubscreen):
    def __init__(self, eventIndex, playerState):
        coreState.LaytonSubscreen.__init__(self)

        self.addToStack(LaytonEventBackground(playerState))
        self.addToStack(LaytonEventGraphics(eventIndex, playerState))
        self.commandFocus = self.stack[-1]
        self.executeGdScript(coreLib.gdScript(coreProp.PATH_ASSET_SCRIPT + "event\\e" + str(eventIndex) + ".gds", playerState, enableBranching=True))

    def executeGdScript(self, puzzleScript):
        for command in puzzleScript.commands:
            if command.opcode == b'\x0b' or command.opcode == b'\x0c':
                self.stack[0].executeCommand(command)
            elif self.commandFocus == None:
                self.executeCommand(command)
            else:
                self.commandFocus.executeCommand(command)

playerState = coreState.LaytonPlayerState()
playerState.puzzleLoadData()
playerState.puzzleLoadNames()
playerState.remainingHintCoins = 10
coreState.play(LaytonEventHandler(1, playerState), playerState)   # 57 is interesting, 45 has mouth layering issue, 48 causes a crash
