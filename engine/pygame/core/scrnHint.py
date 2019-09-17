import pygame, coreProp, coreAnim, coreState

pygame.display.set_mode((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT * 2))

class HintTab():
    def __init__(self, hintText, hintLevel, pos, playerState, imageButtons, isUnlocked=False):
        self.tabLocked = coreAnim.StaticButton(imageButtons.setAnimationFromNameAndReturnInitialFrame("hint" + str(hintLevel + 1) + "l"), imageIsSurface = True)
        self.tabUnlocked = coreAnim.StaticImage(imageButtons.setAnimationFromNameAndReturnInitialFrame("hint" + str(hintLevel + 1)), imageIsSurface = True)
        self.hText = coreAnim.TextScroller(playerState.getFont("fontq"), hintText, textPosOffset=(4, coreProp.LAYTON_SCREEN_HEIGHT + 19))
        self.hText.skip()
        self.tabUnlocked.pos = pos
        self.tabLocked.pos = pos
        self.isUnlocked = isUnlocked

    def draw(self, gameDisplay):
        if self.isUnlocked:
            self.tabUnlocked.draw(gameDisplay)
        else:
            self.tabLocked.draw(gameDisplay)
    
    def wasClicked(self, pos):
        return self.tabLocked.getPressedStatus()
    
    def handleEvent(self, event):
        self.tabLocked.handleEvent(event)

class Screen(coreState.LaytonContext):

    buttonYesNo = coreAnim.AnimatedImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG, "yesnobuttons")

    def __init__(self, puzzleIndex, playerState, puzzleHintCount, puzzleAnimFont, imageButtons):
        coreState.LaytonContext.__init__(self)
        self.screenIsOverlay        = True
        self.screenBlockInput       = True
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False

        self.buttonQuit = coreAnim.StaticButton(imageButtons.setAnimationFromNameAndReturnInitialFrame("modoru"), imageIsSurface=True)
        self.buttonQuit.pos = (coreProp.LAYTON_SCREEN_WIDTH - self.buttonQuit.image.get_width(), coreProp.LAYTON_SCREEN_HEIGHT)

        self.puzzleIndex = puzzleIndex
        self.playerState = playerState

        self.backgroundBs = pygame.image.load(coreProp.PATH_ASSET_BG + coreProp.LAYTON_ASSET_LANG + "\\hint_1_3.png").convert()
        
        self.hintLevelActive = self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel
        self.hintTabs = []
        self.hintStateChanged = True
        if self.hintLevelActive > puzzleHintCount - 1:
            self.hintLevelActive = puzzleHintCount - 1
        
        tempTabX = 0
        
        if self.puzzleIndex < 50:
            puzzlePath = coreProp.PATH_ASSET_QTEXT + coreProp.LAYTON_ASSET_LANG + "\\q000\\"
        elif self.puzzleIndex < 100:
            puzzlePath = coreProp.PATH_ASSET_QTEXT + coreProp.LAYTON_ASSET_LANG + "\\q050\\"
        else:
            puzzlePath = coreProp.PATH_ASSET_QTEXT + coreProp.LAYTON_ASSET_LANG + "\\q100\\"

        for hintTabIndex in range(puzzleHintCount):
            with open(puzzlePath + "h_" + str(self.puzzleIndex) + "_" + str(hintTabIndex + 1) + ".txt", 'r') as hText:
                self.hintTabs.append(HintTab(hText.read(), hintTabIndex, (tempTabX, coreProp.LAYTON_SCREEN_HEIGHT), playerState, imageButtons))
            if playerState.puzzleData[self.puzzleIndex].unlockedHintLevel > hintTabIndex:
                self.hintTabs[-1].isUnlocked = True
            tempTabX += self.hintTabs[hintTabIndex].tabLocked.image.get_width()
        
        self.puzzleAnimFont = puzzleAnimFont
        self.buttonYes = coreAnim.AnimatedButton(Screen.buttonYesNo.setAnimationFromNameAndReturnInitialFrame("yes"), Screen.buttonYesNo.setAnimationFromNameAndReturnInitialFrame("yesp"), x=57, y=coreProp.LAYTON_SCREEN_HEIGHT + 138, imageIsSurface=True)
        self.buttonNo = coreAnim.AnimatedButton(Screen.buttonYesNo.setAnimationFromNameAndReturnInitialFrame("no"), Screen.buttonYesNo.setAnimationFromNameAndReturnInitialFrame("nop"), x=137, y=coreProp.LAYTON_SCREEN_HEIGHT + 138, imageIsSurface=True)

    def refresh(self):
        self.isContextFinished = False
        if not(self.hintTabs[-1].isUnlocked):
            self.hintLevelActive = self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel
        self.hintStateChanged = True
        self.update(None)

    def draw(self, gameDisplay):
        gameDisplay.blit(self.backgroundBs, (0, coreProp.LAYTON_SCREEN_HEIGHT))
        self.buttonQuit.draw(gameDisplay)
        for tab in self.hintTabs[0:self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel + 1]:
            tab.draw(gameDisplay)

        if self.hintTabs[self.hintLevelActive].isUnlocked:
            self.hintTabs[self.hintLevelActive].hText.draw(gameDisplay)
        elif self.playerState.remainingHintCoins >= coreProp.LAYTON_PUZZLE_HINT_COST:

            self.puzzleAnimFont.pos = (174,coreProp.LAYTON_SCREEN_HEIGHT + 107)
            for char in format(str(self.playerState.remainingHintCoins), '>3'):
                if self.puzzleAnimFont.setAnimationFromName(char):
                    self.puzzleAnimFont.setInitialFrameFromAnimation()
                    self.puzzleAnimFont.draw(gameDisplay)
                self.puzzleAnimFont.pos = (self.puzzleAnimFont.pos[0] + self.puzzleAnimFont.dimensions[0] - 1, self.puzzleAnimFont.pos[1])

            self.buttonYes.draw(gameDisplay)
            self.buttonNo.draw(gameDisplay)

    def update(self, gameClockDelta):
        # Images need to be preloaded here, this is inefficient
        if self.hintStateChanged:
            if self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel > self.hintLevelActive:
                self.backgroundBs = pygame.image.load(coreProp.PATH_ASSET_BG + "hint_" + str(self.hintLevelActive + 1)  + ".png").convert()
            else:
                if self.playerState.remainingHintCoins >= coreProp.LAYTON_PUZZLE_HINT_COST:
                    self.backgroundBs = pygame.image.load(coreProp.PATH_ASSET_BG + coreProp.LAYTON_ASSET_LANG + "\\hint_" + str(self.hintLevelActive + 1) + "_2.png").convert()
                else:
                    self.backgroundBs = pygame.image.load(coreProp.PATH_ASSET_BG + coreProp.LAYTON_ASSET_LANG + "\\hint_" + str(self.hintLevelActive + 1) + "_3.png").convert()
            self.hintStateChanged = False

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP:
            self.buttonQuit.handleEvent(event)
            if self.buttonQuit.getPressedStatus():
                self.isContextFinished = True

            if not(self.hintTabs[self.hintLevelActive].isUnlocked) and self.playerState.remainingHintCoins >= coreProp.LAYTON_PUZZLE_HINT_COST:
                self.buttonYes.handleEvent(event)
                self.buttonNo.handleEvent(event)
                if self.buttonYes.getPressedStatus():
                    self.playerState.remainingHintCoins -= coreProp.LAYTON_PUZZLE_HINT_COST
                    self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel += 1
                    self.hintTabs[self.hintLevelActive].isUnlocked = True
                    self.hintStateChanged = True
                elif self.buttonNo.getPressedStatus():
                    self.isContextFinished = True
            
            for indexTab, tab in enumerate(self.hintTabs[0:self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel + 1]):
                tab.handleEvent(event)
                if tab.wasClicked(event.pos) and indexTab != self.hintLevelActive:
                    self.hintLevelActive = indexTab
                    self.hintStateChanged = True
                    break
            return True
        return False
