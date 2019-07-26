import coreProp, coreState, coreAnim, pygame, nazoElements, scrnHint, gdsLib

# Testing only
import ctypes; ctypes.windll.user32.SetProcessDPIAware()
pygame.init()

class LaytonContextPuzzlet(coreState.LaytonContext):
    def __init__(self):
        coreState.LaytonContext.__init__(self)
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

    def __init__(self):
        coreState.LaytonContext.__init__(self)
        self.screenIsOverlay        = True
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.imageTouch = pygame.image.load(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG + "\\qend_touch.png").convert_alpha()
        self.imageTouch.set_colorkey(pygame.Color(0,0,0))
        self.imageTouchPos = ((coreProp.LAYTON_SCREEN_WIDTH - self.imageTouch.get_width()) // 2,
                              ((coreProp.LAYTON_SCREEN_HEIGHT - self.imageTouch.get_height()) // 2) + coreProp.LAYTON_SCREEN_HEIGHT)

    def draw(self, gameDisplay):
        gameDisplay.blit(self.imageTouch, self.imageTouchPos)

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.isContextFinished = True

class LaytonPuzzleUi(LaytonContextPuzzlet):

    buttonHint      = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG, "hint_buttons")
    buttonHint.fromImages(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG + "\\hint_buttons.txt")
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
        self.puzzleAnimFont.fromImages(coreProp.PATH_ASSET_ANI + "q_numbers.txt")
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
            self.puzzleQText = coreAnim.TextScroller(self.playerState.getFont("fontq"), qText.read(), targetFramerate=30, textPosOffset=(4,23))
        
        LaytonPuzzleUi.buttonHint.setActiveFrame(self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel)
        self.buttonHintWaitTime = 0
        self.screenHint = scrnHint.Screen(self.puzzleIndex, self.playerState, self.puzzleHintCount, self.puzzleAnimFont)
        
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
        # Game state needs to go here
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.screenBlockInput:
                self.puzzleQText.skip()
                self.screenBlockInput = False       # Free other contexts to use inputs
                self.setStackUpdate()
            elif self.puzzleHintCount > 0 and LaytonPuzzleUi.buttonHint.wasClicked(event.pos):
                self.screenHint.refresh()
                self.screenNextObject = self.screenHint

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

    buttonSubmit        = coreAnim.StaticImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG + "\\buttons_2.png", x=22, y=7+coreProp.LAYTON_SCREEN_HEIGHT)
    buttonReset         = coreAnim.StaticImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG + "\\buttons_3.png", x=99, y=7+coreProp.LAYTON_SCREEN_HEIGHT)
    promptNoMove        = coreAnim.StaticImage(coreProp.PATH_ASSET_BG + coreProp.LAYTON_ASSET_LANG + "\\nomoretouch.png", y=coreProp.LAYTON_SCREEN_HEIGHT)

    def __init__(self):
        LaytonContextPuzzlet.__init__(self)
        self.elements = []
        self.elementFocus = None
        self.elementClickOffset = (0,0)
        self.puzzleSoftlockMoveScreen = False
        self.puzzleMoveLimit = None
        self.puzzleMoveFont  = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, "inputnumbers")
        self.puzzleMoveFont.fromImages(coreProp.PATH_ASSET_ANI + "inputnumbers.txt")
        self.puzzleCurrentMoves = 0
    
    def draw(self, gameDisplay):
        PuzzletInteractableDragContext.buttonSubmit.draw(gameDisplay)
        PuzzletInteractableDragContext.buttonReset.draw(gameDisplay)
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
            if PuzzletInteractableDragContext.buttonSubmit.wasClicked(event.pos):
                if self.evaluateSolution():
                    self.setVictory()
                else:
                    self.setLoss()
            elif PuzzletInteractableDragContext.buttonReset.wasClicked(event.pos):
                self.reset()
            elif not(self.puzzleSoftlockMoveScreen):
                if self.puzzleMoveLimit == None or self.puzzleCurrentMoves < self.puzzleMoveLimit:
                    for elementIndex in range(len(self.elements)):
                        if self.elements[elementIndex].wasClicked(event.pos):
                            self.elementFocus = elementIndex
                            self.elementClickOffset = (event.pos[0] - self.elements[elementIndex].pos[0], event.pos[1] - self.elements[elementIndex].pos[1])
                            break # To-do: Sort so clickable element is always the topmost, as these can overlap unlike tiles
                else:
                    self.puzzleSoftlockMoveScreen = True
        # Note: MOUSEBUTTONUP is not handled by default because this is where handlers differ

class PuzzletInteractableMatchContext(PuzzletInteractableDragContext):

    matchImage          = pygame.image.load(coreProp.PATH_ASSET_ANI + "match_match.png").convert_alpha()
    matchShadowImage    = pygame.image.load(coreProp.PATH_ASSET_ANI + "match_shadow.png").convert_alpha()

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
    
    COIN_ACCEPTABLE_REGION = 4
    COIN_SHADOW_OFFSET = 1
    backgroundCoin = pygame.image.load(coreProp.PATH_ASSET_BG + "coin_bg.png").convert()
    spriteCoin = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, "coin")
    spriteCoin.fromImages(coreProp.PATH_ASSET_ANI + "coin.txt")
    spriteShadow = nazoElements.IndependentTile(spriteCoin, "shadow")

    def __init__(self):
        PuzzletInteractableDragContext.__init__(self)
        self.posInitial = []
        self.posChanged = []
    
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
            self.elements[self.elementFocus].pos = (pygame.mouse.get_pos()[0] - self.elementClickOffset[0], pygame.mouse.get_pos()[1] - self.elementClickOffset[1])

    def handleEvent(self, event):
        super().handleEvent(event)
        if event.type == pygame.MOUSEBUTTONUP and self.elementFocus != None:
            self.elements.append(self.elements.pop(self.elementFocus))          # Place last interacted element on top
            self.elementFocus = None
            self.puzzleCurrentMoves += 1
            self.elementClickOffset = (0,0)
    
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

    buttonSubmit = coreAnim.StaticImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG + "\\buttons_2.png", x=186, y=158+coreProp.LAYTON_SCREEN_HEIGHT)

    def __init__(self):
        PuzzletInteractableFreeButtonContext.__init__(self)
        self.drawFlagsInteractableElementsActiveCount = 0
    
    def draw(self, gameDisplay):
        super().draw(gameDisplay)
        PuzzletInteractableOnOffContext.buttonSubmit.draw(gameDisplay)
    
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for elementIndex in range(len(self.interactableElements)):
                if self.interactableElements[elementIndex].wasClicked(event.pos):
                    self.drawFlagsInteractableElements[elementIndex] = not(self.drawFlagsInteractableElements[elementIndex])
                    if self.drawFlagsInteractableElements[elementIndex]:
                        self.drawFlagsInteractableElementsActiveCount += 1
                    else:
                        self.drawFlagsInteractableElementsActiveCount -= 1
            
            if PuzzletInteractableOnOffContext.buttonSubmit.wasClicked(event.pos):
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
    buttonSubmit = coreAnim.StaticImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG + "\\buttons_2.png", x=188, y=159+coreProp.LAYTON_SCREEN_HEIGHT)
    buttonRestart = coreAnim.StaticImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG + "\\restart.png", x=7, y=7+coreProp.LAYTON_SCREEN_HEIGHT)

    def __init__(self):
        LaytonContextPuzzlet.__init__(self)
        self.tileDict = {}                  # Stores the core asset used for all tiles

        self.tiles = []
        self.tileTargets = []
        self.tileSolutions = []
        self.tileSlotDict = {}
        self.tileSolutionLoadIndex = 0
        self.tileClickOffset = (0,0)
        self.tileActive = None
    
    def draw(self, gameDisplay):
        PuzzletInteractableTileContext.buttonSubmit.draw(gameDisplay)
        PuzzletInteractableTileContext.buttonRestart.draw(gameDisplay)
        for tileIndex in range(len(self.tiles)):
            if tileIndex != self.tileActive:
                self.tiles[tileIndex].draw(gameDisplay, self.tileTargets[self.tileSlotDict[tileIndex]])
        if self.tileActive != None:
            self.tiles[self.tileActive].draw(gameDisplay, (pygame.mouse.get_pos()[0] - self.tileClickOffset[0], pygame.mouse.get_pos()[1] - self.tileClickOffset[1]))
    
    def executeCommand(self, command):
        if command.opcode == b'\x73':                   # Place tile
            if command.operands[2] not in self.tileDict.keys():
                self.tileDict[command.operands[2]] = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI, command.operands[2][0:-4])
            self.tileSlotDict[len(self.tiles)] = len(self.tiles)
            self.tiles.append(nazoElements.Tile(self.tileDict[command.operands[2]], command.operands[3]))
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
    
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            if self.tileActive != None:
                tileTargetIndex = 0
                for tileTarget in self.tileTargets:
                    if (abs(event.pos[0] - self.tileClickOffset[0] - tileTarget[0]) <= PuzzletInteractableTileContext.TILE_SWITCH_REGION and
                        abs(event.pos[1] - self.tileClickOffset[1]- tileTarget[1]) <= PuzzletInteractableTileContext.TILE_SWITCH_REGION):
                        isOccupied = False
                        for tileIndex in range(len(self.tiles)):
                            if self.tileSlotDict[tileIndex] == tileTargetIndex:
                                isOccupied = True
                                break
                        if isOccupied:  # Switch slots
                            self.tileSlotDict[tileIndex] = self.tileSlotDict[self.tileActive]
                        self.tileSlotDict[self.tileActive] = tileTargetIndex
                        break
                    tileTargetIndex += 1
                self.tileActive = None
            self.tileClickOffset = (0,0)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if PuzzletInteractableTileContext.buttonSubmit.wasClicked(event.pos):
                if self.tileSlotDict in self.tileSolutions:
                    self.setVictory()
                else:
                    self.setLoss()
            elif PuzzletInteractableTileContext.buttonRestart.wasClicked(event.pos):
                for tileIndex in range(len(self.tiles)):
                    self.tileSlotDict[tileIndex] = tileIndex
            else:
                self.tileActive = None
                for tileIndex in range(len(self.tiles)):
                    if self.tiles[tileIndex].wasClicked(event.pos, self.tileTargets[self.tileSlotDict[tileIndex]]):
                        self.tileActive = tileIndex
                        self.tileClickOffset = (event.pos[0] - self.tileTargets[self.tileSlotDict[tileIndex]][0], event.pos[1] - self.tileTargets[self.tileSlotDict[tileIndex]][1])
                        break   # Multi-touch is not supported anyway

class LaytonPuzzleHandler(coreState.LaytonSubscreen):

    defaultHandlers = {"Match":PuzzletInteractableMatchContext, "Free Button":PuzzletInteractableFreeButtonContext,
                       "On Off":PuzzletInteractableOnOffContext, "Tile":PuzzletInteractableTileContext,
                       "Coin":PuzzletInteractableCoinContext}

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
play(9, playerState)    #9:Coin, # 25:Match, 26:OnOff, 34:Tile, 48:FreeButton