import pygame, han_nazo_element, scr_hint, conf, state, anim, script, const
from os import path
from math import sqrt, atan2, pi
from file import FileInterface
from hat_io import asset_dat

# Testing only
import ctypes; ctypes.windll.user32.SetProcessDPIAware()
pygame.init()

class LaytonContextPuzzlet(state.LaytonContext):
    def __init__(self):
        state.LaytonContext.__init__(self)
        self.transitionsEnableIn = False
        self.transitionsEnableOut = False
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
                return True
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

class PuzzletPushButton(LaytonContextPuzzlet):

    def __init__(self, puzzleData, puzzleIndex, playerState):
        LaytonContextPuzzlet.__init__(self)
        self.interactableElements = []
        self.drawFlagsInteractableElements = []
        self.solutionElements = []
    
    def addPushButton(self, imageName, cornerPos):
        self.interactableElements.append(anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "nazo/freebutton", imageName, x=cornerPos[0], y=cornerPos[1]))

    def executeCommand(self, command):
        if command.opcode == b'\x14':
            imageName = command.operands[2]
            if imageName[-4:] == ".spr":
                imageName = imageName[0:-4]

            if command.operands[3]:
                self.solutionElements.append(len(self.interactableElements))
            
            self.addPushButton(imageName, (command.operands[0], command.operands[1] + conf.LAYTON_SCREEN_HEIGHT))
            self.interactableElements[-1].setActiveFrame(command.operands[4])
            self.drawFlagsInteractableElements.append(False)
        else:
            super().executeCommand(command)
    
    def draw(self, gameDisplay):
        for elementIndex in range(len(self.interactableElements)):
            if self.drawFlagsInteractableElements[elementIndex]:
                self.interactableElements[elementIndex].draw(gameDisplay)

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for elementIndex in range(len(self.interactableElements)):
                if self.interactableElements[elementIndex].wasClicked(event.pos):
                    self.drawFlagsInteractableElements[elementIndex] = True

        elif event.type == pygame.MOUSEMOTION:
            for elementIndex in range(len(self.interactableElements)):
                if self.drawFlagsInteractableElements[elementIndex]:
                    if not(self.interactableElements[elementIndex].wasClicked(event.pos)):
                        self.drawFlagsInteractableElements[elementIndex] = False

        elif event.type == pygame.MOUSEBUTTONUP:
            for elementIndex in range(len(self.interactableElements)):
                if self.drawFlagsInteractableElements[elementIndex] == 1:
                    if elementIndex in self.solutionElements:
                        self.setVictory()
                    else:
                        self.setLoss()
                self.drawFlagsInteractableElements[elementIndex] = False

class PuzzletOnOff(PuzzletPushButton):

    # TODO - Change everything to use buttons for easier input code
    # TODO - Test if animations can work on buttons (pre-applied at loading?)

    buttonSubmit        = anim.AnimatedButton(anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "system/btn/" + conf.LAYTON_ASSET_LANG, "hantei"), None,
                                              imageIsSurface=True, useButtonFromAnim=True)
    buttonSubmit.setPos((conf.LAYTON_SCREEN_WIDTH - buttonSubmit.dimensions[0], (conf.LAYTON_SCREEN_HEIGHT * 2) - buttonSubmit.dimensions[1]))

    def __init__(self, puzzleData, puzzleIndex, playerState):
        PuzzletPushButton.__init__(self, puzzleData, puzzleIndex, playerState)
    
    def addPushButton(self, imageName, cornerPos):
        self.interactableElements.append(anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "nazo/onoff", imageName, x=cornerPos[0], y=cornerPos[1]))
    
    def draw(self, gameDisplay):
        super().draw(gameDisplay)
        PuzzletOnOff.buttonSubmit.draw(gameDisplay)
    
    def handleEvent(self, event):
        PuzzletOnOff.buttonSubmit.handleEvent(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            for elementIndex in range(len(self.interactableElements)):
                if self.interactableElements[elementIndex].wasClicked(event.pos):
                    self.drawFlagsInteractableElements[elementIndex] = not(self.drawFlagsInteractableElements[elementIndex])
                    return True
            
        if PuzzletOnOff.buttonSubmit.peekPressedStatus():
            if PuzzletOnOff.buttonSubmit.getPressedStatus():
                isSolved = True
                for elementIndex in range(len(self.drawFlagsInteractableElements)):
                    if self.drawFlagsInteractableElements[elementIndex] and elementIndex not in self.solutionElements:
                        isSolved = False
                        break
                if isSolved:
                    self.setVictory()
                else:
                    self.setLoss()
            return True
        return False

# TODO - Unify solution button using events
class PuzzletCut(LaytonContextPuzzlet):

    # TODO - Fix functionality to make the line follow the cursor properly
    # This makes the puzzles playable, but not in the same way as the game

    RADIUS_TAP = 10
    WIDTH_LINE = 2
    buttonSubmit        = anim.AnimatedButton(anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "system/btn/" + conf.LAYTON_ASSET_LANG, "hantei"), None,
                                              imageIsSurface=True, useButtonFromAnim=True)
    buttonSubmit.setPos((conf.LAYTON_SCREEN_WIDTH - buttonSubmit.dimensions[0], (conf.LAYTON_SCREEN_HEIGHT * 2) - buttonSubmit.dimensions[1]))

    def __init__(self, puzzleData, puzzleIndex, playerState):
        LaytonContextPuzzlet.__init__(self)
        self.colourLine = pygame.Color(255,0,0)
        self.posCorner = (0,0)
        self.posMultiplier = 2
        self.cursorLineSurface = pygame.Surface((conf.LAYTON_SCREEN_WIDTH, conf.LAYTON_SCREEN_HEIGHT))
        self.cursorLineSurface.set_colorkey(pygame.Color(0,0,0))
        self.nodes = []
        self.nodesPairs = []
        self.nodesSolutionPairs = []
        self.nodeInitial = None
    
    def draw(self, gameDisplay):
        gameDisplay.blit(self.cursorLineSurface, (0, conf.LAYTON_SCREEN_HEIGHT))
        if self.nodeInitial != None:
            tempNodeRemapPos = (self.nodes[self.nodeInitial][0], self.nodes[self.nodeInitial][1] + conf.LAYTON_SCREEN_HEIGHT)
            pygame.draw.line(gameDisplay, self.colourLine, tempNodeRemapPos, pygame.mouse.get_pos(), width = 2)
        PuzzletCut.buttonSubmit.draw(gameDisplay)

    def getPressedNode(self, pos):
        pos = (pos[0], pos[1] - conf.LAYTON_SCREEN_HEIGHT)
        for indexNode, node in enumerate(self.nodes):
            if sqrt((node[0] - pos[0]) ** 2  + (node[1] - pos[1]) ** 2) < PuzzletCut.RADIUS_TAP:
                return indexNode
        return None

    def redrawLineSurface(self):
        self.cursorLineSurface.fill((0,0,0))
        for nodeStart, nodeEnd in self.nodesPairs:
            pygame.draw.line(self.cursorLineSurface, self.colourLine, self.nodes[nodeStart], self.nodes[nodeEnd], width = 2)

    def evaluateSolution(self):
        if len(self.nodesPairs) == len(self.nodesSolutionPairs):
            for startNode, endNode in self.nodesPairs:
                if (startNode, endNode) not in self.nodesSolutionPairs and (endNode, startNode) not in self.nodesSolutionPairs:
                    return False
            return True
        return False

    def handleEvent(self, event):
        PuzzletCut.buttonSubmit.handleEvent(event)
        if PuzzletCut.buttonSubmit.peekPressedStatus():
            if PuzzletCut.buttonSubmit.getPressedStatus():
                if self.evaluateSolution():
                    self.setVictory()
                else:
                    self.setLoss()
            return True
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.nodeInitial = self.getPressedNode(event.pos)
            if self.nodeInitial != None:
                return True
        elif event.type == pygame.MOUSEBUTTONUP and self.nodeInitial != None:
            tempPressedNode = self.getPressedNode(event.pos)
            if tempPressedNode != None:
                if tempPressedNode != self.nodeInitial:
                    pair = (self.nodeInitial, tempPressedNode)
                    if pair not in self.nodesPairs and (pair[1], pair[0]) not in self.nodesPairs:
                        self.nodesPairs.append((self.nodeInitial, tempPressedNode))
                        self.redrawLineSurface()
            self.nodeInitial = None
            if tempPressedNode != None:
                return True
        return False

    def executeCommand(self, command):
        if command.opcode == b'\x24':   # Set line colour
            self.colourLine = pygame.Color(command.operands[0],command.operands[1],command.operands[2])
        elif command.opcode == b'\x28': # Add point
            if (self.posCorner[0] + command.operands[0] * self.posMultiplier, (command.operands[1] * self.posMultiplier) + self.posCorner[1]) not in self.nodes:
                self.nodes.append((self.posCorner[0] + command.operands[0] * self.posMultiplier, (command.operands[1] * self.posMultiplier) + self.posCorner[1]))
        elif command.opcode == b'\x29': # Add correct line
            # TODO - Assumes this is always after nodes to create mapping. Is this always the case? Can it be valid otherwise? Testing required.
            try:
                self.nodesSolutionPairs.append((self.nodes.index((self.posCorner[0] + command.operands[0] * self.posMultiplier, (command.operands[1] * self.posMultiplier) + self.posCorner[1])),
                                                self.nodes.index((self.posCorner[0] + command.operands[2] * self.posMultiplier, (command.operands[3] * self.posMultiplier) + self.posCorner[1]))))
            except ValueError:
                state.debugPrint("ErrPuzzletCut: Solution connection has no valid index!")
        elif command.opcode == b'\x10':
            self.posCorner = (command.operands[0],command.operands[1])
        else:
            super().executeCommand(command)
    
class PuzzletSliding(LaytonContextPuzzlet):

    DIRECTION_UP = 0
    DIRECTION_DOWN = 1
    DIRECTION_LEFT = 2
    DIRECTION_RIGHT = 3

    MOVE_COUNTER_POS = (112, 11 + conf.LAYTON_SCREEN_HEIGHT)

    def __init__(self, puzzleData, puzzleIndex, playerState):
        LaytonContextPuzzlet.__init__(self)
        self.posCorner = (0,0)
        self.tileBoardDimensions = (0,0)
        self.tileSize = (0,0)
        self.tileMap = None

        # Debug - shows level collision
        self.cursorLineSurface = pygame.Surface((conf.LAYTON_SCREEN_WIDTH, conf.LAYTON_SCREEN_HEIGHT))
        self.cursorLineSurface.set_colorkey(pygame.Color(0,0,0))

        self.countMoveFont         = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "nazo/common", "counter_number")
        self.countMoves = 0

        self.shapes = []

        self.tileSolution = {}   # index: (tileX, tileY)
        self.tileInternalToMoveableIndexMap = {}    # Locked shapes can bloat the map, causing answers to stop aligning
        self.tileMoveableIndex = 0

        self.activeTile = None
        self.activeTileMouseGrabOffset = (0,0)
        self.activeTileLastMousePos = None

        self.activeTileCurrentMouseDirection = None
        self.directionRequiresChanging = False
        self.directionNextDirection = None
        
        self.activeTileTempPlace = (0,0)
        self.activeTileTempOffset = (0,0)
        self.activeTileMovementPossibilities = None # L,R,U,D

    def shapeSpaceToScreenSpace(self, shape):
        return (self.posCorner[0] + shape.cornerTilePos[0] * self.tileSize[0],
                self.posCorner[1] + conf.LAYTON_SCREEN_HEIGHT + shape.cornerTilePos[1] * self.tileSize[1])

    def draw(self, gameDisplay):
        #gameDisplay.blit(self.cursorLineSurface, (0, conf.LAYTON_SCREEN_HEIGHT))

        def setAnimationFromNameReadyToDraw(name, gameDisplay):
            if self.countMoveFont.setAnimationFromName(name):
                self.countMoveFont.setInitialFrameFromAnimation()
                self.countMoveFont.draw(gameDisplay)
        
        self.countMoveFont.pos = PuzzletSliding.MOVE_COUNTER_POS
        for char in str('%04d' % self.countMoves):
            setAnimationFromNameReadyToDraw(char, gameDisplay)
            self.countMoveFont.pos = (self.countMoveFont.pos[0] + self.countMoveFont.dimensions[0] - 1, self.countMoveFont.pos[1])

        if self.activeTileTempPlace != (0,0):
            for shapeIndex, shape in enumerate(self.shapes):
                if shape.image != None and shapeIndex != self.activeTile:
                    gameDisplay.blit(shape.image, self.shapeSpaceToScreenSpace(shape))

            if self.activeTile != None and self.shapes[self.activeTile].image != None:
                gameDisplay.blit(self.shapes[self.activeTile].image, self.activeTileTempPlace)
        else:
            for shapeIndex, shape in enumerate(self.shapes):
                if shape.image != None:
                    gameDisplay.blit(shape.image, self.shapeSpaceToScreenSpace(shape))

    def reset(self):
        self.countMoves = 0
        for shape in self.shapes:
            shape.reset()

    def update(self, gameClockDelta):

        def snapTileWherePossible():
            if self.activeTileCurrentMouseDirection == PuzzletSliding.DIRECTION_UP and self.activeTileMovementPossibilities[2] > 0:
                deltaYPixels =  self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1] + self.activeTileMouseGrabOffset[1] - self.activeTileLastMousePos[1]
                deltaYTiles = round(deltaYPixels / self.tileSize[1])
                if deltaYPixels > 0:
                    if deltaYPixels > self.activeTileMovementPossibilities[2] * self.tileSize[1]: # Beyond screen space
                        deltaYTiles = self.activeTileMovementPossibilities[2]
                        self.activeTileTempPlace = (self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0],
                                                    self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1] - deltaYTiles * self.tileSize[1])
                    else:
                        self.activeTileTempPlace = (self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0],
                                                    self.activeTileLastMousePos[1] - self.activeTileMouseGrabOffset[1])
                    self.activeTileTempOffset = (0, - deltaYTiles)

            elif self.activeTileCurrentMouseDirection == PuzzletSliding.DIRECTION_DOWN and self.activeTileMovementPossibilities[3] > 0:
                deltaYPixels = self.activeTileLastMousePos[1] - self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1]
                deltaYTiles = round(deltaYPixels / self.tileSize[1])
                if deltaYPixels > 0:
                    if deltaYPixels > self.activeTileMovementPossibilities[3] * self.tileSize[1]:
                        deltaYTiles = self.activeTileMovementPossibilities[3]
                        self.activeTileTempPlace = (self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0],
                                                    self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1] + deltaYTiles * self.tileSize[1])
                    else:
                        self.activeTileTempPlace = (self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0],
                                                    self.activeTileLastMousePos[1] - self.activeTileMouseGrabOffset[1])
                    self.activeTileTempOffset = (0, deltaYTiles)

            elif self.activeTileCurrentMouseDirection == PuzzletSliding.DIRECTION_LEFT and self.activeTileMovementPossibilities[0] > 0:
                deltaXPixels = self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0] - self.activeTileLastMousePos[0] + self.activeTileMouseGrabOffset[0]
                deltaXTiles = round(deltaXPixels / self.tileSize[0])
                if deltaXPixels > 0:
                    if deltaXPixels > self.activeTileMovementPossibilities[0] * self.tileSize[0]:
                        deltaXTiles = self.activeTileMovementPossibilities[0]
                        self.activeTileTempPlace = (self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0] - deltaXTiles * self.tileSize[0],
                                                    self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1])
                    else:
                        self.activeTileTempPlace = (self.activeTileLastMousePos[0] - self.activeTileMouseGrabOffset[0],
                                                    self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1])
                    self.activeTileTempOffset = (- deltaXTiles, 0)

            elif self.activeTileCurrentMouseDirection == PuzzletSliding.DIRECTION_RIGHT and self.activeTileMovementPossibilities[1] > 0:
                deltaXPixels = self.activeTileLastMousePos[0] - self.activeTileMouseGrabOffset[0] - self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0]
                deltaXTiles = round(deltaXPixels / self.tileSize[0])
                if deltaXPixels > 0:
                    if deltaXPixels > self.activeTileMovementPossibilities[1] * self.tileSize[0]:
                        deltaXTiles = self.activeTileMovementPossibilities[1]
                        self.activeTileTempPlace = (self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[0] + deltaXTiles * self.tileSize[0],
                                                    self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1])
                    else:
                        self.activeTileTempPlace = (self.activeTileLastMousePos[0] - self.activeTileMouseGrabOffset[0],
                                                    self.shapeSpaceToScreenSpace(self.shapes[self.activeTile])[1])
                    self.activeTileTempOffset = (deltaXTiles, 0)
                
        if self.activeTileCurrentMouseDirection == None:
            self.activeTileCurrentMouseDirection = self.directionNextDirection

        if self.activeTile != None and self.activeTileCurrentMouseDirection != None: # Tile currently being held and has direction
            # First, attempt to move towards new solution
            snapTileWherePossible()
            
            if self.directionRequiresChanging and self.activeTileCurrentMouseDirection != self.directionNextDirection:
                self.applyShapeOffset(self.shapes[self.activeTile])
                self.activeTileMovementPossibilities = self.getMovementOpportunities(self.shapes[self.activeTile])
                self.activeTileCurrentMouseDirection = self.directionNextDirection
                self.directionRequiresChanging = False
            
            # Attempt to move towards new solution
            snapTileWherePossible()

    def applyShapeOffset(self, shape):
        shape.cornerTilePos = (shape.cornerTilePos[0] + self.activeTileTempOffset[0], shape.cornerTilePos[1] + self.activeTileTempOffset[1])
        self.activeTileTempOffset = (0,0)

    def evaluateSolution(self):
        for tileIndex in self.tileSolution.keys():
            if self.shapes[self.tileInternalToMoveableIndexMap[tileIndex]].cornerTilePos != self.tileSolution[tileIndex]:
                return False
        return True

    def executeCommand(self, command):
        if command.opcode == b'\x4e':
            self.posCorner = (command.operands[0], command.operands[1])
            self.tileBoardDimensions = (command.operands[2], command.operands[3])
            self.tileSize = (command.operands[4], command.operands[5])
            for x in range(self.tileBoardDimensions[0] + 1):
                pygame.draw.line(self.cursorLineSurface, (255,255,255), (self.posCorner[0], self.posCorner[1] + self.tileSize[1] * x),
                                                                        (self.posCorner[0] + self.tileBoardDimensions[0] * self.tileSize[0], self.posCorner[1] + self.tileSize[1] * x), width=1)
            for y in range(self.tileBoardDimensions[1] + 1):
                pygame.draw.line(self.cursorLineSurface, (255,255,255), (self.posCorner[0] + self.tileSize[0] * y, self.posCorner[1]),
                                                                        (self.posCorner[0] + self.tileSize[0] * y, self.posCorner[1] + self.tileBoardDimensions[1] * self.tileSize[1]), width=1)
        elif command.opcode == b'\x4f': # Add occlusion
            rectOcclusion = pygame.Rect(self.posCorner[0] + command.operands[0] * self.tileSize[0], self.posCorner[1] + command.operands[1] * self.tileSize[1],
                                        self.tileSize[0] * command.operands[2], self.tileSize[1] * command.operands[3])
            pygame.draw.rect(self.cursorLineSurface, (255,0,255), rectOcclusion)
            self.shapes.append(han_nazo_element.SlidingShape((command.operands[0], command.operands[1]), True))
            self.shapes[-1].addCollisionRect((0,0), (command.operands[2], command.operands[3]), self.tileSize)
        elif command.opcode == b'\x50': # Set solution
            self.tileSolution[command.operands[0]] = (command.operands[1], command.operands[2])
        elif command.opcode == b'\x51': # Add tilemap (usually one of the first commands):
            # TODO - Unify spr removal
            self.tileMap = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "nazo/slide", command.operands[0][:-4])
        elif command.opcode == b'\x52': # Add tile
            # Unk, (animName, animName), (tileX, tileY)
            if command.operands[0] != 0:
                state.debugPrint("WarnSlideUnkConstant: Operand 0 on added tile was", command.operands[0], "instead of 0!")
            self.tileInternalToMoveableIndexMap[self.tileMoveableIndex] = len(self.shapes)
            self.shapes.append(han_nazo_element.SlidingShape((command.operands[3], command.operands[4]), False))
            self.shapes[-1].image = self.tileMap.setAnimationFromNameAndReturnInitialFrame(command.operands[1])
            self.tileMoveableIndex += 1
        elif command.opcode == b'\x53': # Add dynamic occlusion data
            self.shapes[-1].addCollisionRect((command.operands[0], command.operands[1]), (command.operands[2], command.operands[3]), self.tileSize)
        else:
            super().executeCommand(command)
    
    def getMovementOpportunities(self, shape):
        def hasIntersectedAfterMovement():
            canStop = False
            for checkShape in self.shapes:
                if checkShape != shape:
                    if shape.doesIntersect(checkShape, self.tileSize):
                        canStop = True
                        break
                    if canStop:
                        break
            return canStop

        originalShapeCorner = shape.cornerTilePos
        possibleMovement = [0,0,0,0]

        if shape.cornerTilePos[0] > 0:
            offset = 0
            for _xLeftIndex in range(shape.cornerTilePos[0]):
                shape.cornerTilePos = (shape.cornerTilePos[0] - 1,
                                    shape.cornerTilePos[1])
                if hasIntersectedAfterMovement():
                    offset = 1
                    break
            possibleMovement[0] = originalShapeCorner[0] - shape.cornerTilePos[0] - offset
            shape.cornerTilePos = originalShapeCorner
        
        if shape.cornerTilePos[0] < self.tileBoardDimensions[0] - 1:
            offset = 0
            for _xRightIndex in range(self.tileBoardDimensions[0] - shape.bound.width - shape.cornerTilePos[0]):
                shape.cornerTilePos = (shape.cornerTilePos[0] + 1,
                                    shape.cornerTilePos[1])
                if hasIntersectedAfterMovement():
                    offset = 1
                    break
            possibleMovement[1] = shape.cornerTilePos[0] - originalShapeCorner[0] - offset
            shape.cornerTilePos = originalShapeCorner

        if shape.cornerTilePos[1] > 0:
            offset = 0
            for _yUpIndex in range(shape.cornerTilePos[1]):
                shape.cornerTilePos = (shape.cornerTilePos[0],
                                    shape.cornerTilePos[1] - 1)
                if hasIntersectedAfterMovement():
                    offset = 1
                    break
            possibleMovement[2] = originalShapeCorner[1] - shape.cornerTilePos[1] - offset
            shape.cornerTilePos = originalShapeCorner

        if shape.cornerTilePos[1] < self.tileBoardDimensions[1] - 1:
            offset = 0
            for _yDownIndex in range(self.tileBoardDimensions[1] - shape.bound.height - shape.cornerTilePos[1]):
                shape.cornerTilePos = (shape.cornerTilePos[0],
                                    shape.cornerTilePos[1] + 1)
                if hasIntersectedAfterMovement():
                    offset = 1
                    break
            possibleMovement[3] = shape.cornerTilePos[1] - originalShapeCorner[1] - offset
            shape.cornerTilePos = originalShapeCorner
        
        return possibleMovement

    def flagIfRequiresChanging(self, newDirection):
        if self.activeTileCurrentMouseDirection != newDirection:
            self.directionRequiresChanging = True
            self.directionNextDirection = newDirection

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for indexShape, shape in enumerate(self.shapes):
                if not(shape.isLocked):
                    tempPosCorner = (self.posCorner[0], self.posCorner[1] + conf.LAYTON_SCREEN_HEIGHT)
                    if shape.wasClicked(event.pos, tempPosCorner, self.tileSize):
                        self.activeTileMovementPossibilities = self.getMovementOpportunities(shape)
                        if max(self.activeTileMovementPossibilities) > 0:
                            self.activeTile = indexShape
                            self.activeTileLastMousePos = event.pos
                            self.activeTileMouseGrabOffset = self.shapeSpaceToScreenSpace(shape)
                            self.activeTileMouseGrabOffset = (event.pos[0] - self.activeTileMouseGrabOffset[0],
                                                              event.pos[1] - self.activeTileMouseGrabOffset[1])
                        else:
                            self.activeTile = None
                        break

        elif event.type == pygame.MOUSEMOTION:
            if self.activeTile != None:
                if event.pos[1] >= conf.LAYTON_SCREEN_HEIGHT:
                    # Recalculate direction of mouse travel
                    tempMouseAngle = atan2(event.pos[1] - self.activeTileLastMousePos[1], event.pos[0] - self.activeTileLastMousePos[0])
                    self.activeTileLastMousePos = event.pos
                    if tempMouseAngle >= pi / 4 and tempMouseAngle < 3 * pi / 4:        # DOWN
                        self.flagIfRequiresChanging(PuzzletSliding.DIRECTION_DOWN)
                    elif tempMouseAngle >= 3 * pi / 4 or tempMouseAngle < - 3 * pi / 4: # LEFT
                        self.flagIfRequiresChanging(PuzzletSliding.DIRECTION_LEFT)
                    elif tempMouseAngle >= - 3 * pi / 4 and tempMouseAngle < - pi / 4:  # UP
                        self.flagIfRequiresChanging(PuzzletSliding.DIRECTION_UP)
                    else:                                                               # RIGHT
                        self.flagIfRequiresChanging(PuzzletSliding.DIRECTION_RIGHT)

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.activeTile != None and self.activeTileTempPlace != (0,0):
                self.countMoves += 1
                # Apply shape place!
                self.applyShapeOffset(self.shapes[self.activeTile])
                self.activeTileCurrentMouseDirection = None
                self.directionNextDirection = None
                self.directionRequiresChanging = False
                self.activeTileTempPlace = (0,0)
            self.activeTile = None

            if self.evaluateSolution():
                self.setVictory()
                            
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
            super().executeCommand(command)

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
    TRACE_COLOUR_DEFAULT = (240,0,0)
    TRACE_COLOUR_TRANSPARENCY = (0,240,0)
    TRACE_X_LIMIT = conf.LAYTON_SCREEN_WIDTH - (buttonSubmit.dimensions[0] + TRACE_LINE_THICKNESS)

    def __init__(self, puzzleData, puzzleIndex, playerState):
        LaytonContextPuzzlet.__init__(self)
        self.puzzleIndex = puzzleIndex
        
        self.cursorEnableSoftlockRetryScreen = True
        self.cursorIsDrawing = False
        self.cursorColour = PuzzletTraceButton.TRACE_COLOUR_DEFAULT
        self.cursorLineSurface = pygame.Surface((conf.LAYTON_SCREEN_WIDTH, conf.LAYTON_SCREEN_HEIGHT))
        self.cursorLineSurface.set_colorkey(PuzzletTraceButton.TRACE_COLOUR_TRANSPARENCY)
        self.cursorLineSurface.fill(PuzzletTraceButton.TRACE_COLOUR_TRANSPARENCY)

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
            self.cursorColour = (command.operands[0],command.operands[1],command.operands[2])
        elif command.opcode == b'\x18':
            self.traceLocationsDict[self.countAdditionalTiles].append(han_nazo_element.TraceLocation(command.operands[0], command.operands[1] + conf.LAYTON_SCREEN_HEIGHT,
                                                                      command.operands[2], conf.LAYTON_STRING_BOOLEAN[command.operands[3]]))
        elif command.opcode == b'\x3e':
            self.traceLocationIndexingEnable = True
            self.countAdditionalTiles += 1
            self.traceLocationsDict[self.countAdditionalTiles] = []
            self.traceAdditionalTiles.append(anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "nazo/q" + str(self.puzzleIndex) + "_" + str(self.countAdditionalTiles) + ".arc"))
        else:
            super().executeCommand(command)
    
    def getScript(self):
        output = script.gdScript()
        if self.cursorColour != PuzzletTraceButton.TRACE_COLOUR_DEFAULT:
            output.commands.append(script.gdOperation(b'\x0c', [self.cursorColour[0], self.cursorColour[1], self.cursorColour[2]]))
    
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
        self.cursorLineSurface.fill(PuzzletTraceButton.TRACE_COLOUR_TRANSPARENCY)

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
                self.cursorLineSurface.fill(PuzzletTraceButton.TRACE_COLOUR_TRANSPARENCY)
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

class PuzzletSort(LaytonContextPuzzlet):

    # TODO - Make more resilient to null tiles, as the anim bypass code will fail at the end

    buttonSubmit        = anim.AnimatedButton(anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "system/btn/" + conf.LAYTON_ASSET_LANG, "hantei"), None,
                                              imageIsSurface=True, useButtonFromAnim=True)
    buttonSubmit.setPos((conf.LAYTON_SCREEN_WIDTH - buttonSubmit.dimensions[0], (conf.LAYTON_SCREEN_HEIGHT * 2) - buttonSubmit.dimensions[1]))

    def __init__(self, puzzleData, puzzleIndex, playerState):
        LaytonContextPuzzlet.__init__(self)
        self.interactableElements = []
        self.interactableElementsAnimMapLists = []
        self.solutionAnimNames = []
    
    def executeCommand(self, command):
        if command.opcode == b'\x2e':
            # TODO - Is "Create an Animation" applied by default or just unused?
            self.interactableElements.append(anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "nazo/touch", command.operands[2][:-4], x=command.operands[0],
                                                                y=command.operands[1] + conf.LAYTON_SCREEN_HEIGHT))
            self.interactableElements[-1].setAnimationFromName(str(command.operands[3]))
            self.interactableElementsAnimMapLists.append(list(self.interactableElements[-1].animMap.keys()))
            self.solutionAnimNames.append(str(command.operands[4]))
        else:
            super().executeCommand(command)

    def draw(self, gameDisplay):
        for element in self.interactableElements:
            element.draw(gameDisplay)
        PuzzletSort.buttonSubmit.draw(gameDisplay)
    
    def update(self, gameClockDelta):
        for element in self.interactableElements:
            element.update(gameClockDelta)
    
    def evaluateSolution(self):
        for indexElement, element in enumerate(self.interactableElements):
            if element.animActive != self.solutionAnimNames[indexElement]:
                return False
        return True

    def handleEvent(self, event):
        PuzzletSort.buttonSubmit.handleEvent(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            for indexElement, element in enumerate(self.interactableElements):
                if element.wasClicked(event.pos):
                    # TODO - Ensure that the next animation being used has indices. For now, the only one that doesn't is "Create an Animation"
                    offset = 1
                    nextAnim = "Create an Animation"
                    while nextAnim == "Create an Animation":
                        nextAnim = self.interactableElementsAnimMapLists[indexElement][(self.interactableElementsAnimMapLists[indexElement].index(element.animActive) + offset) % len(self.interactableElementsAnimMapLists[indexElement])]
                        offset += 1
                    element.setAnimationFromName(nextAnim)
                    return True

        if PuzzletSort.buttonSubmit.peekPressedStatus():
            if PuzzletSort.buttonSubmit.getPressedStatus():
                if self.evaluateSolution():
                    self.setVictory()
                else:
                    self.setLoss()
            return True
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
    defaultHandlers = {0: 'Matchstick',
                       3: PuzzletOnOff,    # Mark Answer
                       2: PuzzletPushButton,
                       5: PuzzletTraceButton,
                       10: PuzzletSort,
                       13: 'Move to Answer',
                       14: 'Tap to Answer', 17: 'Move Knight', 23: 'Area', 24: 'Rose Placement', 27: 'Skate to Exit',
                       29: 'Remove Balls', 30: 'Move in Pairs', 31: 'Lamp Placement', 33: 'Cross Bridge', 34: 'Shape Search', 
                       12: PuzzletTileRotate, 18: PuzzletTileRotate,
                       16: 'Write Answer', 22: 'Write Answer', 28: 'Write Answer', 32: 'Write Answer', 35:'Placement',
                       1: 'Sliding', 25: PuzzletSliding, 
                       26: 'Arrange to Answer', 11: 'Arrange to Answer',
                       6: 'Draw Line', 9:PuzzletCut, 15: 'Draw Line'}

    def __init__(self, puzzleIndex, playerState):
        state.LaytonSubscreen.__init__(self)
        self.transitionsEnableIn = False
        self.transitionsEnableOut = False
        self.screenBlockInput = True
        
        self.commandFocus = None
        self.puzzleIndex = puzzleIndex
        puzzleDataIndex = (puzzleIndex // 60) + 1
        puzzleScript    = script.gdScript.fromData(FileInterface.getPackedData(FileInterface.PATH_ASSET_SCRIPT + "puzzle.plz",
                                                   "q" + str(puzzleIndex) + "_param.gds", version = 1))
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

        self.addToStack(LaytonPuzzleUi(self.puzzleData, puzzleIndex, playerState))
        self.addToStack(LaytonScrollerOverlay(self.puzzleData.textPrompt, playerState))
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
    state.play(LaytonPuzzleHandler(44, tempPlayerState), tempPlayerState)
    # 3, 6 Tracebutton
    # 8 PushButton
    # 2, 39, 115 Rotate and arrange
    # 44, 21, 25, 57 sliding
    # 10, 16, 41 cut
    # 29 Placement (??)
    # 56 Rose placement
    # 34, 38 sort