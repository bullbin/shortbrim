import math,sys

useAccurateColour = True
bakeAlpha = True

class DdsImage():
    def __init__(self):
        self.resX = 0
        self.resY = 0
        self.image = []

    def flipX(self):
        for rowIndex in range(len(self.image)):
            self.image[rowIndex].reverse()

    def flipY(self):
        self.image.reverse()

    def getData(self):
        ddsHeader = bytearray(b''.join([b'DDS \x7c\x00\x00\x00\x07\x10\x00\x00', 
                                self.resY.to_bytes(4, byteorder = 'little'),
                                self.resX.to_bytes(4, byteorder = 'little'),                    
                                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
                                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00',
                                b'\x20\x00\x00\x00\x41\x00\x00\x00\x00\x00\x00\x00']))
        if (useAccurateColour):
            ddsHeader.extend(b'\x20\x00\x00\x00\x00\x00\xFF\x00\x00\xFF\x00\x00\xFF\x00\x00\x00\x00\x00\x00\xFF')
        else:
            ddsHeader.extend(b'\x10\x00\x00\x00')
            ddsHeader.extend(((2 ** 10) + (2 ** 11) + (2 ** 12) + (2 ** 13) + (2 ** 14)).to_bytes(4, byteorder = 'little'))      # B mask
            ddsHeader.extend(((2 ** 5) + (2 ** 6) + (2 ** 7) + (2 ** 8) + (2 ** 9)).to_bytes(4, byteorder = 'little'))           # G mask
            ddsHeader.extend(((2 ** 0) + (2 ** 1) + (2 ** 2) + (2 ** 3) + (2 ** 4)).to_bytes(4, byteorder = 'little'))           # R mask (rightmost bits)
            ddsHeader.extend((2 ** 15).to_bytes(4, byteorder = 'little'))  
        ddsHeader.extend(b'\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
        for row in self.image:
            for pixel in row:
                if useAccurateColour:
                    ddsHeader.extend(round(pixel.b * 255).to_bytes(1, byteorder = 'little'))
                    ddsHeader.extend(round(pixel.g * 255).to_bytes(1, byteorder = 'little'))
                    ddsHeader.extend(round(pixel.r * 255).to_bytes(1, byteorder = 'little'))
                    ddsHeader.extend(round(pixel.a * 255).to_bytes(1, byteorder = 'little'))
                else:
                    tempPixel = 0
                    tempPixel += round(pixel.b * 31)
                    tempPixel += round(pixel.g * 31) << 5
                    tempPixel += round(pixel.r * 31) << 10
                    tempPixel += round(pixel.a) << 15
                    ddsHeader.extend(tempPixel.to_bytes(2, byteorder = 'little'))   
        return ddsHeader
        
    def export(self, filename):
        with open(filename, 'wb') as ddsOut:
            ddsOut.write(self.getData())
        
class Colour():
    def __init__(self, r = 1, g = 1, b = 1, a = 1):
        self.r = r
        self.g = g
        self.b = b
        self.a = a
            
    def fromBytesLayton(encodedColour, pixelDivide = [1,5,5,5], pixelColour = [3,2,1,0], invert = [False, False, False, False], useColourMaskAsAlpha = False, colourMask = None):
        encodedBits = []
        for bit in range(16):
            encodedBits.insert(0, encodedColour & 1)
            encodedColour = encodedColour >> 1
            
        bitPosition = 0
        colourOut = Colour(0,0,0,1)
        for indexColour in range(len(pixelColour)):
            intensity = 0
            if pixelDivide[indexColour] > 1:
                for bitColourAppend in range(pixelDivide[indexColour]):
                    intensity += ((2 ** (7 - bitColourAppend)) * encodedBits[bitPosition])
                    bitPosition += 1
                if useAccurateColour:
                    intensity = intensity / 255
                else:
                    intensity = intensity / 248
            else:
                intensity = encodedBits[bitPosition]
                bitPosition += 1
            
            if pixelColour[indexColour] == 0:
                if invert[indexColour]:
                    colourOut.r = 1 - intensity
                else:
                    colourOut.r = intensity
            elif pixelColour[indexColour] == 1:
                if invert[indexColour]:
                    colourOut.g = 1 - intensity
                else:
                    colourOut.g = intensity
            elif pixelColour[indexColour] == 2:
                if invert[indexColour]:
                    colourOut.b = 1 - intensity
                else:
                    colourOut.b = intensity
        
        if useColourMaskAsAlpha and bakeAlpha:
            if colourOut.r == colourMask.r and colourOut.g == colourMask.g and colourOut.b == colourMask.b:
                colourOut.a = 0
        return colourOut

class Tile(DdsImage):
    def __init__(self):
        DdsImage.__init__(self)
        self.data = None
        self.resX = 8
        self.resY = 8
    
    def fetchData(self, reader, bpp):
        self.offsetX = int.from_bytes(reader.read(2), byteorder = 'little')
        self.offsetY = int.from_bytes(reader.read(2), byteorder = 'little')
        self.resX = 2 ** (3 + int.from_bytes(reader.read(2), byteorder = 'little'))
        self.resY = 2 ** (3 + int.from_bytes(reader.read(2), byteorder = 'little'))
        self.data = reader.read(int(bpp / 8 * self.resX * self.resY))
        
    def decode(self, palette, bpp):
        for indexPixel in range(int(self.resX * self.resY * (bpp/8))):
            pixelByte = self.data[indexPixel]
            if indexPixel % int(self.resX * bpp/8) == 0:
                self.image.append([])
            for indexSubPixel in range(int(1/(bpp/8))):
                self.image[-1].append(palette[(pixelByte & ((2**bpp) - 1)) % len(palette)])
                pixelByte = pixelByte >> bpp
    
    def decodeArj(self, palette, bpp):
        for y in range(self.resY):
            self.image.append([])
            for x in range(self.resX):
                self.image[y].append(Colour(0,0,0,1))
        
        pixelIndex = 0
        for ht in range(self.resY // 8):
            for wt in range(self.resX // 8):
                for h in range(8):
                    for w in range(8):
                        if bpp == 4:
                            pixelByte = self.data[pixelIndex // 2]
                            if pixelIndex % 2 == 1:
                                pixelByte = pixelByte >> bpp
                            pixelByte = pixelByte & ((2**bpp) - 1)
                        else:
                            pixelByte = self.data[pixelIndex]
                        self.image[h + ht * 8][w + wt * 8] = palette[pixelByte % len(palette)]
                        pixelIndex += 1

class TiledImage(DdsImage):
    def __init__(self):
        DdsImage.__init__(self)
        self.tiles = []
    
    def constructImage(self, palette, bpp):
        for y in range(self.resY):
            self.image.append([])
            for x in range(self.resX):
                self.image[-1].append(Colour(0,0,0,1))

        for tile in self.tiles:
            for y in range(tile.resY):
                for x in range(tile.resX):
                    if y + tile.offsetY < self.resY and x + tile.offsetX < self.resX:
                        self.image[y + tile.offsetY][x + tile.offsetX] = tile.image[y][x]

class AnimationBasicSequence():
    def __init__(self):
        self.indexFrames = []
        self.frameDuration = []
        self.indexImages = []
        self.name = "Create an Animation"
    def __str__(self):
        return "Animation Details\nName:\t" + self.name + "\nFrmIdx:\t" + str(self.indexFrames) + "\nImgIdx:\t" + str(self.indexImages) + "\nUnkFrm:\t" + str(self.frameDuration) + "\n"

class LaytonArj():
    def __init__(self, filename):
        self.filename = filename
        self.statAlignedBpp = 4
        self.palette = []
        self.images = []
        self.anims = []
        self.load()
    
    def load(self):
        with open(self.filename, 'rb') as laytonIn:
            countImages    = int.from_bytes(laytonIn.read(2), byteorder = 'little')
            self.statAlignedBpp = 2 ** (int.from_bytes(laytonIn.read(2), byteorder = 'little') - 1)
            countColours = int.from_bytes(laytonIn.read(4), byteorder = 'little')

            for indexImage in range(countImages):
                self.images.append(TiledImage())
                self.images[indexImage].resX = int.from_bytes(laytonIn.read(2), byteorder = 'little')
                self.images[indexImage].resY = int.from_bytes(laytonIn.read(2), byteorder = 'little')
                imageCountTiles = int.from_bytes(laytonIn.read(2), byteorder = 'little')
                laytonIn.seek(2,1)
                for indexTile in range(imageCountTiles):
                    self.images[indexImage].tiles.append(Tile())
                    laytonIn.seek(4, 1) # Skip glbX, glbY
                    self.images[indexImage].tiles[indexTile].fetchData(laytonIn, self.statAlignedBpp)

            self.loadPaletteAndAnimations(laytonIn, countColours)
    
    def loadPaletteAndAnimations(self, reader, countColours):
        for indexColour in range(countColours):
            if useAccurateColour:
                self.palette.append(Colour.fromBytesLayton(int.from_bytes(reader.read(2), byteorder = 'little'), useColourMaskAsAlpha=True, colourMask=Colour(0,248/255,0,0)))
            else:
                self.palette.append(Colour.fromBytesLayton(int.from_bytes(reader.read(2), byteorder = 'little'), useColourMaskAsAlpha=True, colourMask=Colour(0,1,0,0)))
        
        reader.seek(30, 1)
        countAnims = int.from_bytes(reader.read(4), byteorder = 'little')
        for indexAnim in range(countAnims):
            self.anims.append(AnimationBasicSequence())
            tempName = ((reader.read(30)).decode("ascii")).split("\x00")[0]
            self.anims[indexAnim].name = tempName

        for indexAnim in range(countAnims):
            countFrames = int.from_bytes(reader.read(4), byteorder = 'little')
            for indexFrame in range(countFrames):
                self.anims[indexAnim].indexFrames.append(int.from_bytes(reader.read(4), byteorder = 'little'))
            for indexFrame in range(countFrames):
                self.anims[indexAnim].frameDuration.append(int.from_bytes(reader.read(4), byteorder = 'little'))
            for indexFrame in range(countFrames):
                self.anims[indexAnim].indexImages.append(int.from_bytes(reader.read(4), byteorder = 'little'))
            #print(self.anims[indexAnim])

    def exportAnimText(self):
        with open('.'.join(self.filename.split("//")[-1].split(".")[0:-1]) + ".txt", 'w+') as animText:
            for anim in self.anims:
                if len(anim.indexFrames) > 0:
                    animText.write(anim.name + "\n")
                    totalDur = 0
                    for dur in anim.frameDuration:
                        totalDur += dur
                    totalDur = round(60 / (totalDur / len(anim.frameDuration)))
                    animText.write(str(totalDur) + "\nTrue,True,0,248,0\n" + str(anim.indexImages[0]))
                    for indexImage in anim.indexImages[1:]:
                        animText.write("," + str(indexImage))
                    animText.write("\n")

    def export(self):
        self.exportAnimText()
        for i, image in enumerate(self.images):
            for tile in image.tiles:
                tile.decodeArj(self.palette, self.statAlignedBpp)
            image.constructImage(self.palette, self.statAlignedBpp)
            image.export('.'.join(self.filename.split("//")[-1].split(".")[0:-1]) + "_" + str(i) + ".dds")

class LaytonArc(LaytonArj):
    def __init__(self, filename):
        LaytonArj.__init__(self, filename)

    def load(self):
        with open(self.filename, 'rb') as laytonIn:
            countImages    = int.from_bytes(laytonIn.read(2), byteorder = 'little')
            self.statAlignedBpp = 2 ** (int.from_bytes(laytonIn.read(2), byteorder = 'little') - 1)

            for indexImage in range(countImages):
                self.images.append(TiledImage())
                self.images[-1].resX = int.from_bytes(laytonIn.read(2), byteorder = 'little')
                self.images[-1].resY = int.from_bytes(laytonIn.read(2), byteorder = 'little')
                imageCountTiles = int.from_bytes(laytonIn.read(4), byteorder = 'little')
                for indexTile in range(imageCountTiles):
                    self.images[-1].tiles.append(Tile())
                    self.images[-1].tiles[-1].fetchData(laytonIn, self.statAlignedBpp)
            
            countColours = int.from_bytes(laytonIn.read(4), byteorder = 'little')
            self.loadPaletteAndAnimations(laytonIn, countColours)

    def export(self):
        self.exportAnimText()
        for i, image in enumerate(self.images):
            for tile in image.tiles:
                tile.decode(self.palette, self.statAlignedBpp)
            image.constructImage(self.palette, self.statAlignedBpp)
            image.export('.'.join(self.filename.split("//")[-1].split(".")[0:-1]) + "_" + str(i) + ".dds")

class LaytonImage():
    def __init__(self, filename):
        self.filename = filename
        self.countTile = 0
        self.palette = []
        self.tiles = []
        self.tilesReconstructed = []
        self.statAlignedBpp = 8
        self.outputImage = DdsImage()
        self.load()

    def load(self):
        with open(self.filename, 'rb') as laytonIn:
            self.lengthPalette = int.from_bytes(laytonIn.read(4), byteorder = 'little')
            for indexColour in range(self.lengthPalette):
                if useAccurateColour:
                    self.palette.append(Colour.fromBytesLayton(int.from_bytes(laytonIn.read(2), byteorder = 'little'), useColourMaskAsAlpha=True, colourMask=Colour(224/255, 0, 120/255, 0)))
                else:
                    self.palette.append(Colour.fromBytesLayton(int.from_bytes(laytonIn.read(2), byteorder = 'little'), useColourMaskAsAlpha=True, colourMask=Colour(224/248, 0, 120/248, 0)))

            self.countTile = int.from_bytes(laytonIn.read(4), byteorder = 'little')
            for index in range(self.countTile):
                self.tiles.append(Tile())
                self.tiles[index].data = laytonIn.read(int((self.statAlignedBpp * 64) / 8))
                self.tiles[index].decode(self.palette, self.statAlignedBpp)
            
            resTileX = int.from_bytes(laytonIn.read(2), byteorder = 'little')
            resTileY = int.from_bytes(laytonIn.read(2), byteorder = 'little')

            for indexTile in range(int(resTileX * resTileY)):
                tempSelectedTile = int.from_bytes(laytonIn.read(2), byteorder = 'little')

                tileSelectedIndex = tempSelectedTile & (2 ** 10 - 1)
                tileSelectedFlipX = tempSelectedTile & (2 ** 11)
                tileSelectedFlipY = tempSelectedTile & (2 ** 10)
                tileSelectedPaletteId = tempSelectedTile >> 14

                if tileSelectedIndex == (2 ** 10 - 1):
                    tempTile = Tile()
                    for xResFill in range(8):
                        tempTile.image.append([])
                        for yResFill in range(8):
                            tempTile.image[xResFill].append(Colour(0,0,0,1))
                    self.tilesReconstructed.append(tempTile)
                else:
                    tileFocus = self.tiles[tileSelectedIndex % self.countTile]
                    if tileSelectedFlipX:
                        tileFocus.flipX()
                    if tileSelectedFlipY:
                        tileFocus.flipY()
                    self.tilesReconstructed.append(tileFocus)

        self.outputImage.resX = int(resTileX * 8)
        self.outputImage.resY = int(resTileY * 8)
        self.outputImage.image = []

        indexTile = 0
        for yTile in range(int(self.outputImage.resY / 8)):
            self.outputImage.image.extend([[],[],[],[],[],[],[],[]])
            for xTile in range(int(self.outputImage.resX / 8)):
                for yRes in range(8):
                    self.outputImage.image[(yTile * 8) + yRes].extend(self.tilesReconstructed[indexTile].image[yRes])
                indexTile += 1

    def export(self):
        self.outputImage.export('.'.join(self.filename.split("//")[-1].split(".")[0:-1]) + ".dds")