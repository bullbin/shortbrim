import pygame, han_nazo_element, scr_hint, conf, state, anim, script
from os import path
from math import sqrt
from file import FileInterface
from hat_io import asset_dat

# Testing only
import ctypes; ctypes.windll.user32.SetProcessDPIAware()
pygame.init()

class LaytonContextPuzzlet(state.LaytonContext):
    def __init__(self):
        state.LaytonContext.__init__(self)
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
        self.transitionsEnableIn = False
        self.transitionsEnableOut = False
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
        return False

class LaytonPuzzleUi(LaytonContextPuzzlet):

    buttonHint      = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "system/btn/" + conf.LAYTON_ASSET_LANG, "hint")
    buttonHint.pos  = (conf.LAYTON_SCREEN_WIDTH - buttonHint.dimensions[0], conf.LAYTON_SCREEN_HEIGHT)

    def __init__(self, puzzleData, puzzleIndex, playerState):
        LaytonContextPuzzlet.__init__(self)
        self.screenIsOverlay        = True
        self.transitionsEnableIn    = False
        self.transitionsEnableOut   = False

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
        if self.playerState.getPuzzleEntry(self.puzzleIndex).unlockedHintLevel != self.buttonHintLevel:
            self.spawnNewButtonHint()

    def draw(self, gameDisplay):
        #if self.puzzleHintCount > 0:
        self.buttonHint.draw(gameDisplay)
        # Draw puzzle index text

        def setAnimationFromNameReadyToDraw(name, gameDisplay):
            if self.puzzleAnimFont.setAnimationFromName(name):
                self.puzzleAnimFont.setInitialFrameFromAnimation()
                self.puzzleAnimFont.draw(gameDisplay)

        self.puzzleAnimFont.pos = (6,4)
        setAnimationFromNameReadyToDraw("nazo", gameDisplay)
        self.puzzleAnimFont.pos = (100,4)
        setAnimationFromNameReadyToDraw("pk", gameDisplay)
        self.puzzleAnimFont.pos = (166,4)
        setAnimationFromNameReadyToDraw("hint", gameDisplay)

        for bannerText, xPosInitial in [(self.puzzleIndexText, 27),
                                        #(format(str(self.playerState.puzzleData[self.puzzleIndex].getValue()), '>3'), 75),

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
            if self.buttonHint.getPressedStatus():
                # TODO - Assess state
                #self.spawnNewButtonHint()
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

class LaytonPuzzleHandler(state.LaytonSubscreen):

    def __init__(self, puzzleIndex, playerState):
        state.LaytonSubscreen.__init__(self)
        self.transitionsEnableIn = False
        self.transitionsEnableOut = False
        self.screenBlockInput = True
        
        self.commandFocus = None
        self.puzzleIndex = puzzleIndex

        puzzleDataIndex = (puzzleIndex // 60) + 1

        puzzleScript    = FileInterface.getPackedData(FileInterface.PATH_ASSET_SCRIPT + "puzzle.plz",
                                                      "q" + str(puzzleIndex) + "_param.gds", version = 1)
        puzzleData = asset_dat.LaytonPuzzleData()
        puzzleData.load(FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "nazo/" + conf.LAYTON_ASSET_LANG + "/nazo" + str(puzzleDataIndex) + ".plz",
                                                    "n" + str(puzzleIndex) + ".dat", version = 1))

        self.addToStack(LaytonPuzzleBackground(puzzleData.idBackgroundTs, puzzleData.idBackgroundBs))
        self.addToStack(LaytonScrollerOverlay(puzzleData.textPrompt, playerState))
        self.addToStack(LaytonPuzzleUi(puzzleData, puzzleIndex, playerState))
        self.addToStack(LaytonTouchOverlay())

if __name__ == '__main__':
    tempPlayerState = state.LaytonPlayerState()
    tempPlayerState.remainingHintCoins = 100
    state.play(LaytonPuzzleHandler(3, tempPlayerState), tempPlayerState)