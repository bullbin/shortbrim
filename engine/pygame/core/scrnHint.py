import coreProp, coreAnim, coreState, pygame

class HintTab():
    def __init__(self, hintText, hintLevel, pos, isUnlocked=False):
        self.tabLocked = coreAnim.AnimatedImage("ani\\" + coreProp.LAYTON_ASSET_LANG + "\\buttons_hint" + str(hintLevel + 1) + "l.png")
        self.tabUnlocked = coreAnim.AnimatedImage("ani\\" + coreProp.LAYTON_ASSET_LANG + "\\buttons_hint" + str(hintLevel + 1) + ".png")
        self.hText = coreAnim.TextScroller(hintText, textPosOffset=(4, coreProp.LAYTON_SCREEN_HEIGHT + 24))
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

    buttonQuit = coreAnim.AnimatedImage("ani\\" + coreProp.LAYTON_ASSET_LANG + "\\buttons_modoru.png")
    buttonQuit.pos = (coreProp.LAYTON_SCREEN_WIDTH - buttonQuit.image.get_width(), coreProp.LAYTON_SCREEN_HEIGHT)
    buttonYes = coreAnim.AnimatedImage("ani\\" + coreProp.LAYTON_ASSET_LANG + "\\yesnobuttons_yes.png")
    buttonYes.pos = (40, coreProp.LAYTON_SCREEN_HEIGHT + 128)
    buttonNo = coreAnim.AnimatedImage("ani\\" + coreProp.LAYTON_ASSET_LANG + "\\yesnobuttons_no.png")
    buttonNo.pos = (140, coreProp.LAYTON_SCREEN_HEIGHT + 128)
    
    def __init__(self, puzzleIndex, playerState, puzzleHintCount):
        coreState.LaytonContext.__init__(self)
        self.screenIsOverlay        = True
        self.screenBlockInput       = True
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False

        self.puzzleIndex = puzzleIndex
        self.playerState = playerState

        self.backgroundBs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\" + coreProp.LAYTON_ASSET_LANG + "\\hint_1_3.png")
        
        self.hintLevelActive = self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel
        self.hintTabs = []
        self.hintStateChanged = True
        if self.hintLevelActive > puzzleHintCount - 1:
            self.hintLevelActive = puzzleHintCount - 1
        
        tempTabX = 0
        
        if self.puzzleIndex < 50:
            puzzlePath = coreProp.LAYTON_ASSET_ROOT + "qtext\\" + coreProp.LAYTON_ASSET_LANG + "\\q000\\"
        elif self.puzzleIndex < 100:
            puzzlePath = coreProp.LAYTON_ASSET_ROOT + "qtext\\" + coreProp.LAYTON_ASSET_LANG + "\\q050\\"
        else:
            puzzlePath = coreProp.LAYTON_ASSET_ROOT + "qtext\\" + coreProp.LAYTON_ASSET_LANG + "\\q100\\"

        for hintTabIndex in range(puzzleHintCount):
            with open(puzzlePath + "h_" + str(self.puzzleIndex) + "_" + str(hintTabIndex + 1) + ".txt", 'r') as hText:
                self.hintTabs.append(HintTab(hText.read(), hintTabIndex, (tempTabX, coreProp.LAYTON_SCREEN_HEIGHT)))
            if playerState.puzzleData[self.puzzleIndex].unlockedHintLevel > hintTabIndex:
                self.hintTabs[-1].isUnlocked = True
            tempTabX += self.hintTabs[hintTabIndex].tabLocked.image.get_width()

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

    def update(self):
        # Images need to be preloaded here, this is inefficient
        if self.hintStateChanged:
            if self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel > self.hintLevelActive:
                self.backgroundBs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\hint_" + str(self.hintLevelActive + 1)  + ".png")
            else:
                if self.playerState.remainingHintCoins >= coreProp.LAYTON_PUZZLE_HINT_COST:
                    self.backgroundBs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\" + coreProp.LAYTON_ASSET_LANG + "\\hint_" + str(self.hintLevelActive + 1) + "_2.png")
                else:
                    self.backgroundBs = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + "bg\\" + coreProp.LAYTON_ASSET_LANG + "\\hint_" + str(self.hintLevelActive + 1) + "_3.png")
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