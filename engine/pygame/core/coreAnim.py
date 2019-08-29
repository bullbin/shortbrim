# Animation Components of LAYTON1

import coreProp, pygame
from os import path
from math import ceil, sin, cos, pi

pygame.display.set_mode((coreProp.LAYTON_SCREEN_WIDTH, coreProp.LAYTON_SCREEN_HEIGHT * 2))
        
class StaticImage():
    def __init__(self, imagePath, x=0, y=0, imageIsSurface=False, imageIsNull=False, imageNullDimensions=None):
        if imagePath == None or imageIsNull:
            if imageNullDimensions != None:
                self.image = pygame.Surface(imageNullDimensions)
            else:
                self.image = pygame.Surface((1,1))
        elif imageIsSurface:
            self.image = imagePath
        else:
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
        self.isActive = True
        if framerate == 0:
            self.getUpdatedFrame = self.getNullUpdatedFrame
        else:
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
    
    def getNullUpdatedFrame(self, gameClockDelta):
        return (True, self.indices[self.currentIndex])

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
        self.timeSinceLastUpdate = 0

class AnimatedImage():
    def __init__(self, frameRootPath, frameName, frameRootExtension="png", x=0,y=0, importAnimPair=True):
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
                        try:
                            self.frames.append(pygame.image.load(frameRootPath + "\\" + frameName + "_" + str(imageIndex) + "." + frameRootExtension).convert())
                        except:
                            print("Error loading frame: " + frameRootPath + "\\" + frameName + "_" + str(imageIndex) + "." + frameRootExtension)
                        imageIndex += 1
                    else:
                        break
                self.dimensions = (self.frames[0].get_width(), self.frames[0].get_height())
            elif path.exists(frameRootPath + "\\" + frameName + "." + frameRootExtension):
                try:
                    self.frames.append(pygame.image.load(frameRootPath + "\\" + frameName + "." + frameRootExtension).convert_alpha())
                    self.dimensions = (self.frames[0].get_width(), self.frames[0].get_height())
                except:
                    print("Error loading frame: " + frameRootPath + "\\" + frameName + "." + frameRootExtension)
            else:
                print("AnimatedImage: No images with '" + frameName + "' found in path '" + str(frameRootPath) + "'")
        else:
            print("AnimatedImage: Path '" + str(frameRootPath) + "' does not exist!")
        
        if importAnimPair:
            self.fromImages(frameRootPath + "\\" + frameName + ".txt")

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
    
    def setAnimationFromNameAndReturnInitialFrame(self, anim):
        if self.setAnimationFromName(anim):
            return self.frames[self.animMap[self.animActive].indices[0]]
        else:
            return None

    def setAnimationFromIndex(self, index):
        if index < len(self.animMap.keys()):
            self.animMap[list(self.animMap.keys())[index]].reset()
            self.animActive = list(self.animMap.keys())[index]
            return True
        return False
    
    def setActiveFrame(self, frameIndex):
        if frameIndex < len(self.frames):
            self.animActiveFrame = frameIndex
        elif len(self.frames) > 0:
            self.animActiveFrame = frameIndex % len(self.frames)
        else:
            return False
        return True
    
    def wasClicked(self, mousePos):
        if self.pos[0] + self.dimensions[0] >= mousePos[0] and mousePos[0] >= self.pos[0]:
            if self.pos[1] + self.dimensions[1] >= mousePos[1] and mousePos[1] >= self.pos[1]:
                return True
        return False

class StaticButton(StaticImage):
    def __init__(self, imagePath, x=0, y=0, imageIsSurface=False, imageIsNull=False, imageNullDimensions=None):
        StaticImage.__init__(self, imagePath, x, y, imageIsSurface, imageIsNull, imageNullDimensions)
        self.reset()
    
    def reset(self):
        self.wasClickedIn = False
        self.wasClickedOut = False
    
    def registerButtonDown(self, event):
        if self.wasClicked(event.pos):
            self.wasClickedIn = True
            self.wasClickedOut = False
        else:
            self.reset()
    
    def registerButtonUp(self, event):
        if self.wasClickedIn and self.wasClicked(event.pos):
            self.wasClickedOut = True
        else:
            self.reset()
    
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.registerButtonDown(event)   
        if event.type == pygame.MOUSEBUTTONUP:
            self.registerButtonUp(event)

    def getPressedStatus(self):
        if self.wasClickedOut:
            self.reset()
            return True
        return False

class AnimatedButton(StaticButton):
    def __init__(self, imagePathInitial, imagePathPressed, x, y, imageIsSurface):
        StaticButton.__init__(self, imagePathInitial, x, y, imageIsSurface)
        self.imageButtonPressed = StaticImage(imagePathPressed, x, y, imageIsSurface)
    
    def draw(self, gameDisplay):
        if self.wasClickedIn and self.wasClicked(pygame.mouse.get_pos()): 
            self.imageButtonPressed.draw(gameDisplay)
        else:
            super().draw(gameDisplay)

class FontMap():
    def __init__(self, fontImage, fontXml, encoding="utf-8", tilesPerLine=16, tileGap=2, xFontGap=1, yFontGap=1, calculateWidth=False, calculateWidthSkipChar=[]):
        self.fontMap = {}
        self.isLoaded = False
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
                            line = line.split(" ")[3:-1]
                            tempIndex = int(line[-2][7:-1])
                            tempCode = (int("0x" + line[-3][6:-1], 16).to_bytes(len(line[-3][6:-1]) // 2, byteorder = 'big')).decode(encoding)
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
            self.isLoaded = True
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
            if coreProp.ENGINE_PERFORMANCE_MODE:
                self.update = self.updateBitmapFontFast
            else:
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

    def updateBitmapFontFast(self, gameClockDelta): # Still expensive due to lots of drawing, but less expensive than the full version which includes colour support
        self.textRender = pygame.Surface((len(self.text) * (self.font.fontWidth + self.font.getSpacing()[0]), self.font.fontHeight + self.font.getSpacing()[1]))
        self.textRender.fill(self.font.fontBlendColour)
        self.textRender.set_colorkey(self.font.fontBlendColour)
        offsetX = 0
        for char in self.text:
            char = self.font.getChar(char)
            if char != None:
                self.textRender.blit(char, (offsetX, 0))
                offsetX += char.get_width() + self.font.getSpacing()[0]
    
    def updateBitmapFont(self, gameClockDelta):
        self.textTempRender = pygame.Surface((len(self.text) * (self.font.fontWidth + self.font.getSpacing()[0]), self.font.fontHeight + self.font.getSpacing()[1]))
        self.textTempRender.fill(self.font.fontBlendColour)
        offsetX = 0
        for char in self.text:
            char = self.font.getChar(char)
            if char != None:
                charColour = char.copy()
                charColour.fill(self.textColour, None, pygame.BLEND_RGBA_ADD)
                self.textTempRender.blit(charColour, (offsetX, 0))
                offsetX += char.get_width() + self.font.getSpacing()[0]
        self.textRender = pygame.Surface((offsetX, self.font.fontHeight))
        self.textRender.blit(self.textTempRender, (0,0))
        self.textRender.set_colorkey(self.font.fontBlendColour)
    
    def drawBitmapFont(self, gameDisplay, location=(0,0)):
        gameDisplay.blit(self.textRender, location)

class AnimatedFader():

    MODE_SINE_SHARP = 0
    MODE_SINE_SMOOTH = 1
    MODE_TRIANGLE = 2
    
    def __init__(self, durationCycle, mode, loop, cycle=True, inverted=False):
        self.durationCycle = durationCycle // 2
        self.doFullCycle = cycle
        self.loop = loop
        self.inverted = inverted
        if cycle:
            self.initalInverted = inverted
        self.reset()
        if coreProp.ENGINE_PERFORMANCE_MODE or mode == AnimatedFader.MODE_TRIANGLE:
            self.getStrength = self.getStrengthTriangle
        elif mode == AnimatedFader.MODE_SINE_SHARP:
            self.getStrength = self.getStrengthSineSingleEase
        elif mode == AnimatedFader.MODE_SINE_SMOOTH:
            self.getStrength = self.getStrengthSineDoubleEase
        else:
            print("AnimatedFader: Fader initialised with bad fade mode!")
            self.getStrength = self.getStrengthTriangle

    def reset(self):
        self.isActive = True
        self.durationElapsed = 0

    def update(self, gameClockDelta):
        if self.isActive:
            self.durationElapsed += gameClockDelta
            if self.durationElapsed >= self.durationCycle:
                self.inverted = not(self.inverted)
                self.durationElapsed = self.durationElapsed % self.durationCycle
                if not(self.loop):
                    if self.doFullCycle:
                        if self.inverted == self.initalInverted:
                            self.isActive = False
                    else:
                        self.isActive = False
    
    def getStrengthSineDoubleEase(self):
        if self.isActive:
            if self.inverted:
                return (cos(pi * (self.durationElapsed / self.durationCycle)) + 1) / 2
            else:
                return 1 - ((cos(pi * (self.durationElapsed / self.durationCycle)) + 1) / 2)
        else:
            return self.inverted

    def getStrengthSineSingleEase(self):
        if self.isActive:
            if self.inverted:
                return 1 - (sin((pi/2) * (self.durationElapsed / self.durationCycle)))
            else:
                return (sin((pi/2) * (self.durationElapsed / self.durationCycle)))
        else:
            return self.inverted

    def getStrengthTriangle(self):
        if self.isActive:
            if self.inverted:
                return 1 - (self.durationElapsed / self.durationCycle)
            else:
                return self.durationElapsed / self.durationCycle
        else:
            return self.inverted

class TextScroller():
    """Text renderer that handles newlines, colour switching and character replacement codes.
    Text is automatically animated; to render immediately, call skip() prior to drawing
    """
    def __init__(self, font, textInput, textPosOffset=(0,0), targetFramerate = coreProp.ENGINE_FPS):
        self.textInput = textInput
        indexReplacementCharStart = self.textInput.find("<")
        while indexReplacementCharStart != -1:
            indexReplacementCharEnd = indexReplacementCharStart + 1
            while self.textInput[indexReplacementCharEnd] != ">":
                indexReplacementCharEnd += 1
            try:
                self.textInput = self.textInput[:indexReplacementCharStart] + coreProp.GRAPHICS_FONT_CHAR_SUBSTITUTION[self.textInput[indexReplacementCharStart + 1:indexReplacementCharEnd]] + self.textInput[indexReplacementCharEnd + 1:]
            except KeyError:
                print("TextScroller: Character '" + self.textInput[indexReplacementCharStart + 1:indexReplacementCharEnd] + "' has no substitution!")
                self.textInput = self.textInput[:indexReplacementCharStart] + self.textInput[indexReplacementCharEnd + 1:]
            indexReplacementCharStart = self.textInput.find("<")

        self.textNewline = 0
        self.textCurrentColour = "x"
        self.textPos = 0
        self.textPosOffset = textPosOffset
        self.textRects = []
        self.font = font
        self.drawIncomplete = True
        self.frameStep = 1000/targetFramerate
        self.timeSinceLastUpdate = 0

    def incrementText(self):    # There are much faster ways to do this, consider writing to a surface then just masking instead of redrawing per character
        if self.textPos < len(self.textInput):
            if self.textInput[self.textPos] == "#":
                if self.textCurrentColour != self.textInput[self.textPos + 1]:
                    self.textCurrentColour = self.textInput[self.textPos + 1]
                    if self.textPos == self.textNewline:
                        self.textNewline += 2
                    self.textPos += 2
                    if self.textPos < len(self.textInput) and self.textPos > 2:
                        if self.textInput[self.textPos] != "\n":
                            # Register colour change between rects
                            self.textNewline = self.textPos
                            self.textRects[-1].append(AnimatedText(self.font, colour=coreProp.GRAPHICS_FONT_COLOR_MAP[self.textCurrentColour]))

            if self.textPos < len(self.textInput):
                if self.textInput[self.textPos] == "\n" or self.textPos == 0:
                    self.textRects.append([AnimatedText(self.font, colour=coreProp.GRAPHICS_FONT_COLOR_MAP[self.textCurrentColour])])
                    if self.textPos == 0:
                        self.textNewline = self.textPos
                    else:
                        self.textNewline = self.textPos + 1
                else:
                    self.textRects[-1][-1].text = self.textInput[self.textNewline:self.textPos + 1]
                    self.textRects[-1][-1].update(None)
                self.textPos += 1
        else:
            self.drawIncomplete = False
    
    def update(self, gameClockDelta):
        if self.drawIncomplete:
            self.timeSinceLastUpdate += gameClockDelta
            while self.timeSinceLastUpdate >= self.frameStep:
                self.timeSinceLastUpdate -= self.frameStep
                self.incrementText()

    def skip(self):
        while self.drawIncomplete:
            self.incrementText()
    
    def draw(self, gameDisplay):
        x, y = self.textPosOffset
        for animText in self.textRects:
            x = self.textPosOffset[0]
            for lineText in animText:
                lineText.draw(gameDisplay, location=(x,y))
                x += lineText.textRender.get_width()
            y += self.font.get_height()

def scaleSurfaceCopy(surface, scaleFactorX, scaleFactorY):
    return pygame.transform.scale(surface, (round(surface.get_width() * scaleFactorX),
                                            round(surface.get_height() * scaleFactorY)))