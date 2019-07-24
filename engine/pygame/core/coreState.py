# State Components of LAYTON1

import coreProp, pygame, coreAnim, gdsLib

class LaytonPuzzleDataEntry():
    def __init__(self, decayValues):
        self.name = ""
        self.unlocked = True
        self.unlockedHintLevel = 0
        self.wasCompleted = False
        self.wasQuit = False
        self.category = None
        self.decayState = 0
        self.decayValues = decayValues
        self.countAttempts = 0
    def getValue(self):
        if self.decayState > len(self.decayValues) - 1:
            return self.decayValues[-1]
        return self.decayValues[self.decayState]

class LaytonPlayerState():
    def __init__(self):
        self.name = "LT1_ENGINE"
        self.puzzleData = {}
        self.currentRoom = 0
        self.remainingHintCoins = 0
        self.hintCoinsFound = []
        self.fonts = {}

        if coreProp.GRAPHICS_USE_GAME_FONTS:
            self.fonts["font18"]    = coreAnim.FontMap(coreProp.PATH_ASSET_FONT + "font18.png", coreProp.PATH_ASSET_FONT + "font18.xml", encoding="shift-jis", calculateWidth = True)
            self.fonts["fontevent"] = coreAnim.FontMap(coreProp.PATH_ASSET_FONT + "fontevent.png", coreProp.PATH_ASSET_FONT + "fontevent.xml", encoding="cp1252", calculateWidth = True, yFontGap=3)
            self.fonts["fontq"]     = coreAnim.FontMap(coreProp.PATH_ASSET_FONT + "fontq.png", coreProp.PATH_ASSET_FONT + "fontq.xml", encoding="cp1252", calculateWidth = True, yFontGap=2)
        else:
            for fontName in ["font18", "fontevent", "fontq"]:
                self.fonts[fontName] = pygame.font.SysFont('freesansmono', 17)

    def getFont(self, fontName):
        if fontName in self.fonts.keys():
            return self.fonts[fontName]
        return pygame.font.SysFont('freesansmono', 17)

    def puzzleLoadNames(self):
        if len(self.puzzleData.keys()) == 0:
            self.puzzleLoadData()
        qscript = gdsLib.gdScript(coreProp.PATH_ASSET_SCRIPT + "qinfo\\" + coreProp.LAYTON_ASSET_LANG + "\\qscript.gds")
        for instruction in qscript.commands:
            if instruction.opcode == b'\xdc':
                try:
                    self.puzzleData[instruction.operands[0]].name = instruction.operands[2]
                    self.puzzleData[instruction.operands[0]].category = instruction.operands[1]
                except KeyError:
                    self.puzzleData[instruction.operands[0]] = LaytonPuzzleDataEntry([])
                    self.puzzleData[instruction.operands[0]].name = instruction.operands[2]
                    self.puzzleData[instruction.operands[0]].category = instruction.operands[1]

    def puzzleLoadData(self):
        pscript = gdsLib.gdScript(coreProp.PATH_ASSET_SCRIPT + "pcarot\\pscript.gds")
        for instruction in pscript.commands:
            if instruction.opcode == b'\xc3':
                # Set picarot decay
                self.puzzleData[instruction.operands[0]] = LaytonPuzzleDataEntry(instruction.operands[1:])

class LaytonScreen():
    def __init__(self):
        self.stack = []
        self.stackLastBackElement = 0
        self.stackLastBlockElement = 0
        self.hasStackChanged = True
        self.fader = coreAnim.Fader()
        self.transitioning = False

    def addToStack(self, screenObject):
        self.stack.append(screenObject)
        self.hasStackChanged = True

    def draw(self, gameDisplay):
        if len(self.stack) >= 1:
            if self.stack[-1].screenIsOverlay:
                # This is an expensive operation, as every item before must be drawn
                for screenObject in self.stack[0:-1]:
                    screenObject.draw(gameDisplay)
            elif self.stack[-1].screenIsBasicOverlay and len(self.stack) > 1:
                # This is a less expensive operation; only the screen before needs to be drawn
                self.stack[-2].draw(gameDisplay)
            self.stack[-1].draw(gameDisplay)
        self.fader.draw(gameDisplay)

    def update(self, gameClockDelta):
        if len(self.stack) >= 1:
            if self.hasStackChanged:            # Update stack pointers if stack has changed
                self.stackLastBackElement = 0
                self.stackLastBlockElement = 0
                invStackIndex = len(self.stack) - 1
                while invStackIndex >= 0:
                    if not(self.stack[invStackIndex].screenIsBasicOverlay or self.stack[invStackIndex].screenIsOverlay) and self.stackLastBackElement < invStackIndex:
                        self.stackLastBackElement = invStackIndex
                    if self.stack[invStackIndex].screenBlockInput and self.stackLastBlockElement < invStackIndex:
                        self.stackLastBlockElement = invStackIndex
                    invStackIndex -= 1
                self.hasStackChanged = False
            
            for indexUpdate in range(self.stackLastBackElement, len(self.stack)):
                self.stack[indexUpdate].update(gameClockDelta)
                self.stackChangePrior = self.hasStackChanged
                self.addToStack(self.stack[indexUpdate].getFutureContext())
                if self.stack[-1] == None:
                    self.stack.pop()
                    if self.stackChangePrior == False:
                        self.hasStackChanged = False
                if self.stack[indexUpdate].screenStackUpdate:
                    self.hasStackChanged = True
                    
            # Fix the fader from going out of bounds.
            self.transitioning = False
            if self.fader.strength > 1:
                self.fader.strength = 1
            elif self.fader.strength < 0:
                self.fader.strength = 0

            if not(self.stack[-1].getContextState()):
                # The last object on the stack is still operating.
                if self.fader.strength > 0:
                    self.transitioning = True
                    # The fader has been drawn, so start fading it if required
                    if self.stack[-1].transitionsEnableIn:
                        if self.fader.interval > 0:
                            self.fader.interval *= -1
                        self.fader.strength += self.fader.interval
                    else:
                        self.fader.strength = 0
            else:
                # The last object on the stack has finished operation, start deleting it.
                if self.fader.strength >= 1:
                    self.stack.pop()
                    self.hasStackChanged = True
                elif self.stack[-1].transitionsEnableOut:
                    self.transitioning = True
                    if self.fader.interval < 0:
                        self.fader.interval *= -1
                    self.fader.strength += self.fader.interval
                else:
                    # This code does not support the blending overlay modes as they render to the same target.
                    self.fader.strength = 0
                    self.stack.pop()
                    self.hasStackChanged = True

    def handleEvent(self, event):
        if not(self.transitioning):
            for indexUpdate in range(self.stackLastBlockElement, len(self.stack)):
                self.stack[indexUpdate].handleEvent(event)

class LaytonSubscreen(LaytonScreen):
    def __init__(self):
        LaytonScreen.__init__(self)
        self.isContextFinished = False
    
    def update(self, gameClockDelta):
        super().update(gameClockDelta)
        self.updateSubscreenMethods(gameClockDelta)
    
    def updateSubscreenMethods(self, gameClockDelta): pass

class LaytonContext():
    def __init__(self):
        self.screenObject           = None
        self.screenNextObject       = None
        self.screenBlockInput       = False     # This context absorbs all inputs, whether in the context or not
        self.screenIsOverlay        = False     # Requires drawing of all screens below it - slow
        self.screenIsBasicOverlay   = False     # Overlays only above the screen below it

        self.transitionsEnableIn    = True
        self.transitionsEnableOut   = True

        self.screenStackUpdate = False
        self.isContextFinished = False

    def getContextState(self):
        return self.isContextFinished
    
    def getFutureContext(self):
        if self.screenNextObject != None:
            screenNextObject = self.screenNextObject
            self.screenNextObject = None
            return screenNextObject
        return None
    
    def executeCommand(self, command):
        print("ErrNoRedefinitionCommand: " + str(command.opcode))

    def setStackUpdate(self):
        self.screenStackUpdate = True

    def draw(self, gameDisplay): pass
    
    def update(self, gameClockDelta): pass
    
    def handleEvent(self, event): pass