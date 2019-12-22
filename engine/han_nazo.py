import pygame, han_nazo_element, scr_hint, conf, state, anim, script, const
from os import path
from math import sqrt
from file import FileInterface
from hat_io import asset_dat

# Testing only
import ctypes; ctypes.windll.user32.SetProcessDPIAware()
pygame.init()

class LaytonContextPuzzlet(state.LaytonContext):
    def __init__(self):
        state.LaytonContext.__init__(self)
        self.registerVictory = False
        self.registerLoss = False
        self.registerQuit = False
    def setVictory(self):
        self.registerVictory = True
        self.registerLoss = False
    def setLoss(self):
        self.registerVictory = False
        self.registerLoss = True
    def getScript(self):
        pass

class LaytonTouchOverlay(state.LaytonContext):

    imageTouchAlphaBounds = (63,248)
    imageTouchAlphaRange = imageTouchAlphaBounds[1] - imageTouchAlphaBounds[0]

    def __init__(self):
        state.LaytonContext.__init__(self)
        self.screenIsOverlay        = True
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False

        self.imageTouch = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "nazo/system/" + conf.LAYTON_ASSET_LANG, "touch")
        self.imageTouch = self.imageTouch.setAnimationFromNameAndReturnInitialFrame("touch")

        self.imageTouchPos = ((conf.LAYTON_SCREEN_WIDTH - self.imageTouch.get_width()) // 2,
                              ((conf.LAYTON_SCREEN_HEIGHT - self.imageTouch.get_height()) // 2) + conf.LAYTON_SCREEN_HEIGHT)
        self.imageTouchAlphaFader = anim.AnimatedFader(5000, anim.AnimatedFader.MODE_SINE_SMOOTH, True, inverted=True)

    def update(self, gameClockDelta):
        self.imageTouchAlphaFader.update(gameClockDelta)
        self.imageTouch.set_alpha(LaytonTouchOverlay.imageTouchAlphaBounds[0] + round(self.imageTouchAlphaFader.getStrength() * LaytonTouchOverlay.imageTouchAlphaRange))

    def draw(self, gameDisplay):
        gameDisplay.blit(self.imageTouch, self.imageTouchPos)

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.isContextFinished = True

class LaytonScrollerOverlay(state.LaytonContext):
    def __init__(self, textPrompt, playerState):
        state.LaytonContext.__init__(self)
        self.transitionsEnableIn = False
        self.transitionsEnableOut = False
        self.screenIsOverlay = True
        self.screenBlockInput = True
        if conf.GRAPHICS_USE_GAME_FONTS:
            self.puzzleQText = anim.TextScroller(playerState.getFont("fontq"), textPrompt, targetFramerate=60, textPosOffset=(11,22))
        else:
            self.puzzleQText = anim.TextScroller(playerState.getFont("fontq"), textPrompt, targetFramerate=60, textPosOffset=(8,22))

    def update(self, gameClockDelta):
        self.puzzleQText.update(gameClockDelta)
    
    def draw(self, gameDisplay):
        self.puzzleQText.draw(gameDisplay)

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.screenBlockInput:
                self.puzzleQText.skip()
                self.screenBlockInput = False
                self.setStackUpdate()
        return False

class LaytonJudgeAnimOverlay(state.LaytonContext):

    FRAMES_ANIM = 4
    FRAMES_HOLD = 36
    FRAMES_CLEAR = 10
    FRAMES_LENGTH = (3,3,3,4)
    INCORRECT_FRAME_INDEX = 2
    INCORRECT_FRAME_OFFSET = 100
    JUDGE_CHAR_MAP = {1:"l", 2:"r"}

    def __init__(self, puzzleData, wasCorrect=True):
        state.LaytonContext.__init__(self)
        self.screenIsOverlay        = False
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False

        self.backgroundFill = pygame.Surface((conf.LAYTON_SCREEN_WIDTH, conf.LAYTON_SCREEN_HEIGHT * 2))

        if puzzleData.idCharacterJudgeAnim in LaytonJudgeAnimOverlay.JUDGE_CHAR_MAP.keys():
            totalIndexFrame = 0
            totalIndexFrameOffset = 0
            tempIndices = []
            tempDuration = []
            self.animFinished = False
            tempFaderDuration = (LaytonJudgeAnimOverlay.FRAMES_HOLD - LaytonJudgeAnimOverlay.FRAMES_CLEAR) * (1000/60) // 2
            self.screenEndAnim = anim.AnimatedImageWithFadeInOutPerAnim(None, None, tempFaderDuration, False, anim.AnimatedFader.MODE_SINE_SHARP, y=conf.LAYTON_SCREEN_HEIGHT, fromImport=False)
            pygame.event.post(pygame.event.Event(const.ENGINE_SKIP_CLOCK, {const.PARAM:None}))

            for indexLenFrame, lenFrame in enumerate(LaytonJudgeAnimOverlay.FRAMES_LENGTH):
                tempIndices = []
                tempDuration = []
                if not(wasCorrect) and indexLenFrame == LaytonJudgeAnimOverlay.INCORRECT_FRAME_INDEX:
                    totalIndexFrameOffset += LaytonJudgeAnimOverlay.INCORRECT_FRAME_OFFSET
                for indexFrame in range(lenFrame):
                    indexFrame += 1
                    tempIndices.append(len(self.screenEndAnim.frames))
                    totalIndexFrame += 1
                    if indexFrame == lenFrame:
                        if indexLenFrame == len(LaytonJudgeAnimOverlay.FRAMES_LENGTH) - 1:
                            tempDuration.append(LaytonJudgeAnimOverlay.FRAMES_HOLD * 2)
                        else:
                            tempDuration.append(LaytonJudgeAnimOverlay.FRAMES_HOLD)
                    else:
                        tempDuration.append(LaytonJudgeAnimOverlay.FRAMES_ANIM)
                    self.screenEndAnim.frames.append(anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "nazo/hantei/judge_" + LaytonJudgeAnimOverlay.JUDGE_CHAR_MAP[puzzleData.idCharacterJudgeAnim] + str(totalIndexFrame + totalIndexFrameOffset) + "_bg.arc"))

                self.screenEndAnim.animMap[str(indexLenFrame)] = anim.AnimatedFrameCollection(tempDuration, indices=tempIndices, loop=False, isFramerateTimeArray=True)
            self.screenEndAnim.setAnimationFromIndex(0)
            self.animActive = 0
        else:
            self.isContextFinished = True
    
    def update(self, gameClockDelta):
        if not(self.animFinished):
            self.screenEndAnim.update(gameClockDelta)
            if not(self.screenEndAnim.getActiveState()):
                self.animActive += 1
                self.animFinished = not(self.screenEndAnim.setAnimationFromIndex(self.animActive))

    def draw(self, gameDisplay):
        gameDisplay.blit(self.backgroundFill, (0,0))
        self.screenEndAnim.draw(gameDisplay)

class LaytonPuzzleUi(LaytonContextPuzzlet):

    buttonHint      = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "system/btn/" + conf.LAYTON_ASSET_LANG, "hint")
    buttonHint.pos  = (conf.LAYTON_SCREEN_WIDTH - buttonHint.dimensions[0], conf.LAYTON_SCREEN_HEIGHT)

    def __init__(self, puzzleData, puzzleIndex, playerState):
        LaytonContextPuzzlet.__init__(self)
        self.screenIsOverlay        = True
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False

        self.puzzleData             = puzzleData
        self.puzzleIndex            = puzzleIndex
        self.playerState            = playerState
        self.puzzleAnimFont         = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "nazo/system/" + conf.LAYTON_ASSET_LANG, "nazo_text")
        self.puzzleIndexText        = '%03d' % puzzleData.idExternal
        self.decayPicarots          = puzzleData.decayPicarots
        
        self.spawnNewButtonHint()
        imageYesButton = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "system/btn/" + conf.LAYTON_ASSET_LANG, "yes")
        imageNoButton = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "system/btn/" + conf.LAYTON_ASSET_LANG, "no")
        imageBackButton = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "system/btn/" + conf.LAYTON_ASSET_LANG, "modoru_memo")
        self.screenHint = scr_hint.Screen(self.puzzleIndex, self.puzzleData, self.playerState, self.puzzleAnimFont, imageYesButton, imageNoButton, imageBackButton)
    
    def spawnNewButtonHint(self):
        self.buttonHintLevel = self.playerState.getPuzzleEntry(self.puzzleIndex).unlockedHintLevel
        self.buttonHint = anim.AnimatedButton(LaytonPuzzleUi.buttonHint.setAnimationFromNameAndReturnInitialFrame(str(self.buttonHintLevel) + "_off"),
                                              LaytonPuzzleUi.buttonHint.setAnimationFromNameAndReturnInitialFrame(str(self.buttonHintLevel) + "_on"),
                                              imageIsSurface=True, x=LaytonPuzzleUi.buttonHint.pos[0], y=LaytonPuzzleUi.buttonHint.pos[1])

    def update(self, gameClockDelta):
        # TODO - Probably just use an event to optimise this
        if self.playerState.getPuzzleEntry(self.puzzleIndex).unlockedHintLevel != self.buttonHintLevel:
            self.spawnNewButtonHint()

    def draw(self, gameDisplay):
        self.buttonHint.draw(gameDisplay)

        def setAnimationFromNameReadyToDraw(name, gameDisplay):
            if self.puzzleAnimFont.setAnimationFromName(name):
                self.puzzleAnimFont.setInitialFrameFromAnimation()
                self.puzzleAnimFont.draw(gameDisplay)

        # TODO - Optimise this to minimise redraw and dynamically implement picarot decay
        self.puzzleAnimFont.pos = (6,4)  # Draw puzzle index text
        setAnimationFromNameReadyToDraw("nazo", gameDisplay)
        self.puzzleAnimFont.pos = (100,4)
        setAnimationFromNameReadyToDraw("pk", gameDisplay)
        self.puzzleAnimFont.pos = (166,4)
        setAnimationFromNameReadyToDraw("hint", gameDisplay)

        for bannerText, xPosInitial in [(self.puzzleIndexText, 27),
                                        (str(self.decayPicarots[0]), 85),
                                        (str(self.decayPicarots[0]), 105),
                                        (format(str(self.playerState.remainingHintCoins), '>3'), 228)]:
            self.puzzleAnimFont.pos = (xPosInitial,5)
            for char in bannerText:
                setAnimationFromNameReadyToDraw(char, gameDisplay)
                self.puzzleAnimFont.pos = (self.puzzleAnimFont.pos[0] + self.puzzleAnimFont.dimensions[0] - 1, self.puzzleAnimFont.pos[1])

    def handleEvent(self, event):
        if not(self.screenBlockInput):
            self.buttonHint.handleEvent(event)
            if self.buttonHint.peekPressedStatus():
                if self.buttonHint.getPressedStatus():
                    self.screenHint.refresh()
                    self.screenNextObject = self.screenHint
                return True
        return False

class LaytonPuzzleBackground(state.LaytonContext):

    def __init__(self, idBackgroundTs, idBackgroundBs):
        state.LaytonContext.__init__(self)
        
        # Set screen variables
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True
        
        if idBackgroundBs == None or idBackgroundTs == None:
            self.backgroundBs, self.backgroundTs = pygame.Surface((0,0)), pygame.Surface((0,0))
        else:
            self.backgroundBs = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "nazo/" + conf.LAYTON_ASSET_LANG + "/q" + str(idBackgroundBs) + ".arc")
            if self.backgroundBs.get_width() == 0:
                self.backgroundBs = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "nazo/" + "q" + str(idBackgroundBs) + ".arc")
                if self.backgroundBs.get_width() == 0:
                    self.backgroundIsLoaded = False
                    self.backgroundBs = pygame.Surface((conf.LAYTON_SCREEN_WIDTH, conf.LAYTON_SCREEN_HEIGHT))
                    self.backgroundBs.fill(conf.GRAPHICS_FONT_COLOR_MAP['g'])
            self.backgroundTs = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "nazo\\system\\nazo_text" + str(idBackgroundTs) + ".arc")

    def draw(self, gameDisplay):
        gameDisplay.blit(self.backgroundTs, (0,0))
        gameDisplay.blit(self.backgroundBs, (0,conf.LAYTON_SCREEN_HEIGHT))

class PuzzletTileRotate(LaytonContextPuzzlet):

    DEBUG_SHOW_ANSWER = False

    def __init__(self, puzzleData, puzzleIndex, playerState):
        LaytonContextPuzzlet.__init__(self)

        self.puzzleIndex = puzzleIndex
    
        self.tiles = []
        self.locations = []
        self.tempTileIndex = 0

        self.oldVerWorkaroundEncountered = False
    
    def draw(self, gameDisplay):
        for tile in self.tiles:
            tile.draw(gameDisplay)
    
    def update(self, gameClockDelta):
        for tile in self.tiles:
            tile.update(gameClockDelta)

    def executeCommand(self, command):
        if command.opcode == b'\x54':   # Fetch tile
            # TODO - Unify .spr removal
            self.tiles.append(han_nazo_element.IndependentTileRotateable(anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "nazo/tilerotate", command.operands[0][0:-4]),
                                                                         "0", 0))
        elif command.opcode == b'\x55': # Fetch location
            self.locations.append((command.operands[0], command.operands[1] + conf.LAYTON_SCREEN_HEIGHT))
        elif command.opcode == b'\x58': # Set answer
            if PuzzletTileRotate.DEBUG_SHOW_ANSWER:
                self.tiles[self.tempTileIndex].sourcePos = self.locations[command.operands[0]]
                self.tiles[self.tempTileIndex].reset()
                self.tiles[self.tempTileIndex].setRot(command.operands[1] * 90)            
            else:
                self.tiles[self.tempTileIndex].sourcePos = self.locations[command.operands[6]]
                self.tiles[self.tempTileIndex].reset()
                self.tiles[self.tempTileIndex].setRot(command.operands[7] * 90)
            self.tempTileIndex += 1

        elif command.opcode == b'\x5b': # Alternative answer opcode? Investigation required
            if PuzzletTileRotate.DEBUG_SHOW_ANSWER:
                if not(self.oldVerWorkaroundEncountered) and self.tempTileIndex > 0:
                    self.tempTileIndex = 0
                    self.oldVerWorkaroundEncountered = True
                    state.debugPrint("WarnTileRotate: Handler version workaround hit!")

                self.tiles[command.operands[0]].sourcePos = self.locations[command.operands[1]]
                self.tiles[self.tempTileIndex].reset()
                self.tiles[command.operands[0]].setRot(command.operands[2] * 90)
                self.tempTileIndex += 1
        else:
            state.debugPrint("ErrTileRotateUnkCommand:", command.opcode)

class PuzzletTraceButton(LaytonContextPuzzlet):

    promptRetry         = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "nazo/tracebutton/" + conf.LAYTON_ASSET_LANG, "retry_trace")
    promptRetry         = anim.StaticImage(promptRetry.setAnimationFromNameAndReturnInitialFrame("gfx"), imageIsSurface=True)
    promptRetry.pos     = ((conf.LAYTON_SCREEN_WIDTH - promptRetry.image.get_width()) // 2, ((conf.LAYTON_SCREEN_HEIGHT - promptRetry.image.get_height()) // 2) + conf.LAYTON_SCREEN_HEIGHT)
    
    promptPoint         = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "nazo/tracebutton", "point_trace")
    promptPoint.setActiveFrame(0)

    promptArrowLeft     = anim.AnimatedButton(anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "nazo/tracebutton", "arrow_left"), None,
                                              imageIsSurface=True, useButtonFromAnim=True, x=2, y=conf.LAYTON_SCREEN_HEIGHT)
    promptArrowRight    = anim.AnimatedButton(anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "nazo/tracebutton", "arrow_right"), None,
                                              imageIsSurface=True, useButtonFromAnim=True, x=158, y=conf.LAYTON_SCREEN_HEIGHT)
    
    buttonSubmit        = anim.AnimatedButton(anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "system/btn/" + conf.LAYTON_ASSET_LANG, "hantei"), None,
                                              imageIsSurface=True, useButtonFromAnim=True)
    buttonSubmit.setPos((conf.LAYTON_SCREEN_WIDTH - buttonSubmit.dimensions[0], (conf.LAYTON_SCREEN_HEIGHT * 2) - buttonSubmit.dimensions[1]))

    TRACE_LINE_THICKNESS = 3
    TRACE_X_LIMIT = conf.LAYTON_SCREEN_WIDTH - (buttonSubmit.dimensions[0] + TRACE_LINE_THICKNESS)

    def __init__(self, puzzleData, puzzleIndex, playerState):
        LaytonContextPuzzlet.__init__(self)
        self.puzzleIndex = puzzleIndex
        
        self.cursorEnableSoftlockRetryScreen = True
        self.cursorIsDrawing = False
        self.cursorColour = pygame.Color(255,0,0)
        self.cursorLineSurface = pygame.Surface((conf.LAYTON_SCREEN_WIDTH, conf.LAYTON_SCREEN_HEIGHT))
        self.cursorLineSurface.set_colorkey(pygame.Color(0,0,0))

        self.cursorSelectedItem = None
        self.cursorPoints = []
        self.cursorTotalPoints = [0,0]
        self.cursorTotalPointsLength = 0

        self.traceLocationsDict = {0:[]}

        self.countAdditionalTiles = 0
        self.traceLocationIndexingEnable = False
        self.indexAdditionalTiles = 0
        self.traceAdditionalTiles = []
    
    def cursorAddPoint(self, point):
        tempPointX = point[0]
        tempPointY = point[1]
        if tempPointX < PuzzletTraceButton.TRACE_LINE_THICKNESS // 2:
            tempPointX = PuzzletTraceButton.TRACE_LINE_THICKNESS // 2
        if tempPointY < conf.LAYTON_SCREEN_HEIGHT:
            tempPointY = conf.LAYTON_SCREEN_HEIGHT
        if tempPointX > PuzzletTraceButton.TRACE_X_LIMIT:
            tempPointX = PuzzletTraceButton.TRACE_X_LIMIT
        tempPointY -= conf.LAYTON_SCREEN_HEIGHT
        self.cursorPoints.append((tempPointX, tempPointY))
        self.cursorTotalPoints[0] += point[0]
        self.cursorTotalPoints[1] += point[1]
        self.cursorTotalPointsLength += 1

    def executeCommand(self, command):
        if command.opcode == b'\x0c':
            self.cursorColour = pygame.Color(command.operands[0],command.operands[1],command.operands[2])
        elif command.opcode == b'\x18':
            self.traceLocationsDict[self.countAdditionalTiles].append(han_nazo_element.TraceLocation(command.operands[0], command.operands[1] + conf.LAYTON_SCREEN_HEIGHT,
                                                                      command.operands[2], conf.LAYTON_STRING_BOOLEAN[command.operands[3]]))
        elif command.opcode == b'\x3e':
            self.traceLocationIndexingEnable = True
            self.countAdditionalTiles += 1
            self.traceLocationsDict[self.countAdditionalTiles] = []
            self.traceAdditionalTiles.append(anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "nazo/q" + str(self.puzzleIndex) + "_" + str(self.countAdditionalTiles) + ".arc"))
        else:
            state.debugPrint("ErrTraceButtonUnkCommand: " + str(command.opcode))
    
    def update(self, gameClockDelta):
        if len(self.cursorPoints) >= 2:
            pygame.draw.lines(self.cursorLineSurface, self.cursorColour, True, self.cursorPoints, PuzzletTraceButton.TRACE_LINE_THICKNESS)
            self.cursorPoints = [self.cursorPoints[-1]]
            return True
        return False
    
    def findSelectedItem(self):
        if self.cursorTotalPointsLength >= 1:
            traceSelectedLocation = (self.cursorTotalPoints[0] // self.cursorTotalPointsLength, self.cursorTotalPoints[1] // self.cursorTotalPointsLength)
            for locationIndex in range(len(self.traceLocationsDict[self.indexAdditionalTiles])):
                if self.traceLocationsDict[self.indexAdditionalTiles][locationIndex].wasClicked(traceSelectedLocation):    # For extremely dense items, this may need to be checked across several indices for closest
                    return locationIndex
        return None

    def evaluateSolution(self):
        if self.cursorSelectedItem != None:
            if self.traceLocationsDict[self.indexAdditionalTiles][self.cursorSelectedItem].isAnswer:
                return True
        return False

    def draw(self, gameDisplay):
        if self.traceLocationIndexingEnable and self.indexAdditionalTiles > 0:
            gameDisplay.blit(self.traceAdditionalTiles[self.indexAdditionalTiles - 1], (0, conf.LAYTON_SCREEN_HEIGHT))

        gameDisplay.blit(self.cursorLineSurface, (0, conf.LAYTON_SCREEN_HEIGHT))
        
        if not(self.cursorIsDrawing):
            if self.cursorSelectedItem == None:
                if self.cursorEnableSoftlockRetryScreen and self.cursorTotalPointsLength > 0:
                    PuzzletTraceButton.promptRetry.draw(gameDisplay)
            else:
                PuzzletTraceButton.promptPoint.draw(gameDisplay)
        
        if self.traceLocationIndexingEnable:
            PuzzletTraceButton.promptArrowLeft.draw(gameDisplay)
            PuzzletTraceButton.promptArrowRight.draw(gameDisplay)
        PuzzletTraceButton.buttonSubmit.draw(gameDisplay)

    def clear(self):
        self.cursorSelectedItem = None
        self.cursorPoints = []
        self.cursorTotalPoints = [0,0]
        self.cursorTotalPointsLength = 0
        self.cursorLineSurface.fill((0,0,0))

    def handleEvent(self, event):
        if self.traceLocationIndexingEnable:
            PuzzletTraceButton.promptArrowLeft.handleEvent(event)
            if PuzzletTraceButton.promptArrowLeft.peekPressedStatus():
                if PuzzletTraceButton.promptArrowLeft.getPressedStatus():
                    self.clear()
                    if self.indexAdditionalTiles <= 0:
                        self.indexAdditionalTiles = self.countAdditionalTiles
                    else:
                        self.indexAdditionalTiles -= 1
                return True

            PuzzletTraceButton.promptArrowRight.handleEvent(event)
            if PuzzletTraceButton.promptArrowRight.peekPressedStatus():
                if PuzzletTraceButton.promptArrowRight.getPressedStatus():
                    self.clear()
                    if self.indexAdditionalTiles >= self.countAdditionalTiles:
                        self.indexAdditionalTiles = 0
                    else:
                        self.indexAdditionalTiles += 1
                return True

        PuzzletTraceButton.buttonSubmit.handleEvent(event)
        if PuzzletTraceButton.buttonSubmit.peekPressedStatus():
            if PuzzletTraceButton.buttonSubmit.getPressedStatus():
                if self.evaluateSolution():
                    self.setVictory()
                else:
                    self.setLoss()
            return True

        if event.type == pygame.MOUSEBUTTONDOWN  and event.pos[1] >= conf.LAYTON_SCREEN_HEIGHT:
            if self.buttonSubmit.wasClicked(event.pos):
                if self.evaluateSolution():
                    self.setVictory()
                else:
                    self.setLoss()
            elif not(self.cursorIsDrawing):
                self.cursorIsDrawing = True
                self.cursorTotalPoints = [0,0]
                self.cursorTotalPointsLength = 0
                self.cursorLineSurface.fill((0,0,0))
                self.cursorAddPoint((event.pos[0], event.pos[1]))

        elif event.type == pygame.MOUSEMOTION:
            if self.cursorIsDrawing:
                self.cursorAddPoint((event.pos[0], event.pos[1]))

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.cursorIsDrawing:
                self.cursorSelectedItem = self.findSelectedItem()
                if self.cursorSelectedItem != None:
                    PuzzletTraceButton.promptPoint.pos = (self.traceLocationsDict[self.indexAdditionalTiles][self.cursorSelectedItem].pos[0],
                                                          self.traceLocationsDict[self.indexAdditionalTiles][self.cursorSelectedItem].pos[1] - PuzzletTraceButton.promptPoint.dimensions[1])
                self.cursorIsDrawing = False
                self.cursorPoints = []
        return False

class LaytonPuzzleHandler(state.LaytonSubscreen):

    # defaultHandlers = {0: 'Matchstick', 1: 'Sliding', 2: 'Multiple Choice', 3: 'Mark Answer',
    #                    4: 'Position to Solve  (NOT IN USe)', 5: 'Circle Answer', 6: 'Draw Line', 7: 'Connect to Answer (NOT IN USE)',
    #                    8: 'Cups (NOT IN USE)', 9: 'Draw Line', 10: 'Sort', 11: 'Arrange to Answer', 12: 'Rotate and Arrange',
    #                    13: 'Move to Answer', 14: 'Tap to Answer', 15: 'Draw Line', 16: 'Write Answer', 17: 'Move Knight',
    #                    18: 'Rotate and Arrange', 19: 'Position to Solve  (NOT IN USE)', 20: '文字入力問題', 21: '文字入力問題',
    #                    22: 'Write Answer', 23: 'Area', 24: 'Rose Placement', 25: 'Sliding', 26: 'Arrange to Answer', 27: 'Skate to Exit',
    #                    28: 'Write Answer', 29: 'Remove Balls', 30: 'Move in Pairs', 31: 'Lamp Placement', 32: 'Write Answer',
    #                    33: 'Cross Bridge', 34: 'Shape Search'}

    # Taken from jiten.plz (Naming scheme for handlers; handlers are also derived from the parameter grabbing this)
    # 22 unique handlers
    defaultHandlers = {0: 'Matchstick', 2: 'Multiple Choice', 3: 'Mark Answer',

                       5: PuzzletTraceButton,

                       10: 'Sort', 13: 'Move to Answer',
                       14: 'Tap to Answer', 15: 'Draw Line', 17: 'Move Knight', 23: 'Area', 24: 'Rose Placement', 27: 'Skate to Exit',
                       29: 'Remove Balls', 30: 'Move in Pairs', 31: 'Lamp Placement', 33: 'Cross Bridge', 34: 'Shape Search', 35:'Placement',

                       12: PuzzletTileRotate, 18: PuzzletTileRotate,

                       16: 'Write Answer', 22: 'Write Answer', 28: 'Write Answer', 32: 'Write Answer', 
                       1: 'Sliding', 25: 'Sliding', 
                       26: 'Arrange to Answer', 11: 'Arrange to Answer',
                       6: 'Draw Line', 9: 'Draw Line'}

    def __init__(self, puzzleIndex, playerState):
        state.LaytonSubscreen.__init__(self)
        self.transitionsEnableIn = False
        self.transitionsEnableOut = False
        self.screenBlockInput = True
        
        self.commandFocus = None
        self.puzzleIndex = puzzleIndex
        puzzleDataIndex = (puzzleIndex // 60) + 1
        puzzleScript    = script.gdScript(FileInterface.getPackedData(FileInterface.PATH_ASSET_SCRIPT + "puzzle.plz",
                                                      "q" + str(puzzleIndex) + "_param.gds", version = 1), None)
        self.puzzleData = asset_dat.LaytonPuzzleData()
        self.puzzleData.load(FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "nazo/" + conf.LAYTON_ASSET_LANG + "/nazo" + str(puzzleDataIndex) + ".plz",
                                                    "n" + str(puzzleIndex) + ".dat", version = 1))
        self.addToStack(LaytonPuzzleBackground(self.puzzleData.idBackgroundTs, self.puzzleData.idBackgroundBs))
        
        if type(LaytonPuzzleHandler.defaultHandlers[self.puzzleData.idHandler]) != str:
            self.addToStack(LaytonPuzzleHandler.defaultHandlers[self.puzzleData.idHandler](self.puzzleData, puzzleIndex, playerState))
            self.commandFocus = self.stack[-1]
            self.executeGdScript(puzzleScript)
        else:
            state.debugPrint("WarnUnknownHandler:", self.puzzleData.idHandler, LaytonPuzzleHandler.defaultHandlers[self.puzzleData.idHandler])

        self.addToStack(LaytonScrollerOverlay(self.puzzleData.textPrompt, playerState))
        self.addToStack(LaytonPuzzleUi(self.puzzleData, puzzleIndex, playerState))
        self.addToStack(LaytonTouchOverlay())
        pygame.event.post(pygame.event.Event(const.ENGINE_SKIP_CLOCK, {const.PARAM:None}))

    def executeGdScript(self, puzzleScript):
        for command in puzzleScript.commands:
            if self.commandFocus != None:
                self.commandFocus.executeCommand(command)
    
    def updateSubscreenMethods(self, gameClockDelta):
        if self.commandFocus != None:
            if self.commandFocus.registerVictory:
                self.commandFocus.registerVictory = False
                self.addToStack(LaytonJudgeAnimOverlay(self.puzzleData, wasCorrect=True))
                self.isContextFinished = True
            elif self.commandFocus.registerLoss:
                self.commandFocus.registerLoss = False
                self.addToStack(LaytonJudgeAnimOverlay(self.puzzleData, wasCorrect=False))
            elif self.commandFocus.registerQuit:
                self.isContextFinished = True

if __name__ == '__main__':
    tempPlayerState = state.LaytonPlayerState()
    tempPlayerState.remainingHintCoins = 100
    state.play(LaytonPuzzleHandler(6, tempPlayerState), tempPlayerState)    # 3 - Multiroom tracebutton, 6 - single tracebutton
    # 2, 39, 115 Rotate and arrange