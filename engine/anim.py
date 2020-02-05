# Animation Components of LAYTON1

import conf, const, pygame
from os import path
from math import ceil, sin, cos, pi

import file
from file import FileInterface
from hat_io import asset, asset_image

pygame.display.set_mode((conf.LAYTON_SCREEN_WIDTH, conf.LAYTON_SCREEN_HEIGHT * 2))

# TODO - Log better
# TODO - Autostart gfx anim

def debugPrint(line):   # Function needs to be moved from coreState to avoid cyclical dependency
    if conf.ENGINE_DEBUG_MODE:
        print(line)

def scaleSurfaceCopy(surface, scaleFactorX, scaleFactorY):
    return pygame.transform.scale(surface, (round(surface.get_width() * scaleFactorX),
                                            round(surface.get_height() * scaleFactorY)))

def fetchBgSurface(filepath):
    filepath = filepath.replace("\\", "/")
    filepath = path.splitext(file.resolveFilepath(filepath))[0]
    if not(conf.ENGINE_LOAD_FROM_DECOMPRESSED) or conf.ENGINE_LOAD_FROM_ROM:
        assetData = asset.File(data=FileInterface.getData(filepath + ".arc"))
        if len(assetData.data) > 0:
            assetData.decompress()
            assetImage = asset_image.LaytonBackgroundImage()
            assetImage.load(assetData.data)
            return pygame.image.fromstring(assetImage.image.convert("RGB").tobytes("raw", "RGB"), assetImage.image.size, "RGB").convert()
    else:
        try:
            return pygame.image.load(filepath + conf.FILE_DECOMPRESSED_EXTENSION_IMAGE)
        except pygame.error:
            print("AnimLibBgSurface: Failed to load", filepath + conf.FILE_DECOMPRESSED_EXTENSION_IMAGE)
    return pygame.Surface((0,0))

class StaticImage():
    def __init__(self, imagePath, x=0, y=0, imageIsSurface=False, imageIsNull=False, imageNullDimensions=None):
        if imagePath == None or imageIsNull:
            if imageNullDimensions != None:
                self.image = pygame.Surface(imageNullDimensions)
            else:
                self.image = pygame.Surface((0,0))
        elif imageIsSurface:
            self.image = imagePath
        else:
            self.image = pygame.Surface((20,20))
            #self.image = pygame.image.load(imagePath).convert_alpha()
        self.dimensions = (self.image.get_width(), self.image.get_height())
        self.pos = (x,y)

    def getImage(self):
        return self.image

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

    ROM_FRAMETIME_MULTIPLIER = (1000 / 60) * 1 #(5 / 3)

    def __init__(self, framerate, indices=[], loop=True, isFramerateTimeArray=False, faceOffset=(None,None)):
        self.framerate = framerate
        self.isActive = True
        self.loop = loop
        self.indices = indices
        self.currentIndex = 0
        self.timeSinceLastUpdate = 0
        self.offsetFace = faceOffset

        if isFramerateTimeArray:
            if type(framerate) != list or len(framerate) == 0:
                self.getUpdatedFrame = self.getNullUpdatedFrame
            else:
                self.frameInterval = (AnimatedFrameCollection.ROM_FRAMETIME_MULTIPLIER) * self.framerate[self.currentIndex]
                self.getUpdatedFrame = self.getArrAccurateUpdatedFrame
        else:
            if type(framerate) != int or framerate <= 0:
                self.getUpdatedFrame = self.getNullUpdatedFrame
            else:
                if conf.ENGINE_PERFORMANCE_MODE:
                    self.frameInterval = 1000/self.framerate
                    self.getUpdatedFrame = self.getAccurateUpdatedFrame
                else:
                    self.frameInterval = 1000 // self.framerate
                    self.getUpdatedFrame = self.getFastUpdatedFrame
                self.frameClosestInterval = 1000 // self.framerate
    
    def getAnimLength(self):
        if len(self.indices) == 0:
            return 0
        else:
            if type(self.framerate) == list:
                totalAnimLength = 0
                for duration in self.framerate:
                    totalAnimLength += duration * AnimatedFrameCollection.ROM_FRAMETIME_MULTIPLIER
                return totalAnimLength
            else:
                return (1000 / self.framerate) * len(self.indices)
    
    def getNullUpdatedFrame(self, gameClockDelta):
        if len(self.indices) > 0:
            return (True, self.indices[self.currentIndex])
        return (False, None)

    def getArrAccurateUpdatedFrame(self, gameClockDelta):
        if self.isActive:
            self.timeSinceLastUpdate += gameClockDelta
            while self.timeSinceLastUpdate >= self.frameInterval:
                self.timeSinceLastUpdate -= self.frameInterval
                self.currentIndex += 1
                if self.currentIndex >= len(self.indices):
                    if self.loop:
                        self.currentIndex = 0
                    else:
                        self.isActive = False
                        return (False, None)
                self.frameInterval = (AnimatedFrameCollection.ROM_FRAMETIME_MULTIPLIER) * (self.framerate[self.currentIndex])
            return (True, self.indices[self.currentIndex])
        return (False, None)

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
        if type(self.framerate) == list and len(self.framerate) > 0:
            self.frameInterval = (AnimatedFrameCollection.ROM_FRAMETIME_MULTIPLIER) * self.framerate[self.currentIndex]
        self.timeSinceLastUpdate = 0

class AnimatedImage():
    def __init__(self, frameRootPath, frameName, x=0,y=0, fromImport=True, importAnimPair=True, usesAlpha=False, frameRootExtension= conf.FILE_DECOMPRESSED_EXTENSION_IMAGE):
        self.pos = (x,y)
        self.frames = []
        self.animMap = {}
        self.animActive = None
        self.animActiveFrame = None

        self.usesAlpha = usesAlpha
        self.alpha = 255
        if self.usesAlpha:
            self.draw = self.drawAlpha
        else:
            self.draw = self.drawNormal
        
        if fromImport:
            frameRootPath = frameRootPath.replace("\\", "/")
            if frameRootPath[-1] != "/":
                frameRootPath += "/"
            if len(frameRootExtension) > 0 and frameRootExtension[0] != ".":    # Bad extension
                frameRootExtension = "." + frameRootExtension

            if not(conf.ENGINE_LOAD_FROM_DECOMPRESSED) or conf.ENGINE_LOAD_FROM_ROM:
                self.loadFromAsset(frameName, frameRootPath)
            else:
                self.loadFromUncompressed(frameRootPath, frameName, frameRootExtension, importAnimPair)

            if len(self.frames) > 0:
                self.dimensions = (self.frames[0].get_width(), self.frames[0].get_height())
            else:
                self.dimensions = (0,0)

    def loadFromUncompressed(self, frameRootPath, frameName, frameRootExtension, importAnimPair):
        if path.exists(frameRootPath):
            if path.exists(frameRootPath + frameName + "_0" + frameRootExtension):
                imageIndex = 0
                while True:
                    if path.exists(frameRootPath + frameName + "_" + str(imageIndex) + frameRootExtension):
                        try:
                            self.frames.append(pygame.image.load(frameRootPath + frameName + "_" + str(imageIndex) + frameRootExtension).convert())
                        except:
                            debugPrint("Error loading frame: " + frameRootPath + frameName + "_" + str(imageIndex) + frameRootExtension)
                        imageIndex += 1
                    else:
                        break
                self.dimensions = (self.frames[0].get_width(), self.frames[0].get_height())
            elif path.exists(frameRootPath + frameName + frameRootExtension):
                try:
                    self.frames.append(pygame.image.load(frameRootPath + frameName + frameRootExtension).convert_alpha())
                except:
                    debugPrint("Error loading frame: " + frameRootPath + frameName + frameRootExtension)
            else:
                debugPrint("AnimatedImage: No images with '" + frameName + "' found in path '" + str(frameRootPath) + "'")
        else:
            debugPrint("AnimatedImage: Path '" + str(frameRootPath) + "' does not exist!")
        
        if importAnimPair and len(self.frames) > 0:
            self.fromImages(frameRootPath + frameName + ".txt")

    def loadFromAsset(self, frameName, frameRootPath):
        assetData = asset.File(data=FileInterface.getData(frameRootPath + frameName + ".arc"))
        isArj = False
        if len(assetData.data) == 0:
            assetData = asset.File(data=FileInterface.getData(frameRootPath + frameName + ".arj"))
            if len(assetData.data) > 0:
                isArj = True
        if len(assetData.data) > 0:
            assetData.decompress()
            assetImage = asset_image.LaytonAnimatedImage()
            assetImage.load(assetData.data, isArj=isArj)
            for indexImage, image in enumerate(assetImage.images):
                self.frames.append(pygame.image.fromstring(image.convert("RGB").tobytes("raw", "RGB"), image.size, "RGB").convert())
                if assetImage.alphaMask != None:
                    self.frames[indexImage].set_colorkey(assetImage.alphaMask)
            for anim in assetImage.anims:
                self.animMap[anim.name] = AnimatedFrameCollection(anim.frameDuration, indices=anim.indexImages, isFramerateTimeArray=True, faceOffset=anim.offsetFace)
        else:
            print("Failed to fetch image!!")

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
            debugPrint("AnimatedImage: Cannot import " + animText + " as it does not exist!")
            return False
    
    def reset(self):
        if self.animActive != None:
            self.animMap[self.animActive].reset()

    def getImage(self):
        try:
            return self.frames[self.animActiveFrame]
        except:
            return None

    def getAnim(self):
        return self.animActive
    
    def getAnimObject(self):
        if self.animActive != None:
            return self.animMap[self.animActive]
        return None

    def drawAlpha(self, gameDisplay):
        if self.animActiveFrame != None:
            if self.alpha > 0:
                if self.alpha == 255:
                    self.drawNormal(gameDisplay)
                else:
                    tempAlphaSurface = self.getImage().copy().convert_alpha()
                    tempAlphaSurface.fill((255, 255, 255, self.alpha), None, pygame.BLEND_RGBA_MULT)
                    gameDisplay.blit(tempAlphaSurface, self.pos)

    def drawNormal(self, gameDisplay):
        if self.animActiveFrame != None:
            gameDisplay.blit(self.getImage(), self.pos)

    def update(self, gameClockDelta):
        if self.animActive != None:
            tempFrame = self.animMap[self.animActive].getUpdatedFrame(gameClockDelta)
            self.animActiveFrame = tempFrame[1] 
            if not(tempFrame[0]):
                self.animActive = None

    def setAlpha(self, alpha):
        self.alpha = round(alpha)

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
    
    def setAnimationFromNameIfNotActive(self, anim):
        if self.animActive != anim:
            return self.setAnimationFromName(anim)
        return True
    
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
    
    def loopingDisable(self):
        for anim in self.animMap.keys():
            self.animMap[anim].loop = False

    def wasClicked(self, mousePos):
        if self.pos[0] + self.dimensions[0] >= mousePos[0] and mousePos[0] >= self.pos[0]:
            if self.pos[1] + self.dimensions[1] >= mousePos[1] and mousePos[1] >= self.pos[1]:
                return True
        return False

class StaticButton(StaticImage):
    def __init__(self, imagePath, x=0, y=0, imageIsSurface=False, imageIsNull=False, imageNullDimensions=None):
        StaticImage.__init__(self, imagePath, x=x, y=y, imageIsSurface=imageIsSurface, imageIsNull=imageIsNull, imageNullDimensions=imageNullDimensions)
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
        if self.wasClickedIn:
            self.wasClickedIn = False
            self.wasClickedOut = True
        else:
            self.reset()
    
    def handleEvent(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.registerButtonDown(event)   
        elif event.type == pygame.MOUSEBUTTONUP:
            self.registerButtonUp(event)

    def getPressedStatus(self):
        if self.wasClickedOut:
            self.reset()
            return True
        return False
    
    def peekPressedStatus(self):
        return self.wasClickedIn or self.wasClickedOut

class AnimatedButton(StaticButton):
    def __init__(self, imagePathInitial, imagePathPressed, imageIsSurface=False, useButtonFromAnim=False, x=0, y=0):
        if useButtonFromAnim:
            StaticButton.__init__(self, imagePathInitial.setAnimationFromNameAndReturnInitialFrame("off"), x=x, y=y, imageIsSurface=imageIsSurface)
            self.imageButtonPressed = StaticImage(imagePathInitial.setAnimationFromNameAndReturnInitialFrame("on"), x=x, y=y, imageIsSurface=imageIsSurface)
        else:
            StaticButton.__init__(self, imagePathInitial, x=x, y=y, imageIsSurface=imageIsSurface)
            self.imageButtonPressed = StaticImage(imagePathPressed, x=x, y=y, imageIsSurface=imageIsSurface)

    def setPos(self, pos):
        self.pos = pos
        self.imageButtonPressed.pos = pos
    
    def draw(self, gameDisplay):
        if self.wasClickedIn:
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
                debugPrint("Font: Error reading XML!")
            except ValueError:
                debugPrint("Font: Unsupported character spacing!")
            except FileNotFoundError:
                debugPrint("Font: No XML at path '" + fontXml + "'")

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
            debugPrint("Font: Path '" + fontImage + "' does not exist!")

    def getChar(self, char):
        try:
            return self.fontMap[char]
        except KeyError:
            return None

    def getSpacing(self):
        return self.fontSpacing
    
    def get_height(self):           # Used to preserve pygame compatibility
        return self.fontHeight + self.fontSpacing[1]

class FontVector():
    def __init__(self, font, yFontGap):
        self.font = font
        self.yFontGap = yFontGap
    def get_height(self):
        return self.font.get_height() + self.yFontGap

class AnimatedText():
    def __init__(self, font, initString = "", colour=(0,0,0)):
        self.text = initString
        self.drawnText = None
        self.textColour = colour
        self.font = font
        if type(self.font) == FontMap:
            # TODO - Remove control characters and colour code
            self.textRender = pygame.Surface((len(self.text) * self.font.fontWidth, self.font.fontHeight))
            if conf.ENGINE_PERFORMANCE_MODE:
                self.update = self.updateBitmapFontFast
            else:
                self.update = self.updateBitmapFont
            self.draw = self.drawBitmapFont
            self.updateBitmapFont(None)
        else:
            self.textRender = self.font.font.render(self.text,True,colour,None)
            self.update = self.updateRasterFont
            self.draw = self.drawRasterFont

    def updateRasterFont(self, gameClockDelta):
        self.textRender = self.font.font.render(self.text,True,self.textColour,None)

    def drawRasterFont(self, gameDisplay, location=(0,0)):
        textRect = self.textRender.get_rect()
        centX, centY = textRect.center
        x,y = location
        centY += y; centX += x
        textRect.center = (centX, centY)
        gameDisplay.blit(self.textRender, textRect)

    def updateBitmapFontFast(self, gameClockDelta): # Still expensive due to lots of drawing, but less expensive than the full version which includes colour support
        if self.drawnText != self.text:
            self.textRender = pygame.Surface((len(self.text) * (self.font.fontWidth + self.font.getSpacing()[0]), self.font.fontHeight + self.font.getSpacing()[1]))
            self.textRender.fill(self.font.fontBlendColour)
            self.textRender.set_colorkey(self.font.fontBlendColour)
            offsetX = 0
            for char in self.text:
                char = self.font.getChar(char)
                if char != None:
                    self.textRender.blit(char, (offsetX, 0))
                    offsetX += char.get_width() + self.font.getSpacing()[0]
            self.drawnText = self.text
    
    def updateBitmapFont(self, gameClockDelta):
        if self.drawnText != self.text:
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
            self.drawnText = self.text
    
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
        self.initialInverted = inverted

        self.reset()
        if conf.ENGINE_PERFORMANCE_MODE or mode == AnimatedFader.MODE_TRIANGLE:
            self.getStrength = self.getStrengthTriangle
        elif mode == AnimatedFader.MODE_SINE_SHARP:
            self.getStrength = self.getStrengthSineSingleEase
        elif mode == AnimatedFader.MODE_SINE_SMOOTH:
            self.getStrength = self.getStrengthSineDoubleEase
        else:
            debugPrint("AnimatedFader: Fader initialised with bad fade mode!")
            self.getStrength = self.getStrengthTriangle

    def reset(self):
        self.isActive = True
        self.inverted = self.initialInverted
        self.durationElapsed = 0

    def update(self, gameClockDelta):
        if self.isActive:
            self.durationElapsed += gameClockDelta
            while self.durationElapsed >= self.durationCycle:
                self.inverted = not(self.inverted)
                self.durationElapsed = self.durationElapsed - self.durationCycle
                if not(self.loop):
                    if self.doFullCycle:
                        if self.inverted == self.initialInverted:
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

class AnimatedImageWithFadeInOutPerAnim(AnimatedImage):
    def __init__(self, frameRootPath, frameName, durationCycle, inverted, mode, x=0,y=0, fromImport=True, importAnimPair=True, usesAlpha=False, frameRootExtension= conf.FILE_DECOMPRESSED_EXTENSION_IMAGE):
        AnimatedImage.__init__(self, frameRootPath, frameName, x=x,y=y, fromImport=fromImport, importAnimPair=importAnimPair, usesAlpha=usesAlpha, frameRootExtension=frameRootExtension)
        self.durationCycle = durationCycle
        self.inverted = inverted
        self.mode = mode
        self._faderReset()
        self.draw = self.drawAlpha
    
    def update(self, gameClockDelta):
        if self.timeTotalElapsed >= self.fadeOutTime and not(self.hasSecondFaderBeenActivated):
            self.hasSecondFaderBeenActivated = True
            self.fader = AnimatedFader(self.durationCycle, self.mode, False, cycle=False, inverted=not(self.inverted))
        else:
            self.timeTotalElapsed += gameClockDelta
        self.fader.update(gameClockDelta)
        self.alpha = (round(self.fader.getStrength() * 255))
        return super().update(gameClockDelta)
    
    def _faderReset(self):
        self.fader = AnimatedFader(self.durationCycle, self.mode, False, cycle=False, inverted=self.inverted)
        self.hasSecondFaderBeenActivated = False
        self.timeTotalElapsed = 0
        self.fadeOutTime = 0

    def getActiveState(self):
        return self.animActive != None or self.fader.isActive

    def reset(self):
        self._faderReset()
        return super().reset()

    def setAnimationFromName(self, anim):
        self._faderReset()
        out = super().setAnimationFromName(anim)
        if out:
            self.fadeOutTime = self.animMap[self.animActive].getAnimLength() - self.durationCycle
        return out
    
    def setAnimationFromIndex(self, index):
        self._faderReset()
        out = super().setAnimationFromIndex(index)
        if out:
            totalDuration = 0
            for duration in self.animMap[self.animActive].framerate:
                totalDuration += duration * (1000/60)
            self.fadeOutTime = totalDuration - self.durationCycle
        return out

class AlphaSurface():
    def __init__(self, alpha, dimensions=(conf.LAYTON_SCREEN_WIDTH, conf.LAYTON_SCREEN_HEIGHT * 2)):
        self.alpha = alpha
        self.surface = pygame.Surface(dimensions).convert_alpha()

    def setAlpha(self, alpha):
        self.alpha = alpha

    def draw(self, gameDisplay, location=(0,0)):
        if self.alpha > 0:
            if self.alpha == 255:
                gameDisplay.blit(self.surface, location)
            else:
                tempAlphaSurface = self.surface.copy().convert_alpha()
                tempAlphaSurface.fill((255, 255, 255, self.alpha), None, pygame.BLEND_RGBA_MULT)
                gameDisplay.blit(tempAlphaSurface, location)
    
    def clear(self):
        self.surface = pygame.Surface((self.surface.get_width(), self.surface.get_height())).convert_alpha()
        self.surface.fill((0,0,0,0))

class AnimatedTextLine(AnimatedText):
    def __init__(self, font, text, colour, indexLine):
        AnimatedText.__init__(self, font, initString=text, colour=colour)
        self.indexLine = indexLine

class NuvoTextScroller():

    DURATION_WAIT = 500

    LAYTON_CONTROL_CHAR = ["#", "@", "&"]

    def __init__(self, font, textInput, textPosOffset=(0,0), targetFramerate = conf.ENGINE_FPS):
        self.textInput = textInput
        self.frameStep = 1000/targetFramerate
        self.timeSinceLastUpdate = 0
        self.pos = textPosOffset
        self.font = font

        self.indexChar = 0
        self.indexLine = 0
        self.lines = []
        self.colour = (0,0,0)
        self.drawIncomplete = True
        self.isWaitingForTap = False
    
    def update(self, gameClockDelta):
        if self.drawIncomplete and not(self.isWaitingForTap):
            if self.indexChar < len(self.textInput):
                self.timeSinceLastUpdate += gameClockDelta
                while self.timeSinceLastUpdate >= self.frameStep and self.indexChar < len(self.textInput) and not(self.isWaitingForTap):
                    self.incrementText()
                    self.timeSinceLastUpdate -= self.frameStep
            else:
                self.drawIncomplete = False
    
    def skip(self):
        while self.indexChar < len(self.textInput) and not(self.isWaitingForTap):
            self.incrementText()

    def draw(self, gameDisplay):
        lastLineIndex = -1
        for textObj in self.lines:
            if lastLineIndex != textObj.indexLine: # Recalculate x
                x = self.pos[0]
                y = self.pos[1] + self.font.get_height() * textObj.indexLine
                lastLineIndex = textObj.indexLine
            textObj.draw(gameDisplay, location=(x,y))
            x += textObj.textRender.get_width()

    def reset(self):
        self.drawIncomplete = True
        self.isWaitingForTap = False
        self.indexChar = 0
        self.colour = (0,0,0)
        self.resetLinePointer()

    def resetLinePointer(self):
        self.lines = []
        self.indexLine = 0

    def doOnPaused(self):
        self.timeSinceLastUpdate -= NuvoTextScroller.DURATION_WAIT

    def doOnWaitToTap(self):
        self.isWaitingForTap = True

    def doOnTriggerAnimChange(self, animName):
        print("animSwitch", animName)

    def incrementText(self):
        nextChar = self.getNextChar()
        wasCharControlCharacter = False
        if nextChar[0] in NuvoTextScroller.LAYTON_CONTROL_CHAR[:2] or (nextChar[0] in NuvoTextScroller.LAYTON_CONTROL_CHAR and nextChar[-1] in NuvoTextScroller.LAYTON_CONTROL_CHAR):
            wasCharControlCharacter = True
        elif nextChar[0] == "<" and nextChar[-1] == ">":
            wasCharControlCharacter = True
        elif nextChar == "\n":
            wasCharControlCharacter = True

        if wasCharControlCharacter:
            if nextChar == "\n":
                self.indexLine += 1
            elif nextChar[0] == "#":
                # Change colour
                # TODO - Error check against colours
                self.colour = conf.GRAPHICS_FONT_COLOR_MAP[nextChar[1]]
            elif nextChar[0] == "@":
                if nextChar[1] == "B":
                    self.indexLine += 1
                elif nextChar[1] == "c":
                    self.resetLinePointer()
                elif nextChar[1] == "w":
                    self.doOnPaused()
                elif nextChar[1] == "p":
                    self.doOnWaitToTap()
                else:
                    debugPrint("NuvoUnhandledCommand: Unknown control character '"  + nextChar[1] + "'")

            elif nextChar[0] == "&":
                self.doOnTriggerAnimChange(nextChar[1:-1])

            if self.indexChar < len(self.textInput) and self.timeSinceLastUpdate >= self.frameStep and not(self.isWaitingForTap):
                self.incrementText() # Keep incrementing if control character used
        else:
            if len(self.lines) > 0:
                if self.lines[-1].indexLine == self.indexLine:
                    if self.lines[-1].textColour == self.colour: # Extend shape
                        self.lines[-1].text = self.lines[-1].text + nextChar
                    else: # Create new text
                        self.lines.append(AnimatedTextLine(self.font, nextChar, self.colour, self.indexLine))
                    self.lines[-1].update(None)
                else: # Add new text
                    self.lines.append(AnimatedTextLine(self.font, nextChar, self.colour, self.indexLine))
            else:
                self.lines.append(AnimatedTextLine(self.font, nextChar, self.colour, self.indexLine))

    def getNextChar(self):
        if self.textInput[self.indexChar] == "<":
            tempReplacementChar = ""
            while self.textInput[self.indexChar] != ">":
                tempReplacementChar = tempReplacementChar + self.textInput[self.indexChar]
                self.indexChar += 1
            self.indexChar += 1
            return tempReplacementChar + ">"
        elif self.textInput[self.indexChar] == "@" or self.textInput[self.indexChar] == "#":
            self.indexChar += 2
            return self.textInput[self.indexChar - 2:self.indexChar]
        elif self.textInput[self.indexChar] == "&":
            tempReplacementChar = "&"
            self.indexChar += 1
            # TODO - Fix error lol
            while self.textInput[self.indexChar] != "&":
                tempReplacementChar = tempReplacementChar + self.textInput[self.indexChar]
                self.indexChar += 1
            self.indexChar += 1
            return tempReplacementChar + "&"
        else:
            self.indexChar += 1
            return self.textInput[self.indexChar - 1]