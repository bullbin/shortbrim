# Animation Components of LAYTON1

import coreProp, pygame

class AnimatedImage():
    def __init__(self, imagePath, x=0,y=0):
        self.image = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + imagePath)
        self.pos = (x,y)
    def draw(self, gameDisplay):
        gameDisplay.blit(self.image, self.pos)

class AnimatedText():
    def __init__(self, initString = "", colour=(0,0,0)):
        self.text = initString
        self.textColour = colour
        self.textRender = coreProp.LAYTON_PUZZLE_FONT.render(self.text,True,colour,None)
    def update(self):
        self.textRender = coreProp.LAYTON_PUZZLE_FONT.render(self.text,True,self.textColour,None)
    def draw(self, gameDisplay, location=(0,0)):
        textRect = self.textRender.get_rect()
        centX, centY = textRect.center
        x,y = location
        centY += y; centX += x
        textRect.center = (centX, centY)
        gameDisplay.blit(self.textRender, textRect)

class TextScroller():
    def __init__(self, textInput, textPosOffset=(4,24)):
         self.textInput = textInput
         self.textNewline = 0
         self.textPos = 0
         self.textPosOffset = textPosOffset
         self.textRects = []
         self.drawIncomplete = True

    def update(self):
        if self.drawIncomplete:
            if self.textInput[self.textPos] == "\n" or self.textPos == 0:
                self.textRects.append(AnimatedText())
                if self.textPos == 0:
                    self.textNewline = self.textPos
                else:
                    self.textNewline = self.textPos + 1
            else:
                self.textRects[-1].text = self.textInput[self.textNewline:self.textPos + 1]
                
            if self.textPos < len(self.textInput) -1:
                self.textPos += 1
            else:
                self.drawIncomplete = False

    def skip(self):
        if self.drawIncomplete:
            skipText = self.textInput.split("\n")
            self.textRects = []
            for line in skipText:
                self.textRects.append(AnimatedText(initString = line))
            self.drawIncomplete = False
    
    def draw(self, gameDisplay):
        x, y = self.textPosOffset
        for animText in self.textRects:
            animText.update()
            animText.draw(gameDisplay, location=(x,y))
            y += coreProp.LAYTON_PUZZLE_FONT.get_height()
