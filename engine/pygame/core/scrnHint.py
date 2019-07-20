import coreProp, coreAnim, coreState, pygame

pygame.display.set_mode((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT * 2))

class HintTab():
    def __init__(self, hintText, hintLevel, pos, playerState, isUnlocked=False):
        self.tabLocked = coreAnim.StaticImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG + "\\buttons_hint" + str(hintLevel + 1) + "l.png")
        self.tabUnlocked = coreAnim.StaticImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG + "\\buttons_hint" + str(hintLevel + 1) + ".png")
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
        return self.tabLocked.wasClicked(pos)

class Screen(coreState.LaytonContext):

    buttonQuit = coreAnim.StaticImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG + "\\buttons_modoru.png")
    buttonQuit.pos = (coreProp.LAYTON_SCREEN_WIDTH - buttonQuit.image.get_width(), coreProp.LAYTON_SCREEN_HEIGHT)
    buttonYes = coreAnim.StaticImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG + "\\yesnobuttons_yes.png", x=57, y=coreProp.LAYTON_SCREEN_HEIGHT + 138)
    buttonNo = coreAnim.StaticImage(coreProp.PATH_ASSET_ANI + coreProp.LAYTON_ASSET_LANG + "\\yesnobuttons_no.png", x=137, y=coreProp.LAYTON_SCREEN_HEIGHT + 138)
    
    def __init__(self, puzzleIndex, playerState, puzzleHintCount):
        coreState.LaytonContext.__init__(self)
        self.screenIsOverlay        = True
        self.screenBlockInput       = True
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False

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
                self.hintTabs.append(HintTab(hText.read(), hintTabIndex, (tempTabX, coreProp.LAYTON_SCREEN_HEIGHT), playerState))
            if playerState.puzzleData[self.puzzleIndex].unlockedHintLevel > hintTabIndex:
                self.hintTabs[-1].isUnlocked = True
            tempTabX += self.hintTabs[hintTabIndex].tabLocked.image.get_width()

    def refresh(self):
        self.isContextFinished = False
        if not(self.hintTabs[-1].isUnlocked):
            self.hintLevelActive = self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel
        self.hintStateChanged = True
        self.update(None)

    def draw(self, gameDisplay):
        gameDisplay.blit(self.backgroundBs, (0, coreProp.LAYTON_SCREEN_HEIGHT))
        Screen.buttonQuit.draw(gameDisplay)
        for tab in self.hintTabs[0:self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel + 1]:
            tab.draw(gameDisplay)

        if self.hintTabs[self.hintLevelActive].isUnlocked:
            self.hintTabs[self.hintLevelActive].hText.draw(gameDisplay)
        elif self.playerState.remainingHintCoins >= coreProp.LAYTON_PUZZLE_HINT_COST:
            Screen.buttonYes.draw(gameDisplay)
            Screen.buttonNo.draw(gameDisplay)

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
        if event.type == pygame.MOUSEBUTTONDOWN:
            if Screen.buttonQuit.wasClicked(event.pos):
                self.isContextFinished = True
            indexTab = 0
            for tab in self.hintTabs[0:self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel + 1]:
                if tab.wasClicked(event.pos) and indexTab != self.hintLevelActive:
                    self.hintLevelActive = indexTab
                    self.hintStateChanged = True
                    break
                indexTab += 1

            if not(self.hintTabs[self.hintLevelActive].isUnlocked) and self.playerState.remainingHintCoins >= coreProp.LAYTON_PUZZLE_HINT_COST:
                if Screen.buttonYes.wasClicked(event.pos):
                    self.playerState.remainingHintCoins -= coreProp.LAYTON_PUZZLE_HINT_COST
                    self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel += 1
                    self.hintTabs[self.hintLevelActive].isUnlocked = True
                    self.hintStateChanged = True
                elif Screen.buttonNo.wasClicked(event.pos):
                    self.isContextFinished = True