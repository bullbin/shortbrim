import coreProp, coreState, coreAnim, pygame, nazoElements, scrnHint, gdsLib

# Testing only
import ctypes; ctypes.windll.user32.SetProcessDPIAware()
pygame.init()

class LaytonContextPuzzlet(coreState.LaytonContext):
    def __init__(self):
        coreState.LaytonContext.__init__(self)
        self.imageButtons = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG, "buttons")
        self.registerVictory = False
        self.registerLoss = False
        self.registerQuit = False
    def setVictory(self):
        self.registerVictory = True
        self.registerLoss = False
    def setLoss(self):
        self.registerVictory = False
        self.registerLoss = True

class LaytonTouchOverlay(coreState.LaytonContext):

    imageTouchAlphaBounds = (63,127)

    def __init__(self):
        coreState.LaytonContext.__init__(self)
        self.screenIsOverlay        = True
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.imageTouch = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG, "qend_touch")
        self.imageTouch = self.imageTouch.setAnimationFromNameAndReturnInitialFrame("touch")
        self.imageTouchPos = ((coreProp.LAYTON_SCREEN_WIDTH - self.imageTouch.get_width()) // 2,
                              ((coreProp.LAYTON_SCREEN_HEIGHT - self.imageTouch.get_height()) // 2) + coreProp.LAYTON_SCREEN_HEIGHT)
        self.imageTouchAlpha = LaytonTouchOverlay.imageTouchAlphaBounds[1]

    def update(self, gameClockDelta):
        self.imageTouch.set_alpha(self.imageTouchAlpha)

    def draw(self, gameDisplay):
        gameDisplay.blit(self.imageTouch, self.imageTouchPos)

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.isContextFinished = True

class LaytonPuzzleUi(LaytonContextPuzzlet):

    buttonHint      = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG, "hint_buttons")
    buttonHint.pos  = (coreProp.LAYTON_SCREEN_WIDTH - buttonHint.dimensions[0], coreProp.LAYTON_SCREEN_HEIGHT)
    buttonHintFlashDelay = 15000

    def __init__(self, puzzleIndex, playerState, puzzleHintCount):
        LaytonContextPuzzlet.__init__(self)
        self.screenIsOverlay        = True
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True

        self.puzzleIndex            = puzzleIndex
        self.playerState            = playerState
        self.puzzleAnimFont         = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, "q_numbers")
        self.puzzleIndexText        = '%03d' % self.puzzleIndex
        self.puzzleHintCount        = puzzleHintCount

        if self.puzzleIndex < 50:
            puzzlePath = coreProp.PATH_ASSET_QTEXT + coreProp.LAYTON_ASSET_LANG + "\\q000\\"
        elif self.puzzleIndex < 100:
            puzzlePath = coreProp.PATH_ASSET_QTEXT + coreProp.LAYTON_ASSET_LANG + "\\q050\\"
        else:
            puzzlePath = coreProp.PATH_ASSET_QTEXT + coreProp.LAYTON_ASSET_LANG + "\\q100\\"
            
        # Load the puzzle qText
        with open(puzzlePath + "q_" + str(self.puzzleIndex) + ".txt", 'r') as qText:
            self.puzzleQText = coreAnim.TextScroller(self.playerState.getFont("fontq"), qText.read(), targetFramerate=60, textPosOffset=(4,23))
        
        LaytonPuzzleUi.buttonHint.setActiveFrame(self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel)
        self.buttonHintWaitTime = 0
        self.screenHint = scrnHint.Screen(self.puzzleIndex, self.playerState, self.puzzleHintCount, self.puzzleAnimFont, self.imageButtons)
        
    def update(self, gameClockDelta):
        self.puzzleQText.update(gameClockDelta)
        if not(self.screenBlockInput):
            LaytonPuzzleUi.buttonHint.update(gameClockDelta)
            if LaytonPuzzleUi.buttonHint.animActive == None:
                LaytonPuzzleUi.buttonHint.setActiveFrame(self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel)
                if self.buttonHintWaitTime < LaytonPuzzleUi.buttonHintFlashDelay:
                    self.buttonHintWaitTime += gameClockDelta
                else:
                    LaytonPuzzleUi.buttonHint.setAnimationFromIndex(self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel)
                    self.buttonHintWaitTime = 0

    def draw(self, gameDisplay):
        if self.puzzleHintCount > 0:
            LaytonPuzzleUi.buttonHint.draw(gameDisplay)
        self.puzzleQText.draw(gameDisplay)

        # Draw puzzle index text
        for bannerText, xPosInitial in [(self.puzzleIndexText, 27),
                                        (format(str(self.playerState.puzzleData[self.puzzleIndex].getValue()), '>3'), 75),
                                        (format(str(self.playerState.remainingHintCoins), '>3'), 228)]:
            self.puzzleAnimFont.pos = (xPosInitial,6)
            for char in bannerText:
                if self.puzzleAnimFont.setAnimationFromName(char):
                    self.puzzleAnimFont.setInitialFrameFromAnimation()
                    self.puzzleAnimFont.draw(gameDisplay)
                self.puzzleAnimFont.pos = (self.puzzleAnimFont.pos[0] + self.puzzleAnimFont.dimensions[0] - 1, self.puzzleAnimFont.pos[1])

    def handleEvent(self, event):

        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.screenBlockInput:
                self.puzzleQText.skip()
                self.screenBlockInput = False       # Free other contexts to use inputs
                self.setStackUpdate()
            elif self.puzzleHintCount > 0 and LaytonPuzzleUi.buttonHint.wasClicked(event.pos):
                self.screenHint.refresh()
                self.screenNextObject = self.screenHint
                return True
        return False

class LaytonPuzzleBackground(coreState.LaytonContext):

    backgroundTs = pygame.image.load(coreProp.PATH_ASSET_BG + coreProp.LAYTON_ASSET_LANG + "\\q_bg.png")

    def __init__(self, puzzleIndex, playerState):
        coreState.LaytonContext.__init__(self)
        
        # Set screen variables
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True

        try:
            self.backgroundBs = pygame.image.load(coreProp.PATH_ASSET_BG + "q" + str(puzzleIndex) + "_bg.png")
        except:
            print("[APPLET] BG: No default background found!")
            self.backgroundBs = pygame.Surface((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT)).convert()

    def draw(self, gameDisplay):
        gameDisplay.blit(LaytonPuzzleBackground.backgroundTs, (0,0))
        gameDisplay.blit(self.backgroundBs, (0,coreProp.LAYTON_SCREEN_HEIGHT))

class PuzzletInteractableDragContext(LaytonContextPuzzlet):

    promptNoMove        = coreAnim.StaticImage(coreProp.PATH_ASSET_BG + coreProp.LAYTON_ASSET_LANG + "\\nomoretouch.png", y=coreProp.LAYTON_SCREEN_HEIGHT)

    def __init__(self):
        LaytonContextPuzzlet.__init__(self)
        self.buttonReset = coreAnim.StaticImage(self.imageButtons.setAnimationFromNameAndReturnInitialFrame("modosu"), x=99, y=7+coreProp.LAYTON_SCREEN_HEIGHT, imageIsSurface=True)
        self.buttonSubmit = coreAnim.StaticImage(self.imageButtons.setAnimationFromNameAndReturnInitialFrame("kettei"), x=22, y=7+coreProp.LAYTON_SCREEN_HEIGHT, imageIsSurface=True)
        self.elements = []
        self.elementFocus = None
        self.elementClickOffset = (0,0)
        self.puzzleSoftlockMoveScreen = False
        self.puzzleMoveLimit = None
        self.puzzleMoveFont  = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, "inputnumbers")
        self.puzzleCurrentMoves = 0
        self.posInitial = []
        self.posChanged = []
    
    def draw(self, gameDisplay):
        self.buttonSubmit.draw(gameDisplay)
        self.buttonReset.draw(gameDisplay)
        for elementIndex in range(len(self.elements)):
            if elementIndex != self.elementFocus:
                self.elements[elementIndex].draw(gameDisplay)
        if self.elementFocus != None:
            self.elements[self.elementFocus].draw(gameDisplay)
        if self.puzzleMoveLimit != None:
            self.puzzleMoveFont.pos = (31, coreProp.LAYTON_SCREEN_HEIGHT + 167)
            for char in format(str(self.puzzleMoveLimit - self.puzzleCurrentMoves), '>2'):
                if self.puzzleMoveFont.setAnimationFromName(char):
                    self.puzzleMoveFont.setInitialFrameFromAnimation()
                    self.puzzleMoveFont.draw(gameDisplay)
                self.puzzleMoveFont.pos = (self.puzzleMoveFont.pos[0] + self.puzzleMoveFont.dimensions[0] - 1, self.puzzleMoveFont.pos[1])
            if self.puzzleSoftlockMoveScreen:
                PuzzletInteractableDragContext.promptNoMove.draw(gameDisplay)

    def reset(self):
        self.puzzleSoftlockMoveScreen = False
        self.puzzleCurrentMoves = 0
    
    def evaluateSolution(self):
        return False

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.buttonSubmit.wasClicked(event.pos):
                if self.evaluateSolution():
                    self.setVictory()
                else:
                    self.setLoss()
                return True
            elif self.buttonReset.wasClicked(event.pos):
                self.reset()
                return True
            elif not(self.puzzleSoftlockMoveScreen):
                if self.puzzleMoveLimit == None or self.puzzleCurrentMoves < self.puzzleMoveLimit:
                    for elementIndex in range(len(self.elements)):
                        if self.elements[elementIndex].wasClicked(event.pos):
                            self.elementFocus = elementIndex
                            self.elementClickOffset = (event.pos[0] - self.elements[elementIndex].pos[0], event.pos[1] - self.elements[elementIndex].pos[1])
                            break # To-do: Sort so clickable element is always the topmost, as these can overlap unlike tiles
                else:
                    self.puzzleSoftlockMoveScreen = True
        return False
        # Note: MOUSEBUTTONUP is not handled by default because this is where handlers differ

class PuzzletInteractableMatchContext(PuzzletInteractableDragContext):

    matchImage          = pygame.image.load(coreProp.PATH_ASSET_ANI + "match_0.png").convert_alpha()
    matchShadowImage    = pygame.image.load(coreProp.PATH_ASSET_ANI + "match_1.png").convert_alpha()

    def __init__(self):
        PuzzletInteractableDragContext.__init__(self)
    
    def executeCommand(self, command):
        if command.opcode == b'\x2a':
            self.elements.append(nazoElements.Match(PuzzletInteractableMatchContext.matchImage, PuzzletInteractableMatchContext.matchShadowImage,
                                                    command.operands[0],command.operands[1]+coreProp.LAYTON_SCREEN_HEIGHT,
                                                    command.operands[2]))
        elif command.opcode == b'\x2b':
            pass
        elif command.opcode == b'\x27':
            self.puzzleMoveLimit = command.operands[0]
        else:
            print("ErrUnrecognised: " + str(command.opcode))

class PuzzletInteractableCoinContext(PuzzletInteractableDragContext):
    
    COIN_ACCEPTABLE_REGION = 6
    COIN_SHADOW_OFFSET = 1
    backgroundCoin = pygame.image.load(coreProp.PATH_ASSET_BG + "coin_bg.png").convert()
    spriteCoin = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, "coin")
    spriteShadow = nazoElements.IndependentTile(spriteCoin, "shadow")

    def __init__(self):
        PuzzletInteractableDragContext.__init__(self)
    
    def executeCommand(self, command):
        if command.opcode == b'\x25':
            self.elements.append(nazoElements.IndependentTile(PuzzletInteractableCoinContext.spriteCoin, "coin", x=command.operands[0], y=command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT))
            self.posInitial.append((command.operands[0], command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT))
        elif command.opcode == b'\x26':
            if (command.operands[0], command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT) not in self.posInitial:
                self.posChanged.append((command.operands[0], command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT))
        elif command.opcode == b'\x27':
            self.puzzleMoveLimit = command.operands[0]
        else:
            print("ErrUnrecognised: " + str(command.opcode))

    def draw(self, gameDisplay):
        gameDisplay.blit(PuzzletInteractableCoinContext.backgroundCoin, (0, coreProp.LAYTON_SCREEN_HEIGHT))
        for elementIndex in range(len(self.elements)):
            if elementIndex != self.elementFocus:
                PuzzletInteractableCoinContext.spriteShadow.pos = (self.elements[elementIndex].pos[0] + PuzzletInteractableCoinContext.COIN_SHADOW_OFFSET,
                                                                   self.elements[elementIndex].pos[1] + PuzzletInteractableCoinContext.COIN_SHADOW_OFFSET)
                PuzzletInteractableCoinContext.spriteShadow.draw(gameDisplay)
        super().draw(gameDisplay)
    
    def update(self, gameClockDelta):
        super().update(gameClockDelta)
        if self.elementFocus != None:
            posCursorFollow = (pygame.mouse.get_pos()[0] - self.elementClickOffset[0], pygame.mouse.get_pos()[1] - self.elementClickOffset[1])
            if posCursorFollow[1] < coreProp.LAYTON_SCREEN_HEIGHT:
                self.elements[self.elementFocus].pos = (posCursorFollow[0], coreProp.LAYTON_SCREEN_HEIGHT)
            else:
                self.elements[self.elementFocus].pos = posCursorFollow

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONUP and self.elementFocus != None:
            self.elements.append(self.elements.pop(self.elementFocus))          # Place last interacted element on top
            self.elementFocus = None
            self.puzzleCurrentMoves += 1
            self.elementClickOffset = (0,0)
        super().handleEvent(event)
    
    def evaluateSolution(self):
        posChanged = list(self.posChanged)
        isSolved = True
        for element in self.elements:
            if element.pos not in self.posInitial:  # The element has changed places
                elementHasSolution = False
                for posChangeIndex in range(len(posChanged)):
                    if (abs(element.pos[0] - posChanged[posChangeIndex][0]) <= PuzzletInteractableCoinContext.COIN_ACCEPTABLE_REGION and
                        abs(element.pos[1] - posChanged[posChangeIndex][1]) <= PuzzletInteractableCoinContext.COIN_ACCEPTABLE_REGION):
                        posChanged.pop(posChangeIndex)
                        elementHasSolution = True
                        break
                if not(elementHasSolution):
                    isSolved = False
            if not(isSolved):
                break
        if len(posChanged) == 0:
            return True
        return False

    def reset(self):
        super().reset()
        for element in self.elements:
            element.reset()

class PuzzletInteractableFreeButtonContext(LaytonContextPuzzlet):

    def __init__(self):
        LaytonContextPuzzlet.__init__(self)
        self.interactableElements = []
        self.drawFlagsInteractableElements = []
        
        self.solutionElements = []
    
    def executeCommand(self, command):
        if command.opcode == b'\x5d':
            imageName = command.operands[2]
            if imageName[-4:] == ".spr":
                imageName = imageName[0:-4]

            if command.operands[3]:
                self.solutionElements.append(len(self.interactableElements))
            
            self.interactableElements.append(coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, imageName,
                                                                    x=command.operands[0], y=command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT))
            self.interactableElements[-1].setActiveFrame(command.operands[4])
            self.drawFlagsInteractableElements.append(False)
        else:
            print("ErrUnrecognised: " + str(command.opcode))
    
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

class PuzzletInteractableOnOffContext(PuzzletInteractableFreeButtonContext):

    def __init__(self):
        PuzzletInteractableFreeButtonContext.__init__(self)
        self.buttonSubmit = coreAnim.StaticImage(self.imageButtons.setAnimationFromNameAndReturnInitialFrame("kettei"), x=186, y=158+coreProp.LAYTON_SCREEN_HEIGHT, imageIsSurface=True)
        self.drawFlagsInteractableElementsActiveCount = 0
    
    def draw(self, gameDisplay):
        super().draw(gameDisplay)
        self.buttonSubmit.draw(gameDisplay)
    
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for elementIndex in range(len(self.interactableElements)):
                if self.interactableElements[elementIndex].wasClicked(event.pos):
                    self.drawFlagsInteractableElements[elementIndex] = not(self.drawFlagsInteractableElements[elementIndex])
                    if self.drawFlagsInteractableElements[elementIndex]:
                        self.drawFlagsInteractableElementsActiveCount += 1
                    else:
                        self.drawFlagsInteractableElementsActiveCount -= 1
            
            if self.buttonSubmit.wasClicked(event.pos):
                if self.drawFlagsInteractableElementsActiveCount == len(self.solutionElements):
                    isSolved = True
                    for elementIndex in self.drawFlagsInteractableElements:
                        if elementIndex not in self.solutionElements:
                            isSolved = False
                    if isSolved:
                        self.setVictory()
                    else:
                        self.setLoss()
                else:
                    self.setLoss()

class PuzzletInteractableTileContext(LaytonContextPuzzlet):

    TILE_SWITCH_REGION = 12

    def __init__(self):
        LaytonContextPuzzlet.__init__(self)
        self.buttonSubmit = coreAnim.StaticButton(self.imageButtons.setAnimationFromNameAndReturnInitialFrame("kettei"), x=188, y=159+coreProp.LAYTON_SCREEN_HEIGHT, imageIsSurface=True)
        self.buttonRestart = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG, "restart")
        self.buttonRestart = coreAnim.StaticButton(self.buttonRestart.setAnimationFromNameAndReturnInitialFrame("gfx"), x=7, y=7+coreProp.LAYTON_SCREEN_HEIGHT, imageIsSurface=True)
        self.tileDict = {}                  # Stores the core asset used for all tiles
        self.tiles = []
        self.tileTargets = []
        self.tileTargetIndicesSkip = []     # Stores targets which are unmovable (locked in place)
        self.tileSolutions = []
        self.tileSlotDict = {}
        self.tileSolutionLoadIndex = 0
        self.tileClickOffset = (0,0)
        self.tileActiveDrawPosition = (0,0)
        self.tileActive = None
    
    def draw(self, gameDisplay):
        self.buttonSubmit.draw(gameDisplay)
        self.buttonRestart.draw(gameDisplay)
        for tileIndex in range(len(self.tiles)):
            if tileIndex != self.tileActive:
                gameDisplay.blit(self.tiles[tileIndex], self.tileTargets[self.tileSlotDict[tileIndex]])
        if self.tileActive != None:
            posCursorFollow = (self.tileActiveDrawPosition[0] - self.tileClickOffset[0], self.tileActiveDrawPosition[1] - self.tileClickOffset[1])
            if posCursorFollow[1] < coreProp.LAYTON_SCREEN_HEIGHT:
                gameDisplay.blit(self.tiles[self.tileActive], (posCursorFollow[0], coreProp.LAYTON_SCREEN_HEIGHT))
            else:
                gameDisplay.blit(self.tiles[self.tileActive], posCursorFollow)
    
    def executeCommand(self, command):
        if command.opcode == b'\x73':                   # Place tile
            if command.operands[2] not in self.tileDict.keys():
                self.tileDict[command.operands[2]] = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, command.operands[2][0:-4])
            self.tileSlotDict[len(self.tiles)] = len(self.tiles)
            if self.tileDict[command.operands[2]].setAnimationFromName(command.operands[3]):
                self.tiles.append(self.tileDict[command.operands[2]].frames[self.tileDict[command.operands[2]].animMap[self.tileDict[command.operands[2]].animActive].indices[0]])
            else:
                if len(self.tileDict[command.operands[2]].frames) >= command.operands[3]:
                    self.tiles.append(self.tileDict[command.operands[2]].frames[command.operands[3] - 1])
                else:
                    self.tiles.append(pygame.Surface((24,24)))
            self.tileTargets.append((command.operands[0], command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT))
        elif command.opcode == b'\x74':                 # Set target
            self.tileTargets.append((command.operands[0], command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT))
        elif command.opcode == b'\x75':                 # Map solution
            self.tileSolutions[self.tileSolutionLoadIndex // len(self.tiles)][command.operands[0]] = len(self.tiles) + command.operands[1]
            self.tileSolutionLoadIndex += 1
        elif command.opcode == b'\x76':                 # Set solution count
            for _solutionIndex in range(command.operands[0]):
                self.tileSolutions.append({})
        else:
            print("CommandTileUnknown: " + str(command.opcode))

    def reset(self):
        for tileIndex in range(len(self.tiles)):
            if tileIndex not in self.tileTargetIndicesSkip:
                self.tileSlotDict[tileIndex] = tileIndex

    def evaluateSolution(self):
        if self.tileSlotDict in self.tileSolutions:
            return True
        return False

    def wasTileClicked(self, tileIndex, mousePos):
        if self.tileTargets[self.tileSlotDict[tileIndex]][0] + self.tiles[tileIndex].get_width() >= mousePos[0] and mousePos[0] >= self.tileTargets[self.tileSlotDict[tileIndex]][0]:
            if self.tileTargets[self.tileSlotDict[tileIndex]][1] + self.tiles[tileIndex].get_height() >= mousePos[1] and mousePos[1] >= self.tileTargets[self.tileSlotDict[tileIndex]][1]:
                self.tileActive = tileIndex
                self.tileClickOffset = (mousePos[0] - self.tileTargets[self.tileSlotDict[tileIndex]][0], mousePos[1] - self.tileTargets[self.tileSlotDict[tileIndex]][1])
                return True
        return False

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            self.buttonSubmit.registerButtonUp(event)
            self.buttonRestart.registerButtonUp(event)
            if self.buttonSubmit.getPressedStatus():
                if self.evaluateSolution():
                    self.setVictory()
                else:
                    self.setLoss()
            elif self.buttonRestart.getPressedStatus():
                self.reset()

            elif self.tileActive != None:
                tileTargetIndex = 0
                for tileTarget in self.tileTargets:
                    if (abs(event.pos[0] - self.tileClickOffset[0] - tileTarget[0]) <= PuzzletInteractableTileContext.TILE_SWITCH_REGION and
                        abs(event.pos[1] - self.tileClickOffset[1]- tileTarget[1]) <= PuzzletInteractableTileContext.TILE_SWITCH_REGION):
                        isOccupied = False
                        isFree = True
                        for tileIndex in range(len(self.tiles)):
                            if self.tileSlotDict[tileIndex] == tileTargetIndex:
                                if tileIndex in self.tileTargetIndicesSkip:
                                    isFree = False
                                isOccupied = True
                                break
                        if isFree:
                            if isOccupied:  # Switch slots
                                self.tileSlotDict[tileIndex] = self.tileSlotDict[self.tileActive]
                            self.tileSlotDict[self.tileActive] = tileTargetIndex
                        break
                    tileTargetIndex += 1
                self.tileActive = None
            self.tileClickOffset = (0,0)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.buttonSubmit.registerButtonDown(event)
            self.buttonRestart.registerButtonDown(event)

            self.tileActive = None
            for tileIndex in range(len(self.tiles)):
                if tileIndex not in self.tileTargetIndicesSkip and self.wasTileClicked(tileIndex, event.pos):
                    self.tileActiveDrawPosition = event.pos
                    break   # Multi-touch is not supported anyway
        
        elif self.tileActive != None and event.type == pygame.MOUSEMOTION:
            self.tileActiveDrawPosition = event.pos

class PuzzletInteractableQueenContext(PuzzletInteractableTileContext):

    QUEEN_OCTUPLET_CORNER = (197, 62 + coreProp.LAYTON_SCREEN_HEIGHT)
    QUEEN_OCTUPLET_GAP = 2
    QUEEN_SPRITE = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, "queen_gfx")

    def __init__(self):
        PuzzletInteractableTileContext.__init__(self)
        self.tileQueenCount = 0
        self.tileBoardSquareDimension = 0
        self.tileSolvingMethod = 0
        self.backgroundBs = pygame.Surface((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT))
    
    def executeCommand(self, command):
        if command.opcode == b'\x3b':
            try:
                self.backgroundBs = pygame.image.load(coreProp.PATH_ASSET_BG + "chess_" + str(command.operands[2]) + "_bg.png").convert()
            except:
                print("ErrQueenBgNotFound: Could not load " + coreProp.PATH_ASSET_BG + "chess_" + str(command.operands[2]) + "_bg.png")
            self.tileBoardSquareDimension = command.operands[2]
            for yQueenIndex in range(command.operands[2]):
                for xQueenIndex in range(command.operands[2]):
                    self.tileSolutions.append(True)
                    self.tileTargets.append(((xQueenIndex * PuzzletInteractableQueenContext.QUEEN_SPRITE.dimensions[0]) + command.operands[0],
                                             (yQueenIndex * PuzzletInteractableQueenContext.QUEEN_SPRITE.dimensions[1]) + coreProp.LAYTON_SCREEN_HEIGHT + command.operands[1]))
        elif command.opcode == b'\x3c':
            self.tileQueenCount = command.operands[0]
            for _queenIndex in range(command.operands[0]):
                self.tileSlotDict[len(self.tiles)] = len(self.tileTargets) + len(self.tiles)
                if PuzzletInteractableQueenContext.QUEEN_SPRITE.setAnimationFromName("q1"):
                    self.tiles.append(PuzzletInteractableQueenContext.QUEEN_SPRITE.frames[PuzzletInteractableQueenContext.QUEEN_SPRITE.animMap[PuzzletInteractableQueenContext.QUEEN_SPRITE.animActive].indices[0]])
                else:
                    self.tiles.append(pygame.Surface((20,20)))
            for yQueenIndex in range(4):
                for xQueenIndex in range(2):
                    self.tileTargets.append(((xQueenIndex * (PuzzletInteractableQueenContext.QUEEN_SPRITE.dimensions[0] + PuzzletInteractableQueenContext.QUEEN_OCTUPLET_GAP)) + PuzzletInteractableQueenContext.QUEEN_OCTUPLET_CORNER[0],
                                             (yQueenIndex * (PuzzletInteractableQueenContext.QUEEN_SPRITE.dimensions[1] + PuzzletInteractableQueenContext.QUEEN_OCTUPLET_GAP)) + PuzzletInteractableQueenContext.QUEEN_OCTUPLET_CORNER[1]))
        elif command.opcode == b'\x3d':
            self.tileSlotDict[len(self.tiles)] = (command.operands[1] * self.tileBoardSquareDimension) + command.operands[0]
            self.tileTargetIndicesSkip.append(len(self.tiles))
            if PuzzletInteractableQueenContext.QUEEN_SPRITE.setAnimationFromName("q3"):
                self.tiles.append(PuzzletInteractableQueenContext.QUEEN_SPRITE.frames[PuzzletInteractableQueenContext.QUEEN_SPRITE.animMap[PuzzletInteractableQueenContext.QUEEN_SPRITE.animActive].indices[0]])
            else:
                self.tiles.append(pygame.Surface((20,20)))
        elif command.opcode == b'\x3e':
            self.tileSolvingMethod = command.operands[0]
        else:
            print("ErrQueenUnkCommand: " + str(command.opcode))
    
    def draw(self, gameDisplay):
        gameDisplay.blit(self.backgroundBs, (0, coreProp.LAYTON_SCREEN_HEIGHT))
        super().draw(gameDisplay)
    
    def evaluateSolution(self):
        for tileIndex in range(len(self.tiles)):        # Check if all tiles are on the board
            if self.tileSlotDict[tileIndex] >= (self.tileBoardSquareDimension ** 2):
                return False
        for slotBuilder in range(self.tileBoardSquareDimension ** 2):
            self.tileSolutions[slotBuilder] = True
        for tileIndex in range(len(self.tiles)):
            if self.tileSolutions[self.tileSlotDict[tileIndex]]:            # If its own square is available
                self.tileSolutions[self.tileSlotDict[tileIndex]] = False     # Invalidate its own square
                tempCoord = [self.tileSlotDict[tileIndex] % self.tileBoardSquareDimension, self.tileSlotDict[tileIndex] // self.tileBoardSquareDimension]
                for invalidateHori in range(self.tileBoardSquareDimension):
                    self.tileSolutions[(tempCoord[1] * self.tileBoardSquareDimension) + invalidateHori] = False   # Invalidate all horizontal squares
                    self.tileSolutions[(self.tileBoardSquareDimension * invalidateHori) + tempCoord[0]] = False    # Invalidate all vertical squares
                for diagonalIndex in range(min(tempCoord)):  # Invalidate diagonal with gradient top-left to bottom-right stopping at the tile
                    self.tileSolutions[((tempCoord[1] - diagonalIndex - 1) * self.tileBoardSquareDimension) + tempCoord[0] - diagonalIndex - 1] = False
                for diagonalIndex in range(self.tileBoardSquareDimension - max(tempCoord) - 1): # Invalidate diagonal with gradient top-left to bottom-right running after the tile
                    self.tileSolutions[((tempCoord[1] + diagonalIndex + 1) * self.tileBoardSquareDimension) + tempCoord[0] + diagonalIndex + 1] = False
                    
                if tempCoord[0] > self.tileBoardSquareDimension // 2 or tempCoord[1] > self.tileBoardSquareDimension // 2:      # If in the top-left quadrant, invert the co-ordinate to get diagonal lengths
                    tempInvertedCoord = [self.tileBoardSquareDimension - 1 - tempCoord[0], self.tileBoardSquareDimension - 1 - tempCoord[1]]
                else:
                    tempInvertedCoord = [tempCoord[1], tempCoord[0]]
                for diagonalIndex in range(tempInvertedCoord[1]):   # The above but for the two remaining diagonals
                    self.tileSolutions[((tempCoord[1] + diagonalIndex + 1) * self.tileBoardSquareDimension) + tempCoord[0] - diagonalIndex - 1] = False
                for diagonalIndex in range(tempInvertedCoord[0]):
                    self.tileSolutions[((tempCoord[1] - diagonalIndex - 1) * self.tileBoardSquareDimension) + tempCoord[0] + diagonalIndex + 1] = False
            else:
                return False
        
        if self.tileSolvingMethod == 1: # Used in 'Too Many Queen 3'; additional constraint that no squares can be free, thankfully this is tracked
            for isUsableSpace in self.tileSolutions:
                if isUsableSpace:
                    return False
        return True

    def reset(self):
        for tileIndex in range(len(self.tiles)):
            if tileIndex not in self.tileTargetIndicesSkip:
                self.tileSlotDict[tileIndex] = len(self.tileTargets) - (8 - tileIndex)

class PuzzletInteractableTraceButtonContext(LaytonContextPuzzlet):

    promptRetry = coreAnim.StaticImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG + "\\retry_trace_0.png")
    promptRetry.pos = ((coreProp.LAYTON_SCREEN_WIDTH - promptRetry.image.get_width()) // 2, ((coreProp.LAYTON_SCREEN_HEIGHT - promptRetry.image.get_height()) // 2) + coreProp.LAYTON_SCREEN_HEIGHT)
    promptPoint = pygame.image.load(coreProp.PATH_ASSET_ANI + "point_trace_0.png").convert_alpha()

    def __init__(self):
        LaytonContextPuzzlet.__init__(self)
        self.buttonSubmit = coreAnim.StaticImage(self.imageButtons.setAnimationFromNameAndReturnInitialFrame("kettei"), x=188, y=159+coreProp.LAYTON_SCREEN_HEIGHT, imageIsSurface=True)
        self.cursorEnableSoftlockRetryScreen = True
        self.cursorIsDrawing = False
        self.cursorColour = pygame.Color(255,255,255)
        self.cursorLineSurface = pygame.Surface((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT))
        self.cursorLineSurface.set_colorkey(pygame.Color(0,0,0))
        self.cursorSelectedItem = None
        self.cursorPoints = []
        self.cursorTotalPoints = [0,0]
        self.cursorTotalPointsLength = 0
        self.traceLocations = []
    
    def cursorAddPoint(self, point):
        if point[1] < coreProp.LAYTON_SCREEN_HEIGHT:
            self.cursorPoints.append((point[0], 0))
        else:
            self.cursorPoints.append((point[0], point[1] - coreProp.LAYTON_SCREEN_HEIGHT))
        self.cursorTotalPoints[0] += point[0]
        self.cursorTotalPoints[1] += point[1]
        self.cursorTotalPointsLength += 1

    def executeCommand(self, command):
        if command.opcode == b'\x42':
            self.cursorColour = pygame.Color(command.operands[0], command.operands[1], command.operands[2])
        elif command.opcode == b'\xd4':
            self.traceLocations.append(nazoElements.TraceLocation(command.operands[0], command.operands[1] + coreProp.LAYTON_SCREEN_HEIGHT,
                                                                  command.operands[2], {"true":True, "false":False}[command.operands[3]]))
        else:
            print("ErrTraceButtonUnkCommand: " + str(command.opcode))
    
    def update(self, gameClockDelta):
        if len(self.cursorPoints) >= 2:
            pygame.draw.lines(self.cursorLineSurface, self.cursorColour, True, self.cursorPoints, 3)
            self.cursorPoints = [self.cursorPoints[-1]]
    
    def findSelectedItem(self):
        if self.cursorTotalPointsLength >= 1:
            traceSelectedLocation = (self.cursorTotalPoints[0] // self.cursorTotalPointsLength, self.cursorTotalPoints[1] // self.cursorTotalPointsLength)
            for locationIndex in range(len(self.traceLocations)):
                if self.traceLocations[locationIndex].wasClicked(traceSelectedLocation):
                    return locationIndex
        return None

    def evaluateSolution(self):
        if self.cursorSelectedItem != None:
            if self.traceLocations[self.cursorSelectedItem].isAnswer:
                return True
        return False

    def draw(self, gameDisplay):
        self.buttonSubmit.draw(gameDisplay)
        gameDisplay.blit(self.cursorLineSurface, (0, coreProp.LAYTON_SCREEN_HEIGHT))
        if not(self.cursorIsDrawing):
            if self.cursorSelectedItem == None:
                if self.cursorEnableSoftlockRetryScreen and self.cursorTotalPointsLength > 0:
                    PuzzletInteractableTraceContext.promptRetry.draw(gameDisplay)
            else:
                gameDisplay.blit(PuzzletInteractableTraceContext.promptPoint,
                                 (self.traceLocations[self.cursorSelectedItem].pos[0], self.traceLocations[self.cursorSelectedItem].pos[1] - PuzzletInteractableTraceContext.promptPoint.get_height()))

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN  and event.pos[1] >= coreProp.LAYTON_SCREEN_HEIGHT:
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
                self.cursorIsDrawing = False
                self.cursorPoints = []
        return False

class PuzzletInteractableTraceContext(PuzzletInteractableTraceButtonContext):
    def __init__(self):
        PuzzletInteractableTraceButtonContext.__init__(self)
        self.cursorEnableSoftlockRetryScreen = False
        self.answerTraceSurface = pygame.Surface((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT))
        self.answerTraceSurface.set_colorkey(pygame.Color(0,0,0))
        self.answerTraceSurface.set_alpha(127)
        self.unkCommand1Points = [] # not final
        self.unkCommand2Points = []
    
    def executeCommand(self, command):
        if command.opcode == b'\x40':
            self.unkCommand1Points.append((command.operands[0], command.operands[1]))
        elif command.opcode == b'\x41':
            self.unkCommand2Points.append((command.operands[0], command.operands[1]))
        elif command.opcode == b'\x42':
            self.cursorColour = pygame.Color(command.operands[0], command.operands[1], command.operands[2])
        else:
            print("ErrTraceUnkCommand: " + str(command.opcode))
    
    def draw(self, gameDisplay):
        super().draw(gameDisplay)
        gameDisplay.blit(self.answerTraceSurface, (0, coreProp.LAYTON_SCREEN_HEIGHT))

    def update(self, gameClockDelta):
        super().update(gameClockDelta)
        if len(self.unkCommand2Points) > 1:
            pygame.draw.polygon(self.answerTraceSurface, (0,0,255), self.unkCommand2Points)
            self.unkCommand2Points = []
        if len(self.unkCommand1Points) > 1:
            pygame.draw.polygon(self.answerTraceSurface, (0,255,0), self.unkCommand1Points)
            self.unkCommand1Points = []

class PuzzletInteractableCutPuzzleContext(LaytonContextPuzzlet):

    def __init__(self):
        LaytonContextPuzzlet.__init__(self)
        self.tileWidth = 2
        self.boardCorner = (0,0)
        self.boardCornerOffset = 1
        self.boardSize = (0,0)
        self.lineSetColor = pygame.Color(255,0,0)
        self.lineGuideColor = pygame.Color(0,255,0)
        self.lines = []
        self.nodes = []
    
    def executeCommand(self, command):
        if command.opcode == b'\xa3':
            self.boardCorner = (command.operands[0] - self.boardCornerOffset, command.operands[1] + self.boardCornerOffset)
        elif command.opcode == b'\xa4':
            self.boardSize = (command.operands[0], command.operands[1])
        elif command.opcode == b'\xa5':
            self.tileWidth = command.operands[0]
            self.boardCornerOffset = self.tileWidth - 1
        elif command.opcode == b'\xa1':
            self.lines.append([(self.boardCorner[0] + command.operands[0] * self.tileWidth, self.boardCorner[1] + coreProp.LAYTON_SCREEN_HEIGHT + command.operands[1] * self.tileWidth),
                               (self.boardCorner[0] + command.operands[2] * self.tileWidth, self.boardCorner[1] + coreProp.LAYTON_SCREEN_HEIGHT + command.operands[3] * self.tileWidth)])
        elif command.opcode == b'\xa0':
            self.nodes.append((self.boardCorner[0] + command.operands[0] * self.tileWidth, self.boardCorner[1] + coreProp.LAYTON_SCREEN_HEIGHT + command.operands[1] * self.tileWidth))
        elif command.opcode == b'\xac':
            self.lineSetColor = pygame.Color(command.operands[0], command.operands[1], command.operands[2])
        elif command.opcode == b'\xad':
            self.lineGuideColor = pygame.Color(command.operands[0], command.operands[1], command.operands[2])
        else:
            print("ErrUnkCutCommand: " + str(command.opcode))
    
    def draw(self, gameDisplay):
        for line in self.lines:
            pygame.draw.lines(gameDisplay, pygame.Color(255,0,0), False, line, 1)
        for center in self.nodes:
            pygame.draw.circle(gameDisplay, pygame.Color(0,0,255), center, 1)

class LaytonPuzzleHandler(coreState.LaytonSubscreen):

    defaultHandlers = {"Match":PuzzletInteractableMatchContext, "Free Button":PuzzletInteractableFreeButtonContext,
                       "On Off":PuzzletInteractableOnOffContext, "Tile":PuzzletInteractableTileContext,
                       "Coin":PuzzletInteractableCoinContext, "Queen":PuzzletInteractableQueenContext,
                       "Trace Button":PuzzletInteractableTraceButtonContext, "Trace":PuzzletInteractableTraceContext,
                       "Cut Puzzle":PuzzletInteractableCutPuzzleContext}

    def __init__(self, puzzleIndex, playerState):
        coreState.LaytonSubscreen.__init__(self)
        self.commandFocus = None
        self.puzzleHintCount = 0

        self.addToStack(LaytonPuzzleBackground(puzzleIndex, playerState))
        self.executeGdScript(gdsLib.gdScript(coreProp.PATH_ASSET_SCRIPT + "qscript\\q" + str(puzzleIndex) + "_param.gds"))
        self.addToStack(LaytonPuzzleUi(puzzleIndex, playerState, self.puzzleHintCount))
        self.addToStack(LaytonTouchOverlay())

    def executeGdScript(self, puzzleScript):
        for command in puzzleScript.commands:
            if command.opcode == b'\x0b':
                try:
                    self.stack[0].backgroundBs = pygame.image.load((coreProp.PATH_ASSET_BG + command.operands[0].replace("?", coreProp.LAYTON_ASSET_LANG))[0:-4] + ".png").convert()
                except:
                    print("Replace background: " + command.operands[0])
            elif command.opcode == b'\x1b':
                if command.operands[0] in LaytonPuzzleHandler.defaultHandlers.keys():
                    self.addToStack(LaytonPuzzleHandler.defaultHandlers[command.operands[0]]())
                    self.commandFocus = self.stack[-1]
                else:
                    print("ErrNoHandler: " + str(command.operands[0]))
            elif command.opcode == b'\x1c':
                self.puzzleHintCount = command.operands[0]
            elif self.commandFocus == None:
                self.executeCommand(command)
            else:
                self.commandFocus.executeCommand(command)
    
    def executeCommand(self, command):
        print("CommandNoTarget: " + str(command.opcode))
    
    def updateSubscreenMethods(self, gameClockDelta):
        if self.commandFocus != None:
            if self.commandFocus.registerVictory:
                print("Victory received.")
                self.commandFocus.registerVictory = False
            elif self.commandFocus.registerLoss:
                print("Loss received.")
                self.commandFocus.registerLoss = False
            elif self.commandFocus.registerQuit:
                self.isContextFinished = True

def play(puzzleIndex, playerState):
    isActive = True
    gameDisplay = pygame.display.set_mode((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT * 2))
    gameClock = pygame.time.Clock()
    gameClockDelta = 0
    rootHandler = LaytonPuzzleHandler(puzzleIndex, playerState)

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
                
        gameClockDelta = gameClock.tick(coreProp.ENGINE_FPS)

playerState = coreState.LaytonPlayerState()
playerState.puzzleLoadData()
playerState.puzzleLoadNames()
playerState.remainingHintCoins = 10
play(16, playerState)    #4:Trace Button, 9:Coin, 10:Connect, 12:River Cross, 13:Slide Puzzle 2, 14:Cup, 16:Queen, 21:Trace, 25:Match, 26:OnOff, 27:Place Target, 34:Tile, 48:FreeButton, 80:Slide, 143:Slide, 101:Cut