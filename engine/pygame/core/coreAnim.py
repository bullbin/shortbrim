# Animation Components of LAYTON1

import coreProp, pygame
from os import path
from math import ceil

pygame.display.set_mode((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT * 2))
        
class StaticImage():
    def __init__(self, imagePath, x=0, y=0):
        self.image = pygame.image.load(coreProp.LAYTON_ASSET_ROOT + imagePath).convert_alpha()
        self.pos = (x,y)

    def update(self, gameClockDelta):
        pass

    def draw(self, gameDisplay):
        gameDisplay.blit(self.image, self.pos)
    
    def wasClicked(self, mousePos):
        if self.pos[0] + self.image.get_width() >= mousePos[0] and mousePos[0] >= self.pos[0]:
            if self.pos[1] + self.image.get_height() >= mousePos[1] and mousePos[1] >= self.pos[1]:
                return True
        return False

class AnimatedFrameCollection():
    def __init__(self, framerate, indices=[], loop=True):
        self.framerate = framerate
        if coreProp.LAYTON_PERFORMANCE_MODE:
            self.frameInterval = 1000/self.framerate
            self.getUpdatedFrame = self.getAccurateUpdatedFrame
        else:
            self.frameInterval = 1000 // self.framerate
            self.getUpdatedFrame = self.getFastUpdatedFrame

        self.frameClosestInterval = 1000 // self.framerate
        self.loop = loop
        self.indices = indices
        self.currentIndex = 0
        self.timeSinceLastUpdate = 0
        self.isActive = True

    def getAccurateUpdatedFrame(self, gameClockDelta):
        if self.isActive:
            self.timeSinceLastUpdate += gameClockDelta
            if self.timeSinceLastUpdate >= self.frameInterval:
                frameStep = int(self.timeSinceLastUpdate // (self.frameClosestInterval))
                if self.currentIndex + frameStep >= len(self.indices):
                    if self.loop:
                        self.currentIndex = (self.currentIndex + frameStep) % len(self.indices)
                    else:
                        self.isActive = False
                        return (False, None)
                else:
                    self.currentIndex += frameStep
                self.timeSinceLastUpdate -= (frameStep * (self.frameInterval))
            return (True, self.indices[self.currentIndex])
        return (False, None)
    
    def getFastUpdatedFrame(self, gameClockDelta):
        if self.isActive:
            if self.timeSinceLastUpdate >= self.frameInterval:
                if self.currentIndex + 1 == len(self.indices):
                    if self.loop:
                        self.currentIndex = 0
                    else:
                        self.isActive = False
                        return (False, None)
                else:
                    self.currentIndex += 1
                self.timeSinceLastUpdate = 0
            else:
                self.timeSinceLastUpdate += gameClockDelta
            return (True, self.indices[self.currentIndex])
        return (False, None)
    
    def reset(self):
        self.isActive = True
        self.currentIndex = 0

class AnimatedImage():
    def __init__(self, frameRootPath, frameName, frameRootExtension="png", x=0,y=0):
        self.pos = (x,y)
        self.frames = []
        self.dimensions = (0,0)
        self.animMap = {}
        self.animActive = None
        self.animActiveFrame = None
        
        if path.exists(frameRootPath):
            if path.exists(frameRootPath + "\\" + frameName + "_0." + frameRootExtension):
                imageIndex = 0
                while True:
                    if path.exists(frameRootPath + "\\" + frameName + "_" + str(imageIndex) + "." + frameRootExtension):
                        self.frames.append(pygame.image.load(frameRootPath + "\\" + frameName + "_" + str(imageIndex) + "." + frameRootExtension).convert())
                        imageIndex += 1
                    else:
                        break
                self.dimensions = (self.frames[0].get_width(), self.frames[0].get_height())
            elif path.exists(frameRootPath + "\\" + frameName + "." + frameRootExtension):
                self.frames.append(pygame.image.load(frameRootPath + "\\" + frameName + "." + frameRootExtension).convert_alpha())
                self.dimensions = (self.frames[0].get_width(), self.frames[0].get_height())
            else:
                print("AnimatedImage: No images found in path '" + str(frameRootPath) + "'")
        else:
            print("AnimatedImage: Path '" + str(frameRootPath) + "' does not exist!")

    def fromImages(self, animText):
        if path.exists(animText):
            with open(animText, 'r') as animDb:
                lineIndex = 0
                for line in animDb:
                    lineIndex = lineIndex % 4
                    if lineIndex == 0:
                        tempAnimName = line
                        tempAnimIndices = []
                        tempAnimLoop = False
                    elif lineIndex == 1:
                        tempAnimFramerate = int(line)
                    elif lineIndex == 2:
                        line = line[0:-1].split(",")
                        if line[0] == "True":                       # Set looping
                            tempAnimLoop = True
                        if len(line) > 1 and line[1] == "True":     # Set chroma-key (temporary)
                            for frame in self.frames:
                                frame.set_colorkey(pygame.Color(int(line[2]), int(line[3]), int(line[4])))
                    else:
                        line = line.split(",")
                        for index in line:
                            tempAnimIndices.append(int(index) % len(self.frames))
                        self.animMap[tempAnimName] = AnimatedFrameCollection(tempAnimFramerate, indices=tempAnimIndices, loop=tempAnimLoop)
                    lineIndex += 1
            return True
        else:
            print("AnimatedImage: Cannot import " + animText + " as it does not exist!")
            return False
    
    def draw(self, gameDisplay):
        if self.animActiveFrame != None:
            gameDisplay.blit(self.frames[self.animActiveFrame], self.pos)

    def update(self, gameClockDelta):
        if self.animActive != None:
            tempFrame = self.animMap[self.animActive].getUpdatedFrame(gameClockDelta)
            self.animActiveFrame = tempFrame[1] 
            if not(tempFrame[0]):
                self.animActive = None

    def setAnimationFromName(self, anim):
        if anim in self.animMap.keys():
            self.animMap[anim].reset()
            self.animActive = anim
        else:
            print("Animation not found: " + str(anim))
            self.animActive = None
    
    def setAnimationFromIndex(self, index):
        if index < len(self.animMap.keys()):
            self.animMap[list(self.animMap.keys())[index]].reset()
            self.animActive = list(self.animMap.keys())[index]
    
    def setActiveFrame(self, frameIndex):
        if frameIndex < len(self.frames):
            self.animActiveFrame = frameIndex
        elif len(self.frames) > 0:
            self.animActiveFrame = frameIndex % len(self.frames)
    
    def wasClicked(self, mousePos):
        if self.pos[0] + self.dimensions[0] >= mousePos[0] and mousePos[0] >= self.pos[0]:
            if self.pos[1] + self.dimensions[1] >= mousePos[1] and mousePos[1] >= self.pos[1]:
                return True
        return False

class AnimatedText():
    def __init__(self, initString = "", colour=(0,0,0)):
        self.text = initString
        self.textColour = colour
        self.textRender = coreProp.LAYTON_PUZZLE_FONT.render(self.text,True,colour,None)
    def update(self, gameClockDelta):
        self.textRender = coreProp.LAYTON_PUZZLE_FONT.render(self.text,True,self.textColour,None)
    def draw(self, gameDisplay, location=(0,0)):
        textRect = self.textRender.get_rect()
        centX, centY = textRect.center
        x,y = location
        centY += y; centX += x
        textRect.center = (centX, centY)
        gameDisplay.blit(self.textRender, textRect)

class Fader():
    def __init__(self):
        self.strength = 0
        self.interval = 0.1

    def draw(self, gameDisplay):
        faderSurface = pygame.Surface((coreProp.LAYTON_SCREEN_WIDTH,coreProp.LAYTON_SCREEN_HEIGHT * 2)).convert()
        faderSurface.set_alpha(ceil(self.strength * 255))
        faderSurface.fill((0,0,0))
        gameDisplay.blit(faderSurface, (0,0))

class TextScroller():
    def __init__(self, textInput, textPosOffset=(4,24), targetFramerate = coreProp.LAYTON_ENGINE_FPS):
         self.textInput = textInput
         self.textNewline = 0
         self.textPos = 0
         self.textPosOffset = textPosOffset
         self.textRects = []
         self.drawIncomplete = True
         self.targetFramerate = targetFramerate

    def update(self, gameClockDelta):
        if self.drawIncomplete and (gameClockDelta >= 1000/self.targetFramerate):
            if self.textInput[self.textPos] == "\n" or self.textPos == 0:
                self.textRects.append(AnimatedText())
                if self.textPos == 0:
                    self.textNewline = self.textPos
                else:
                    self.textNewline = self.textPos + 1
            else:
                self.textRects[-1].text = self.textInput[self.textNewline:self.textPos + 1]
                self.textRects[-1].update(gameClockDelta)
                
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
            animText.draw(gameDisplay, location=(x,y))
            y += coreProp.LAYTON_PUZZLE_FONT.get_height()