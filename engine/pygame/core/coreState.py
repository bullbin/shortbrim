# State Components of LAYTON1

import coreProp, coreAnim, gdsLib

class LaytonPuzzleDataEntry():
    def __init__(self, decayValues):
        self.name = ""
        self.unlocked = True
        self.unlockedHintLevel = 0
        self.category = None
        self.decayState = 0
        self.decayValues = decayValues
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

    def puzzleLoadNames(self):
        if len(self.puzzleData.keys()) == 0:
            self.puzzleLoadData()
        qscript = gdsLib.gdScript(coreProp.LAYTON_ASSET_ROOT + "script\\qinfo\\" + coreProp.LAYTON_ASSET_LANG + "\\qscript.gds")
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
        pscript = gdsLib.gdScript(coreProp.LAYTON_ASSET_ROOT + "script\\pcarot\\pscript.gds")
        for instruction in pscript.commands:
            if instruction.opcode == b'\xc3':
                # Set picarot decay
                self.puzzleData[instruction.operands[0]] = LaytonPuzzleDataEntry(instruction.operands[1:])

class LaytonScreen():
    def __init__(self):
        self.stack = []
        self.hasStackChanged = False
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

            invStackIndex = len(self.stack) - 1
            while invStackIndex >= 0:
                self.stack.append(self.stack[invStackIndex].getFutureContext())
                if self.stack[-1] == None:
                    self.stack.pop()
                else:
                    invStackIndex -= 1

                if self.stack[invStackIndex].screenBlockInput:
                    break
                    
                invStackIndex -= 1

            # Fix the fader from going out of bounds.

            if len(self.stack) > 1:
                if self.stack[-1].screenIsOverlay:
                    pass
                elif self.stack[-1].screenIsBasicOverlay:
                    pass
            
            invStackIndex = len(self.stack) - 1
            while invStackIndex >= 0:
                self.stack[invStackIndex].update(gameClockDelta)
                if not(self.stack[invStackIndex].screenIsOverlay or self.stack[invStackIndex].screenIsBasicOverlay):
                    break
                invStackIndex -= 1

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
            invStackIndex = len(self.stack) - 1
            while invStackIndex >= 0:
                self.stack[invStackIndex].handleEvent(event)
                if self.stack[invStackIndex].screenBlockInput:
                    break
                invStackIndex -= 1

class LaytonSubscreen(LaytonScreen):
    def __init__(self):
        LaytonScreen.__init__(self)
        self.isContextFinished = False
    
    def update(self, gameClockDelta):
        super().update(gameClockDelta)
        self.updateSubscreenMethods(gameClockDelta)
    
    def updateSubscreenMethods(self, gameClockDelta):
        pass

class LaytonContext():
    def __init__(self):
        self.screenObject           = None
        self.screenNextObject       = None
        self.screenBlockInput       = False     # This context absorbs all inputs, whether in the context or not
        self.screenIsOverlay        = False     # Requires drawing of all screens below it - slow
        self.screenIsBasicOverlay   = False     # Overlays only above the screen below it

        self.transitionsEnableIn    = True
        self.transitionsEnableOut   = True

        self.isContextFinished = False

    def getContextState(self):
        return self.isContextFinished
    
    def getFutureContext(self):
        if self.screenNextObject != None:
            screenNextObject = self.screenNextObject
            self.screenNextObject = None
            return screenNextObject
        return None

    def draw(self, gameDisplay):
        pass
    
    def update(self, gameClockDelta):
        pass
    
    def handleEvent(self, event):
        pass