# State Components of LAYTON1

import coreProp, pygame, coreAnim, coreLib
from os import path
import ctypes; ctypes.windll.user32.SetProcessDPIAware() # Scale window to ensure perfect pixels

if coreProp.ENGINE_FORCE_USE_ALT_TIMER:
    import time

def debugPrint(line):
    if coreProp.ENGINE_DEBUG_MODE:
        print(line)

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
        self.puzzletTutorialsCompleted = []
        self.currentRoom = 0
        self.remainingHintCoins = 0
        self.hintCoinsFound = []
        self.fonts = {}

        for fontName, fontEncoding, xFontSpacing, yFontSpacing, altFontSize in [("font18", "shift-jis", 1, 1, 17), ("fontevent", "cp1252", 1, 3, 17), ("fontq", "cp1252", 1, 2, 17)]:
            if coreProp.GRAPHICS_USE_GAME_FONTS:
                self.fonts[fontName] = coreAnim.FontMap(coreProp.PATH_ASSET_FONT + fontName + ".png", coreProp.PATH_ASSET_FONT + fontName + ".xml", encoding=fontEncoding, calculateWidth = True, xFontGap=xFontSpacing, yFontGap=yFontSpacing)
                if not(self.fonts[fontName].isLoaded):
                    self.fonts[fontName] = coreAnim.FontVector(pygame.font.SysFont('freesansmono', altFontSize), yFontSpacing)
            else:
                self.fonts[fontName] = coreAnim.FontVector(pygame.font.SysFont('freesansmono', altFontSize), yFontSpacing)

    def getFont(self, fontName):
        if fontName in self.fonts.keys():
            return self.fonts[fontName]
        return pygame.font.SysFont('freesansmono', 17)

    def puzzleLoadNames(self):
        if len(self.puzzleData.keys()) == 0:
            self.puzzleLoadData()
        qscript = coreLib.gdScript(coreProp.PATH_ASSET_SCRIPT + "qinfo\\" + coreProp.LAYTON_ASSET_LANG + "\\qscript.gds", None)
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
        pscript = coreLib.gdScript(coreProp.PATH_ASSET_SCRIPT + "pcarot\\pscript.gds", None)
        for instruction in pscript.commands:
            if instruction.opcode == b'\xc3': # Set picarot decay
                self.puzzleData[instruction.operands[0]] = LaytonPuzzleDataEntry(instruction.operands[1:])

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

        self.drawBoundingRect = pygame.Rect((0,0), (coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_WIDTH * 2))

    def getContextState(self):
        return self.isContextFinished
    
    def getFutureContext(self):
        if self.screenNextObject != None:
            screenNextObject = self.screenNextObject
            self.screenNextObject = None
            return screenNextObject
        return None
    
    def executeCommand(self, command):
        debugPrint("ErrNoRedefinitionCommand: " + str(command.opcode))

    def setStackUpdate(self):
        self.screenStackUpdate = True

    def draw(self, gameDisplay): pass
    
    def update(self, gameClockDelta): return False 
    
    def handleEvent(self, event): return False

class LaytonScreen(LaytonContext):
    def __init__(self):
        LaytonContext.__init__(self)
        self.screenBlockInput       = True
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.stack = []
        self.stackLastBackElement = 0
        self.stackLastBlockElement = 0
        self.hasStackChanged = True

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

    def updateStackPointers(self):
        self.stackLastBackElement = 0
        self.stackLastBlockElement = 0
        invStackIndex = len(self.stack) - 1
        while invStackIndex >= 0:
            if not(self.stack[invStackIndex].screenIsBasicOverlay or self.stack[invStackIndex].screenIsOverlay) and self.stackLastBackElement < invStackIndex:
                self.stackLastBackElement = invStackIndex
            if self.stack[invStackIndex].screenBlockInput and self.stackLastBlockElement < invStackIndex:
                self.stackLastBlockElement = invStackIndex
            invStackIndex -= 1

    def executeCommand(self, command):
        debugPrint("CommandNoTarget: " + str(command.opcode))

    def update(self, gameClockDelta):
        if len(self.stack) >= 1:
            if self.hasStackChanged:            # Update stack pointers if stack has changed
                self.updateStackPointers()
                self.hasStackChanged = False
            
            for indexUpdate in range(len(self.stack) - 1, self.stackLastBackElement - 1, -1):
                self.stack[indexUpdate].update(gameClockDelta)
                self.stackChangePrior = self.hasStackChanged
                self.addToStack(self.stack[indexUpdate].getFutureContext())
                if self.stack[-1] == None:
                    self.stack.pop()
                    if self.stackChangePrior == False:
                        self.hasStackChanged = False
                    else:
                        self.hasStackChanged = True
                if self.stack[indexUpdate].screenStackUpdate:   # Forcefully update stack pointers due to stack workaround
                    self.updateStackPointers()
                    self.stack[indexUpdate].screenStackUpdate = False
                    self.hasStackChanged = False
                if self.stack[indexUpdate].getContextState():   # Stack object has finished operation
                    self.stack.remove(self.stack[indexUpdate])
                    self.hasStackChanged = True

    def handleEvent(self, event):
        for indexUpdate in range(len(self.stack), self.stackLastBlockElement, -1):
            if self.stack[indexUpdate - 1].handleEvent(event):  # Event was absorbed, remove from queue
                break
        return True   

class LaytonSubscreen(LaytonScreen):
    def __init__(self):
        LaytonScreen.__init__(self)
        self.isContextFinished = False
    
    def update(self, gameClockDelta):
        super().update(gameClockDelta)
        self.updateSubscreenMethods(gameClockDelta)
    
    def updateSubscreenMethods(self, gameClockDelta): pass

class AltClock():

    PYGAME_GET_FPS_AVERAGE_CALLS = 10

    def __init__(self):
        self.prevFrame = time.perf_counter()
        self.frameTimeHistory = []

        if coreProp.ENGINE_DEBUG_MODE:
            if coreProp.ENGINE_FORCE_BUSY_WAIT:
                def tick(gameClockInterval):
                    self.frameTimeHistory.append(self.tickAltTimerQuality(gameClockInterval))
                    if len(self.frameTimeHistory) > AltClock.PYGAME_GET_FPS_AVERAGE_CALLS:
                        self.frameTimeHistory = self.frameTimeHistory[-AltClock.PYGAME_GET_FPS_AVERAGE_CALLS:]
                    return self.frameTimeHistory[-1]
            else:
                def tick(gameClockInterval):
                    self.frameTimeHistory.append(self.tickAltTimerPerformance(gameClockInterval))
                    if len(self.frameTimeHistory) > AltClock.PYGAME_GET_FPS_AVERAGE_CALLS:
                        self.frameTimeHistory = self.frameTimeHistory[-AltClock.PYGAME_GET_FPS_AVERAGE_CALLS:]
                    return self.frameTimeHistory[-1]
            self.tick = tick
        else:
            if coreProp.ENGINE_FORCE_BUSY_WAIT:
                self.tick = self.tickAltTimerQuality
            else:
                self.tick = self.tickAltTimerPerformance
    
    def tickAltTimerQuality(self, gameClockInterval):
        lastPrevFrame = self.prevFrame
        while (time.perf_counter() - lastPrevFrame) < gameClockInterval:
            pass
        self.prevFrame = time.perf_counter()
        return (time.perf_counter() - lastPrevFrame) * 1000

    def tickAltTimerPerformance(self, gameClockInterval):
        lastPrevFrame = self.prevFrame
        try:
            time.sleep((gameClockInterval) - (time.perf_counter() - lastPrevFrame))
        except:
            pass
        self.prevFrame = time.perf_counter()
        return (time.perf_counter() - lastPrevFrame) * 1000

    def get_fps(self):
        if len(self.frameTimeHistory) == AltClock.PYGAME_GET_FPS_AVERAGE_CALLS:
            total = 0
            for frameTime in self.frameTimeHistory:
                total += frameTime
            return 1000 / (total / AltClock.PYGAME_GET_FPS_AVERAGE_CALLS)
        return 0

def play(rootHandler, playerState):
    
    isActive = True
    gameDisplay = pygame.display.set_mode((coreAnim.prepareOffset(coreProp.LAYTON_SCREEN_WIDTH), coreAnim.prepareOffset(coreProp.LAYTON_SCREEN_HEIGHT * 2)))
    gameClockDelta = 0
    
    if coreProp.ENGINE_FORCE_USE_ALT_TIMER:
        gameClock = AltClock()
        gameClockInterval = coreProp.ENGINE_FRAME_INTERVAL / 1000
        tick = gameClock.tick
    else:
        gameClock = pygame.time.Clock()
        gameClockInterval = coreProp.ENGINE_FPS
        if coreProp.ENGINE_FORCE_BUSY_WAIT:
            tick = gameClock.tick_busy_loop
        else:
            tick = gameClock.tick

    while isActive:
        
        rootHandler.update(gameClockDelta)
        rootHandler.draw(gameDisplay)

        if coreProp.ENGINE_DEBUG_MODE:
            debugFont = playerState.getFont("fontq")
            debugGameFps = round(gameClock.get_fps(), 2)

            if coreProp.ENGINE_PERFORMANCE_MODE:
                debugFps = coreAnim.AnimatedText(debugFont, initString="FPS: " + str(debugGameFps), colour=(255,0,0))
            else:
                if debugGameFps == coreProp.ENGINE_FPS:
                    perfColour = (0,255,0)
                elif debugGameFps > coreProp.ENGINE_FPS:
                    perfColour = (255,0,255)
                else:
                    debugGameFpsRatio = debugGameFps/coreProp.ENGINE_FPS
                    perfColour = (round((1-debugGameFpsRatio) * 255), round(debugGameFpsRatio * 255), 0)
                debugFps = coreAnim.AnimatedText(debugFont, initString="FPS: " + str(debugGameFps), colour=perfColour)
                debugFpsShadow = pygame.Surface((debugFps.textRender.get_width(), debugFps.textRender.get_height()))
                debugFpsShadow.set_alpha(127)
                gameDisplay.blit(debugFpsShadow, (0,0))

            debugFps.draw(gameDisplay)

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                isActive = False
            else:
                rootHandler.handleEvent(event)
        
        gameClockDelta = tick(gameClockInterval)