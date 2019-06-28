import coreProp, coreState, coreAnim, pygame

class LaytonPuzzleHandler(coreState.LaytonContext):
    
    backgroundTs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\" + coreProp.LAYTON_ASSET_LANG + r"\q_bg.png")
    buttonSkip = None
    
    def __init__(self, playerState, puzzleIndex, puzzleScript, puzzleEnable = True):

        coreState.LaytonContext.__init__(self)
        
        try:
            with open(coreProp.LAYTON_ASSET_ROOT + "bg\\q" + str(puzzleIndex) + "_bg.png", 'rb') as imgTest:
                pass
            self.backgroundBs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\q" + str(puzzleIndex) + "_bg.png")
        except FileNotFoundError:
            print("[NZGEN] No default background found!")
            self.backgroundBs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\q" + str(puzzleIndex) + "_bg.png")

        self.playerState            = playerState
        self.puzzleEnable           = puzzleEnable
        self.puzzleScript           = puzzleScript
        self.puzzleIndex            = puzzleIndex
        self.puzzleInputWaiting     = True
        self.puzzleQText            = coreAnim.TextScroller("")
        self.puzzleIndexText        = coreAnim.AnimatedText(initString=str(self.puzzleIndex))
        self.puzzlePicarotsText     = coreAnim.AnimatedText(initString=str(self.playerState.puzzleData[self.puzzleIndex].getValue()))
        self.puzzleHintCoinsText    = coreAnim.AnimatedText(initString=str(self.playerState.remainingHintCoins))

        self.puzzleMoveLimit = None
        
        self.load()

    def executeGdScript(self):
        for command in self.puzzleScript.commands:
            if command.opcode == b'\x0b':
                print("Replace background: " + command.operands[0])
                break
    
    def load(self):
        # Load a fresh puzzle state, useful when restarting the puzzle
        if self.puzzleIndex < 50:
            puzzlePath = coreProp.LAYTON_ASSET_ROOT + "qtext\\" + coreProp.LAYTON_ASSET_LANG + "\\q000\\"
        elif self.puzzleIndex < 100:
            puzzlePath = coreProp.LAYTON_ASSET_ROOT + "qtext\\" + coreProp.LAYTON_ASSET_LANG + "\\q050\\"
        else:
            puzzlePath = coreProp.LAYTON_ASSET_ROOT + "qtext\\" + coreProp.LAYTON_ASSET_LANG + "\\q100\\"
            
        # Load the puzzle qText
        with open(puzzlePath + "q_" + str(self.puzzleIndex) + ".txt", 'r') as qText:
            self.puzzleQText = coreAnim.TextScroller(qText.read())

        self.executeGdScript()
        self.puzzleInputWaiting = True
        self.puzzlePicarotsText = coreAnim.AnimatedText(initString=str(self.playerState.puzzleData[self.puzzleIndex].getValue()))
        
    def update(self):
        if self.puzzleEnable:
            self.puzzleQText.update()
            self.puzzleHintCoinsText.update()

    def skip(self):
        # Play the skip sound as well
        if self.puzzleEnable:
            self.puzzleQText.skip()

    def drawUi(self, gameDisplay):
        pass
    
    def draw(self, gameDisplay):
        gameDisplay.blit(LaytonPuzzleHandler.backgroundTs, (0,0))
        gameDisplay.blit(self.backgroundBs, (0,192))
        self.puzzleIndexText.draw(gameDisplay, location=(30, 6))
        self.puzzlePicarotsText.draw(gameDisplay, location=(88,6))
        self.puzzleHintCoinsText.draw(gameDisplay, location=(231,6))
        self.puzzleQText.draw(gameDisplay)
        if self.puzzleInputWaiting:
            # Draw the 'touch' waitscreen
            pass

    def setLoss(self):
        print("Player loses.")
        pass

    def setVictory(self):
        print("Player wins.")
        pass
    
    def getUpdatedPlayerState(self):
        return self.playerState
    
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.puzzleEnable:
            self.skip()
            self.puzzleInputWaiting = False
