import pygame, conf, anim, state, const
from file import FileInterface

pygame.display.set_mode((conf.LAYTON_SCREEN_WIDTH, conf.LAYTON_SCREEN_HEIGHT * 2))

class MysteryButton():

    OFFSET_PRESS_X = 1
    OFFSET_PRESS_Y = 1

    def __init__(self, index, x, y, imageBank, playerState):
        self.buttonSolved   = anim.AnimatedButton(imageBank.setAnimationFromNameAndReturnInitialFrame(str(index + 1)),
                                                  imageBank.setAnimationFromNameAndReturnInitialFrame(str(index + 1)),
                                                  x = x, y = y, imageIsSurface=True)
        self.buttonUnsolved = anim.AnimatedButton(imageBank.setAnimationFromNameAndReturnInitialFrame(str(index + 11)),
                                                  imageBank.setAnimationFromNameAndReturnInitialFrame(str(index + 11)),
                                                  x = x, y = y, imageIsSurface=True)
        self.buttonSolved.imageButtonPressed.pos    = (self.buttonSolved.pos[0] + MysteryButton.OFFSET_PRESS_X,
                                                       self.buttonSolved.pos[1] + MysteryButton.OFFSET_PRESS_Y)
        self.buttonUnsolved.imageButtonPressed.pos  = (self.buttonUnsolved.pos[0] + MysteryButton.OFFSET_PRESS_X,
                                                       self.buttonUnsolved.pos[1] + MysteryButton.OFFSET_PRESS_Y)
        self.playerState = playerState
        self.index = index

    def draw(self, gameDisplay):
        if self.playerState.getStatusMystery(self.index) != state.LaytonPlayerState.MYSTERY_HIDDEN:
            if self.playerState.getStatusMystery(self.index) != state.LaytonPlayerState.MYSTERY_UNLOCKED:
                self.buttonSolved.draw(gameDisplay)
            else:
                self.buttonUnsolved.draw(gameDisplay)
    
    def handleEvent(self, event):
        if self.playerState.getStatusMystery(self.index) != state.LaytonPlayerState.MYSTERY_HIDDEN:
            self.buttonUnsolved.handleEvent(event)
            self.buttonSolved.handleEvent(event)
    
    def peekPressedStatus(self):
        return self.buttonSolved.peekPressedStatus()
    
    def getPressedStatus(self):
        self.buttonUnsolved.getPressedStatus()
        return self.buttonSolved.getPressedStatus()

class Screen(state.LaytonContext):

    IMAGE_NO_MYSTERY_SELECTED   = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "menu/bag/" + conf.LAYTON_ASSET_LANG + "/info_mode_sub")
    IMAGE_BG_MYSTERY_TEXT       = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "menu/bag/info_mode_sub2")
    IMAGE_BG_BOTTOM_SCREEN      = anim.fetchBgSurface(FileInterface.PATH_ASSET_BG + "menu/bag/info_mode_bg")

    BANK_IMAGES = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "menu/bag/" + conf.LAYTON_ASSET_LANG, "info_mode_chr")
    BANK_IMAGES_BACK = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "menu/bag/" + conf.LAYTON_ASSET_LANG, "memo_close_buttons")

    SOLVED_ANIM = anim.AnimatedImage(FileInterface.PATH_ASSET_ANI + "event", "hukmaru_hanko")
    SOLVED_ANIM.loopingDisable()
    # TODO - Null surface on fail to return
    # TODO - Global buttons on everything that respond by delivering pygame events (good way to interface during blank periods?)
    BUTTON_BACK = anim.AnimatedButton(BANK_IMAGES_BACK.setAnimationFromNameAndReturnInitialFrame("return1"),
                                      BANK_IMAGES_BACK.setAnimationFromNameAndReturnInitialFrame("return2"),
                                      imageIsSurface=True, x=206, y=conf.LAYTON_SCREEN_HEIGHT + 172)
    
    DURATION_SCALE = 200
    SCALE_FACTOR = 7/6

    POS_BUTTONS_INITIAL_X = 4
    POS_BUTTONS_INITIAL_Y = 27
    POS_BUTTONS_STRIDE_X = 2
    POS_BUTTONS_STRIDE_Y = 10

    STAMP_OFFSET_X = -4
    STAMP_OFFSET_Y = -2

    def __init__(self, playerState, fadeInCall=None, fadeOutCall=None, canQuitCall=None):
        state.LaytonContext.__init__(self)
        self.screenIsOverlay        = True
        self.screenBlockInput       = True

        self.indexSelectedMystery = None

        self.needsFadeIn = fadeInCall != None
        self.fadeInCall = fadeInCall
        self.fadeOutCall = fadeOutCall
        
        if canQuitCall == None:

            def nullTrue():
                return True

            self.canQuitCall = nullTrue
        else:
            self.canQuitCall = canQuitCall
        
        self.lockUntilDead = False

        self.solvedAnimQueue = []
        self.solvedAnimLast = None

        self.buttons = []
        self.playerState = playerState
        
        self.mysteryTextTitle = []
        self.mysteryTextUnsolved = []
        self.mysteryTextSolved = []

        self.mysteryTextTitleScroller = anim.AnimatedText(playerState.getFont('fontevent'), "")
        self.mysteryTextTitlePos = (0,0)
        self.mysteryTextScroller = anim.NuvoTextScroller(playerState.getFont('fontevent'), "", textPosOffset=(17,45))

        x = Screen.POS_BUTTONS_INITIAL_X
        y = Screen.POS_BUTTONS_INITIAL_Y + conf.LAYTON_SCREEN_HEIGHT

        # TODO - Support anim for unlocking new mysteries

        for indexMystery in range(10):

            if indexMystery == 5:
                x = Screen.POS_BUTTONS_INITIAL_X
                y = Screen.POS_BUTTONS_INITIAL_Y + Screen.POS_BUTTONS_STRIDE_Y + conf.LAYTON_SCREEN_HEIGHT + Screen.BANK_IMAGES.dimensions[1]
            
            self.buttons.append(MysteryButton(indexMystery, x, y, Screen.BANK_IMAGES, playerState))

            if playerState.getStatusMystery(indexMystery) == state.LaytonPlayerState.MYSTERY_WAITING_UNLOCK:
                self.solvedAnimQueue.append(indexMystery)
            
            tempMysteryText = FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "txt/" + conf.LAYTON_ASSET_LANG + "/txt.plz", "it_" + str(indexMystery + 1) + ".txt", version = 1)
            if tempMysteryText != None:
                self.mysteryTextTitle.append(tempMysteryText.decode('shift-jis'))
            else:
                self.mysteryTextTitle.append("")

            tempMysteryText = FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "txt/" + conf.LAYTON_ASSET_LANG + "/txt.plz", "id_" + str(indexMystery + 1) + ".txt", version = 1)
            if tempMysteryText != None:
                self.mysteryTextUnsolved.append(tempMysteryText.decode('shift-jis'))
            else:
                self.mysteryTextUnsolved.append("")

            tempMysteryText = FileInterface.getPackedData(FileInterface.PATH_ASSET_ROOT + "txt/" + conf.LAYTON_ASSET_LANG + "/txt.plz", "ide_" + str(indexMystery + 1) + ".txt", version = 1)
            if tempMysteryText != None:
                self.mysteryTextSolved.append(tempMysteryText.decode('shift-jis'))
            else:
                self.mysteryTextSolved.append("")

            x += Screen.POS_BUTTONS_STRIDE_X + Screen.BANK_IMAGES.dimensions[0]

    def update(self, gameClockDelta):
        if self.lockUntilDead:
            if self.canQuitCall():
                self.terminateExecution()
        else:
            if self.needsFadeIn:
                self.fadeInCall()
                self.needsFadeIn = False
            elif self.canQuitCall():
                Screen.SOLVED_ANIM.update(gameClockDelta)
                if self.solvedAnimLast != None:
                    self.playerState.setStatusMystery(self.solvedAnimLast, state.LaytonPlayerState.MYSTERY_UNLOCKED)
                    self.solvedAnimLast = None

                if len(self.solvedAnimQueue) > 0:
                    if Screen.SOLVED_ANIM.getAnim() == None:
                        # Ready next anim
                        self.solvedAnimLast = self.solvedAnimQueue.pop(0)
                        Screen.SOLVED_ANIM.pos = (self.buttons[self.solvedAnimLast].buttonSolved.pos[0] + Screen.STAMP_OFFSET_X,
                                                  self.buttons[self.solvedAnimLast].buttonSolved.pos[1] + Screen.STAMP_OFFSET_Y)
                        Screen.SOLVED_ANIM.setAnimationFromName("New Animation")
                        # Trigger sound can be done here as well

                self.mysteryTextTitleScroller.update(gameClockDelta)
                self.mysteryTextScroller.update(gameClockDelta)

    def draw(self, gameDisplay):
        if self.indexSelectedMystery == None:
            gameDisplay.blit(Screen.IMAGE_NO_MYSTERY_SELECTED, (0,0))
        else:
            gameDisplay.blit(Screen.IMAGE_BG_MYSTERY_TEXT, (0,0))

        gameDisplay.blit(Screen.IMAGE_BG_BOTTOM_SCREEN, (0,conf.LAYTON_SCREEN_HEIGHT))
        Screen.BUTTON_BACK.draw(gameDisplay)
        self.mysteryTextScroller.draw(gameDisplay)
        self.mysteryTextTitleScroller.draw(gameDisplay, location=self.mysteryTextTitlePos)
        for button in self.buttons:
            button.draw(gameDisplay)

        Screen.SOLVED_ANIM.draw(gameDisplay)
    
    def kill(self):
        if self.fadeOutCall == None:
            self.terminateExecution()
        else:
            self.fadeOutCall()
            self.lockUntilDead = True
    
    def terminateExecution(self):
        self.isContextFinished = True
        pygame.event.post(pygame.event.Event(const.ENGINE_RESUME_EXECUTION_STACK, {const.PARAM:None}))

    def handleEvent(self, event):
        if self.canQuitCall():
            if len(self.solvedAnimQueue) == 0:
                Screen.BUTTON_BACK.handleEvent(event)
                if Screen.BUTTON_BACK.peekPressedStatus():
                    if Screen.BUTTON_BACK.getPressedStatus():
                        self.kill()
                    return True

                for indexButton, button in enumerate(self.buttons):
                    button.handleEvent(event)
                    if button.peekPressedStatus():
                        if button.getPressedStatus():
                            self.indexSelectedMystery = indexButton
                            self.mysteryTextScroller.reset()

                            # Redraw mystery text
                            self.mysteryTextTitleScroller.text = self.mysteryTextTitle[self.indexSelectedMystery]
                            self.mysteryTextTitleScroller.update(None)
                            self.mysteryTextTitlePos = ((conf.LAYTON_SCREEN_WIDTH - self.mysteryTextTitleScroller.textRender.get_width()) // 2, 14)

                            if self.playerState.statusMystery[self.indexSelectedMystery] == state.LaytonPlayerState.MYSTERY_LOCKED:
                                self.mysteryTextScroller.textInput = self.mysteryTextUnsolved[self.indexSelectedMystery]
                            else:
                                self.mysteryTextScroller.textInput = self.mysteryTextSolved[self.indexSelectedMystery]
                            self.mysteryTextScroller.skip()
                        return True
        return super().handleEvent(event)

if __name__ == '__main__':
    playerState = state.LaytonPlayerState()
    playerState.remainingHintCoins = 10
    tempDebugExitLayer = state.LaytonScreen()
    # 11 170, 10 60
    tempDebugExitLayer.addToStack(Screen(playerState))
    state.play(tempDebugExitLayer, playerState)