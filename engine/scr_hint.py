import pygame, conf, anim, state
from file import FileInterface

pygame.display.set_mode((conf.LAYTON_SCREEN_WIDTH, conf.LAYTON_SCREEN_HEIGHT * 2))

# data_lt2/bg/nazo/system/en/jitenhint_<n>.arc is the unlock screen? Strange

class HintTab():
    def __init__(self, hintText, hintLevel, pos, playerState, imageLockedButton, imageUnlockedButton, isUnlocked=False):
        self.tabLocked      = anim.AnimatedButton(imageLockedButton, None, imageIsSurface=True, useButtonFromAnim=True, x=pos[0], y=pos[1])
        self.tabUnlocked    = anim.AnimatedButton(imageUnlockedButton, None, imageIsSurface=True, useButtonFromAnim=True, x=pos[0], y=pos[1])

        self.hText = anim.TextScroller(playerState.getFont("fontq"), hintText, textPosOffset=(20, conf.LAYTON_SCREEN_HEIGHT + 43))
        self.hText.skip()
        self.isUnlocked = isUnlocked

    def draw(self, gameDisplay):
        if self.isUnlocked:
            self.tabUnlocked.draw(gameDisplay)
        else:
            self.tabLocked.draw(gameDisplay)
    
    def wasClicked(self, pos):
        self.tabUnlocked.getPressedStatus()
        return self.tabLocked.getPressedStatus()
    
    def handleEvent(self, event):
        self.tabUnlocked.handleEvent(event)
        return self.tabLocked.handleEvent(event)

class Screen(state.LaytonContext):

    def __init__(self, puzzleIndex, puzzleData, playerState, puzzleAnimFont, imageYesButton, imageNoButton, imageBackButton):
        state.LaytonContext.__init__(self)
        self.screenIsOverlay        = True
        self.screenBlockInput       = True
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False

        self.buttonQuit = anim.AnimatedButton(imageBackButton, None, imageIsSurface=True, useButtonFromAnim=True)
        self.buttonQuit.setPos((conf.LAYTON_SCREEN_WIDTH - self.buttonQuit.image.get_width(), conf.LAYTON_SCREEN_HEIGHT))

        self.puzzleIndex = puzzleIndex
        self.playerState = playerState

        self.backgroundBs = pygame.image.load(conf.PATH_ASSET_BG + conf.LAYTON_ASSET_LANG + "\\hint_1_3.png").convert()
        
        self.hintLevelActive = self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel
        self.hintTabs = []
        self.hintStateChanged = True
        if self.hintLevelActive > 2:
            self.hintLevelActive = 2
        
        tempTabX = 8
        tempTabY = 4
        for hintTabIndex in range(3):
            imageButtonsLocked = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "nazo/system/" + conf.LAYTON_ASSET_LANG, "hintlock" + str(hintTabIndex + 1))
            imageButtonsUnlocked = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "nazo/system/" + conf.LAYTON_ASSET_LANG, "hint" + str(hintTabIndex + 1))
            self.hintTabs.append(HintTab(puzzleData.textHint[hintTabIndex], hintTabIndex, (tempTabX, conf.LAYTON_SCREEN_HEIGHT + tempTabY), playerState,
                                         imageButtonsLocked, imageButtonsUnlocked))
            if playerState.puzzleData[self.puzzleIndex].unlockedHintLevel > hintTabIndex:
                self.hintTabs[-1].isUnlocked = True
            tempTabX += self.hintTabs[hintTabIndex].tabLocked.image.get_width() + 1
        
        self.puzzleAnimFont = puzzleAnimFont
        self.buttonYes = anim.AnimatedButton(imageYesButton, None, imageIsSurface=True, useButtonFromAnim=True, x=57, y=conf.LAYTON_SCREEN_HEIGHT + 138)
        self.buttonNo = anim.AnimatedButton(imageNoButton, None, imageIsSurface=True, useButtonFromAnim=True, x=137, y=conf.LAYTON_SCREEN_HEIGHT + 138)

    def refresh(self):
        self.isContextFinished = False
        if not(self.hintTabs[-1].isUnlocked):
            self.hintLevelActive = self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel
        self.hintStateChanged = True
        self.update(None)

    def draw(self, gameDisplay):
        gameDisplay.blit(self.backgroundBs, (0, conf.LAYTON_SCREEN_HEIGHT))
        self.buttonQuit.draw(gameDisplay)

        for tab in self.hintTabs[0:self.playerState.puzzleData[self.puzzleIndex].unlockedHintLevel + 1]:
            tab.draw(gameDisplay)

        if self.hintTabs[self.hintLevelActive].isUnlocked:
            self.hintTabs[self.hintLevelActive].hText.draw(gameDisplay)
        elif self.playerState.remainingHintCoins >= conf.LAYTON_PUZZLE_HINT_COST:

            self.puzzleAnimFont.pos = (194, conf.LAYTON_SCREEN_HEIGHT + 111)
            for char in str(self.playerState.remainingHintCoins):
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
                self.backgroundBs = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "nazo/system/" + conf.LAYTON_ASSET_LANG + "/hint_" + str(self.hintLevelActive + 1) + ".arc")
            else:
                if self.playerState.remainingHintCoins >= conf.LAYTON_PUZZLE_HINT_COST:
                    self.backgroundBs = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "nazo/system/" + conf.LAYTON_ASSET_LANG + "/hint_" + str(self.hintLevelActive + 1) + "_2.arc")
                else:
                    self.backgroundBs = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "nazo/system/" + conf.LAYTON_ASSET_LANG + "/hint_" + str(self.hintLevelActive + 1) + "_3.arc")
            self.hintStateChanged = False

    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.MOUSEBUTTONUP:
            self.buttonQuit.handleEvent(event)
            if self.buttonQuit.getPressedStatus():
                self.isContextFinished = True
            else:
                if not(self.hintTabs[self.hintLevelActive].isUnlocked) and self.playerState.remainingHintCoins >= conf.LAYTON_PUZZLE_HINT_COST:
                    self.buttonYes.handleEvent(event)
                    self.buttonNo.handleEvent(event)
                    if self.buttonYes.getPressedStatus():
                        self.playerState.remainingHintCoins -= conf.LAYTON_PUZZLE_HINT_COST
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