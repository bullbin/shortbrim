import coreProp, coreState, coreAnim, pygame, scrnHint

class LaytonPuzzleHandler(coreState.LaytonContext):
    
    backgroundTs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\" + coreProp.LAYTON_ASSET_LANG + "\\q_bg.png")
    buttonSkip = None
    buttonHint = coreAnim.AnimatedImage("ani\\" + coreProp.LAYTON_ASSET_LANG + "\\hint_buttons.png")
    buttonHint.pos = (coreProp.LAYTON_SCREEN_WIDTH - buttonHint.image.get_width(), coreProp.LAYTON_SCREEN_HEIGHT)
    
    def __init__(self, playerState, puzzleIndex, puzzleScript, puzzleEnable = True, puzzleShowHint = False):

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

        self.puzzleSubcontexts      = coreState.LaytonContextStack()
        self.puzzleFader            = coreAnim.Fader()

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

        if len(self.puzzleSubcontexts) > 0:
            if self.puzzleSubcontexts.getCurrentItem().isContextFinished:
                pass

        if self.puzzleSubcontexts.transitioning:
            if self.puzzleSubcontexts.transitioningIn:
                if self.puzzleFader.strength < 1:
                    self.puzzleFader.strength += 0.1
                elif self.puzzleFader.strength >= 1:
                    # The fader has finished fading in
                    self.puzzleFader.strength = 1
                    self.puzzleSubcontexts.transitioningIn = False
                    self.puzzleSubcontexts.transitioningOut = True

            else:
                if self.puzzleFader.strength > 0:
                    self.puzzleFader.strength -= 0.1
                else:
                    # The fader has finished fading out
                    self.puzzleFader.strength = 0
                    # Fading now complete, free context switching lock
                    self.puzzleSubcontexts.transitioning = False
                    self.puzzleSubcontexts.transitioningOut = False

    def skip(self):
        # Play the skip sound as well
        if self.puzzleEnable:
            self.puzzleQText.skip()

    def drawUi(self, gameDisplay):
        LaytonPuzzleHandler.buttonHint.draw(gameDisplay)
    
    def draw(self, gameDisplay):
        if self.puzzleSubcontexts.transitioning:
            if self.puzzleSubcontexts.transitioningIn:
                # Draw the lower layer, then the fader
                if len(self.puzzleSubcontexts.stack) == 1:
                    self.drawAsGameLogic(gameDisplay)
                    self.drawUi(gameDisplay)
                else:
                    self.puzzleSubcontexts.stack[-2].draw(gameDisplay)
            else:
                # Draw the upper layer, then the fader
                self.puzzleSubcontexts.stack[-1].draw(gameDisplay)
            self.puzzleFader.draw(gameDisplay)
        
        else:
            if len(self.puzzleSubcontexts.stack) > 0:
                self.puzzleSubcontexts.stack[-1].draw(gameDisplay)
            else:
                self.drawAsGameLogic(gameDisplay)
                self.drawUi(gameDisplay)
    
    def drawAsGameLogic(self, gameDisplay):
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
    
    def handleEvent(self, event):
        
        if len(self.puzzleSubcontexts.stack) > 0:
            self.puzzleSubcontexts.getCurrentItem().handleEvent(event)
        else:
            if self.puzzleEnable:
                if self.puzzleInputWaiting:
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.skip()
                        self.puzzleInputWaiting = False

                elif event.type == pygame.MOUSEBUTTONDOWN and LaytonPuzzleHandler.buttonHint.wasClicked(event.pos):
                    self.puzzleSubcontexts.stack.append(scrnHint.Screen(self.puzzleIndex))
                    #self.puzzleSubcontexts.transitioning = True
                    #self.puzzleSubcontexts.transitioningIn = True
                    #self.puzzleSubcontexts.transitioningOut = False
                    
                else:
                    self.handleEventAsGameLogic(event)
    
    def handleEventAsGameLogic(self, event):
        # Code used to interact with the puzzle elements needs to be in here
        pass