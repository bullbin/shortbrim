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

class LaytonPuzzleUi(LaytonContextPuzzlet):

    buttonHint      = coreAnim.AnimatedImage(coreProp.LAYTON_ASSET_ROOT + "ani\\" + coreProp.LAYTON_ASSET_LANG, "hint_buttons")
    buttonHint.fromImages(coreProp.LAYTON_ASSET_ROOT + "ani\\" + coreProp.LAYTON_ASSET_LANG + "\\hint_buttons.txt")
    buttonHint.pos  = (coreProp.LAYTON_SCREEN_WIDTH - buttonHint.dimensions[0], coreProp.LAYTON_SCREEN_HEIGHT)
    buttonHintFlashDelay = 15000

    def __init__(self, puzzleIndex, playerState, puzzleHintCount):
        LaytonContextPuzzlet.__init__(self)
        self.screenIsOverlay        = True
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True

        self.puzzleIndex = puzzleIndex
        self.playerState = playerState
        self.puzzleIndexText        = coreAnim.AnimatedText(initString=str(self.puzzleIndex))
        self.puzzlePicarotsText     = coreAnim.AnimatedText(initString=str(self.playerState.puzzleData[self.puzzleIndex].getValue()))
        self.puzzleHintCoinsText    = coreAnim.AnimatedText(initString=str(self.playerState.remainingHintCoins))
        self.puzzleHintCount        = puzzleHintCount

        if self.puzzleIndex < 50:
            puzzlePath = coreProp.LAYTON_ASSET_ROOT + "qtext\\" + coreProp.LAYTON_ASSET_LANG + "\\q000\\"
        elif self.puzzleIndex < 100:
            puzzlePath = coreProp.LAYTON_ASSET_ROOT + "qtext\\" + coreProp.LAYTON_ASSET_LANG + "\\q050\\"
        else:
            puzzlePath = coreProp.LAYTON_ASSET_ROOT + "qtext\\" + coreProp.LAYTON_ASSET_LANG + "\\q100\\"
            
        # Load the puzzle qText
        with open(puzzlePath + "q_" + str(self.puzzleIndex) + ".txt", 'r') as qText:
            self.puzzleQText = coreAnim.TextScroller(qText.read())
        
        LaytonPuzzleUi.buttonHint.setActiveFrame(self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel)
        self.buttonHintWaitTime = 0
        self.screenHint = scrnHint.Screen(self.puzzleIndex, self.playerState, self.puzzleHintCount)
        
    def update(self, gameClockDelta):
        self.puzzleHintCoinsText    = coreAnim.AnimatedText(initString=str(self.playerState.remainingHintCoins))
        self.puzzleQText.update(gameClockDelta)
        if not(self.screenBlockInput):
            LaytonPuzzleUi.buttonHint.update(gameClockDelta)
            if LaytonPuzzleUi.buttonHint.animActive == None or LaytonPuzzleUi.buttonHint.animActiveFrame == None:
                if LaytonPuzzleUi.buttonHint.animActiveFrame == None:
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
        self.puzzleIndexText.draw(gameDisplay, location=(30, 6))
        self.puzzlePicarotsText.draw(gameDisplay, location=(88,6))
        self.puzzleHintCoinsText.draw(gameDisplay, location=(231,6))

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

    backgroundTs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\" + coreProp.LAYTON_ASSET_LANG + "\\q_bg.png")

    def __init__(self, puzzleIndex, playerState):
        coreState.LaytonContext.__init__(self)
        
        # Set screen variables
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False
        self.screenBlockInput       = True

        try:
            self.backgroundBs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\q" + str(puzzleIndex) + "_bg.png")
        except:
            print("[APPLET] BG: No default background found!")
            self.backgroundBs = pygame.Surface((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT)).convert()

    def draw(self, gameDisplay):
        gameDisplay.blit(LaytonPuzzleBackground.backgroundTs, (0,0))
        gameDisplay.blit(self.backgroundBs, (0,coreProp.LAYTON_SCREEN_HEIGHT))

class PuzzletInteractableMatchContext(LaytonContextPuzzlet):

    matchImage          = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "ani\\match_match.png").convert_alpha()
    matchShadowImage    = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "ani\\match_shadow.png").convert_alpha()
    buttonSubmit        = coreAnim.StaticImage("ani\\" + coreProp.LAYTON_ASSET_LANG + "\\buttons_2.png", x=22, y=7+coreProp.LAYTON_SCREEN_HEIGHT)
    buttonReset         = coreAnim.StaticImage("ani\\" + coreProp.LAYTON_ASSET_LANG + "\\buttons_3.png", x=99, y=7+coreProp.LAYTON_SCREEN_HEIGHT)

    def __init__(self):
        LaytonContextPuzzlet.__init__(self)
        self.matches = []
        self.puzzleMoveLimit = None
    
    def executeCommand(self, command):
        if command.opcode == b'\x2a':
            self.matches.append(nazoElements.Match(PuzzletInteractableMatchContext.matchImage, PuzzletInteractableMatchContext.matchShadowImage,
                                                   command.operands[0],command.operands[1]+coreProp.LAYTON_SCREEN_HEIGHT,
                                                   command.operands[2]))
        elif command.opcode == b'\x2b':
            pass
        elif command.opcode == b'\x27':
            self.puzzleMoveLimit = command.operands[0]
        else:
            print("ErrUnrecognised: " + str(command.opcode))
    
    def draw(self, gameDisplay):
        for match in self.matches:
            match.draw(gameDisplay)
        PuzzletInteractableMatchContext.buttonSubmit.draw(gameDisplay)
        PuzzletInteractableMatchContext.buttonReset.draw(gameDisplay)
    
    def evaluateSolution(self):
        pass
    
    def reset(self):
        pass

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if PuzzletInteractableMatchContext.buttonSubmit.wasClicked(event.pos):
                self.evaluateSolution()
            elif PuzzletInteractableMatchContext.buttonReset.wasClicked(event.pos):
                self.reset()

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
            
            self.interactableElements.append(coreAnim.AnimatedImage(coreProp.LAYTON_ASSET_ROOT + "ani\\", imageName,
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

        elif event.type == pygame.MOUSEBUTTONUP:
            for elementIndex in range(len(self.interactableElements)):
                if self.drawFlagsInteractableElements[elementIndex] == 1:
                    if elementIndex in self.solutionElements:
                        self.setVictory()
                    else:
                        self.setLoss()
                self.drawFlagsInteractableElements[elementIndex] = False

class PuzzletInteractableOnOff(PuzzletInteractableFreeButtonContext):

    buttonSubmit = coreAnim.StaticImage("ani\\" + coreProp.LAYTON_ASSET_LANG + "\\buttons_2.png", x=186, y=158+coreProp.LAYTON_SCREEN_HEIGHT)

    def __init__(self):
        PuzzletInteractableFreeButtonContext.__init__(self)
        self.drawFlagsInteractableElementsActiveCount = 0
    
    def draw(self, gameDisplay):
        super().draw(gameDisplay)
        PuzzletInteractableOnOff.buttonSubmit.draw(gameDisplay)
    
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for elementIndex in range(len(self.interactableElements)):
                if self.interactableElements[elementIndex].wasClicked(event.pos):
                    self.drawFlagsInteractableElements[elementIndex] = not(self.drawFlagsInteractableElements[elementIndex])
                    if self.drawFlagsInteractableElements[elementIndex]:
                        self.drawFlagsInteractableElementsActiveCount += 1
                    else:
                        self.drawFlagsInteractableElementsActiveCount -= 1
            
            if PuzzletInteractableOnOff.buttonSubmit.wasClicked(event.pos):
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

class LaytonPuzzleHandler(coreState.LaytonSubscreen):

    defaultHandlers = {"Match":PuzzletInteractableMatchContext, "Free Button":PuzzletInteractableFreeButtonContext,
                       "On Off":PuzzletInteractableOnOff}

    def __init__(self, puzzleIndex, playerState):
        coreState.LaytonSubscreen.__init__(self)
        self.commandFocus = None
        
        self.puzzleHintCount = 0

        self.addToStack(LaytonPuzzleBackground(puzzleIndex, playerState))
        self.executeGdScript(gdsLib.gdScript(coreProp.LAYTON_ASSET_ROOT + "script\\qscript\\q" + str(puzzleIndex) + "_param.gds"))
        self.addToStack(LaytonPuzzleUi(puzzleIndex, playerState, self.puzzleHintCount))

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
                
        gameClockDelta = gameClock.tick(coreProp.LAYTON_ENGINE_FPS)

playerState = coreState.LaytonPlayerState()
playerState.puzzleLoadData()
playerState.puzzleLoadNames()
playerState.remainingHintCoins = 10
play(4, playerState)    # 25:Match, 26:OnOff, 48:FreeButton