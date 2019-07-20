# Animation Components of LAYTON1

import coreProp, pygame
from os import path
from math import ceil

pygame.display.set_mode((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT * 2))
        
class StaticImage():
    def __init__(self, imagePath, x=0, y=0):
        self.image = pygame.image.load(imagePath).convert_alpha()
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
        if coreProp.ENGINE_PERFORMANCE_MODE:
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
                    if line[-1] == "\n":
                        line = line[0:-1]
                    lineIndex = lineIndex % 4
                    if lineIndex == 0:
                        tempAnimName = line
                        tempAnimIndices = []
                        tempAnimLoop = False
                    elif lineIndex == 1:
                        tempAnimFramerate = int(line)
                    elif lineIndex == 2:
                        line = line.split(",")
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
    
    def setInitialFrameFromAnimation(self):
        if self.animActive != None:
            self.animActiveFrame = self.animMap[self.animActive].indices[0]

    def setAnimationFromName(self, anim):
        if anim in self.animMap.keys():
            self.animMap[anim].reset()
            self.animActive = anim
            return True
        self.animActive = None
        return False

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

class FontMap():
    def __init__(self, fontImage, fontXml, encoding="utf-8", tilesPerLine=16, tileGap=2, xFontGap=1, yFontGap=1, calculateWidth=False, calculateWidthSkipChar=[]):
        self.fontMap = {}
        self.fontWidth = 0
        self.fontHeight = 0
        self.fontBlendColour = pygame.Color(255,255,255)
        self.fontSpacing = (xFontGap, yFontGap)
        if path.exists(fontImage):
            self.fontSurface = pygame.image.load(fontImage).convert()
            tempFontMap = {}
            try:
                self.fontWidth = int((self.fontSurface.get_width() - ((tilesPerLine + 1) * tileGap)) / 16)
                with open(fontXml, 'r', encoding=encoding, errors='ignore') as xmlIn:
                    # This only extracts simple areas of the XML - it is not resilient
                    for line in xmlIn:
                        if "CharInfo" in line and "Code" in line and "Index" in line:
                            tempCode = line[18]
                            line = line.split(" ")[3:-1]
                            tempIndex = int(line[-2][7:-1])
                            tempWidth = int(line[-1][7:-1])
                            if tempWidth >= self.fontWidth:
                                tempWidth = self.fontWidth - 1
                            tempFontMap[tempIndex] = (tempCode, tempWidth)
                tempRowCount = (ceil(len(tempFontMap.keys()) / tilesPerLine))
                self.fontHeight = int((self.fontSurface.get_height() - (tempRowCount + 1) * tileGap) / tempRowCount)

            except UnicodeDecodeError:
                print("Font: Error reading XML!")
            except ValueError:
                print("Font: Unsupported character spacing!")
            except FileNotFoundError:
                print("Font: No XML at path '" + fontXml + "'")

            offsetY = tileGap
            charIndex = 0
            for _indexTileHeight in range((ceil(len(tempFontMap.keys()) / tilesPerLine))):
                if charIndex < len(tempFontMap.keys()):
                    offsetX = tileGap
                    for _indexTileWidth in range(tilesPerLine):
                        try:
                            self.fontMap[tempFontMap[charIndex][0]] = self.fontSurface.subsurface((offsetX, offsetY, tempFontMap[charIndex][1], self.fontHeight))

                            if calculateWidth and tempFontMap[charIndex][0] not in calculateWidthSkipChar:
                                self.fontMap[tempFontMap[charIndex][0]] = self.fontSurface.subsurface((offsetX, offsetY, tempFontMap[charIndex][1], self.fontHeight))
                                for xPixel in range(tempFontMap[charIndex][1]):
                                    found = False
                                    xPixel = (tempFontMap[charIndex][1] - 1 - xPixel)
                                    for yPixel in range(self.fontHeight):
                                        if self.fontMap[tempFontMap[charIndex][0]].get_at((xPixel, yPixel)) != self.fontBlendColour:
                                            found = True
                                            break
                                    if found:
                                        break
                                if found:
                                    self.fontMap[tempFontMap[charIndex][0]] = self.fontSurface.subsurface((offsetX, offsetY, xPixel + 1, self.fontHeight))

                            offsetX += self.fontWidth + tileGap
                            charIndex += 1
                        except KeyError:
                            break
                    offsetY += self.fontHeight + tileGap
                else:
                    break
        else:
            print("Font: Path '" + fontImage + "' does not exist!")

    def getChar(self, char):
        try:
            return self.fontMap[char]
        except KeyError:
            return None

    def getSpacing(self):
        return self.fontSpacing
    
    def get_height(self):           # Used to preserve pygame compatibility
        return self.fontHeight + self.fontSpacing[1]
    
class AnimatedText():
    def __init__(self, font, initString = "", colour=(0,0,0)):
        self.text = initString
        self.textColour = colour
        self.font = font
        if type(self.font) == FontMap:
            self.textRender = pygame.Surface((len(self.text) * self.font.fontWidth, self.font.fontHeight))
            self.update = self.updateBitmapFont
            self.draw = self.drawBitmapFont
            self.updateBitmapFont(None)
        else:
            self.textRender = self.font.render(self.text,True,colour,None)
            self.update = self.updateRasterFont
            self.draw = self.drawRasterFont

    def updateRasterFont(self, gameClockDelta):
        self.textRender = self.font.render(self.text,True,self.textColour,None)

    def drawRasterFont(self, gameDisplay, location=(0,0)):
        textRect = self.textRender.get_rect()
        centX, centY = textRect.center
        x,y = location
        centY += y; centX += x
        textRect.center = (centX, centY)
        gameDisplay.blit(self.textRender, textRect)

    def updateBitmapFont(self, gameClockDelta):
        self.textRender = pygame.Surface((len(self.text) * (self.font.fontWidth + self.font.getSpacing()[0]), self.font.fontHeight + self.font.getSpacing()[1]))
        self.textRender.fill(self.font.fontBlendColour)
        self.textRender.set_colorkey(self.font.fontBlendColour)
        offsetX = 0
        for char in self.text:
            char = self.font.getChar(char)
            if char != None:
                self.textRender.blit(char, (offsetX, 0))
                offsetX += char.get_width() + self.font.getSpacing()[0]

    def drawBitmapFont(self, gameDisplay, location=(0,0)):
        gameDisplay.blit(self.textRender, location)

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
    def __init__(self, font, textInput, textPosOffset=(0,0), targetFramerate = coreProp.ENGINE_FPS):
        self.textInput = textInput
        self.textCumulativeLengths = []
        self.textNewline = 0
        self.textPos = 0
        self.textPosOffset = textPosOffset
        self.textRects = []
        self.font = font
        self.drawIncomplete = True
        self.frameStep = 1000/targetFramerate
        self.timeSinceLastUpdate = 0

    def update(self, gameClockDelta):
        if self.drawIncomplete:
            self.timeSinceLastUpdate += gameClockDelta
            if self.timeSinceLastUpdate >= self.frameStep:
                self.timeSinceLastUpdate -= self.frameStep
                if self.textInput[self.textPos] == "\n" or self.textPos == 0:
                    self.textRects.append(AnimatedText(self.font))
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
                self.textRects.append(AnimatedText(self.font, initString = line))
            self.drawIncomplete = False
    
    def draw(self, gameDisplay):
        x, y = self.textPosOffset
        for animText in self.textRects:
            animText.draw(gameDisplay, location=(x,y))
            y += self.font.get_height()