import math

useAccurateColour = True

class ddsImage():
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
        
class colour():
    def __init__(self, r = 1, g = 1, b = 1, a = 0):
        self.r = r
        self.g = g
        self.b = b
        self.a = a
            
    def fromBytesLayton(encodedColour, pixelDivide = [1,5,5,5], pixelColour = [3,2,1,0], invert = [True, False, False, False]):
        encodedBits = []
        for bit in range(16):
            encodedBits.insert(0, encodedColour & 1)
            encodedColour = encodedColour >> 1
            
        bitPosition = 0
        colourOut = colour(0,0,0,0)
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
        if useAccurateColour:
            if not(colourOut.r == 224/255 and colourOut.g == 0 and colourOut.b == 120/255):
                colourOut.a = 1
        else:
            if not(colourOut.r == 224/248 and colourOut.g == 0 and colourOut.b == 120/248):
                colourOut.a = 1
        return colourOut

class tile(ddsImage):
    def __init__(self):
        ddsImage.__init__(self)
        
    def decode(self, data, bpp, palette, xRes = 8, yRes = 8):
        self.resX = xRes
        self.resY = yRes

        for indexPixel in range(int(xRes * yRes * (bpp/8))):
            pixelByte = data[indexPixel]
            if indexPixel % int(xRes * bpp/8) == 0:
                self.image.append([])
            for indexSubPixel in range(int(1/(bpp/8))):
                self.image[-1].append(palette[(pixelByte & ((2**bpp) - 1)) % len(palette)])
                pixelByte = pixelByte >> bpp   

class laytonImage():
    def __init__(self, filename):
        self.filename = filename
        self.countTile = 0
        self.palette = []
        self.tiles = []
        self.tilesReconstructed = []
        self.statAlignedBpp = 8
        self.outputImage = ddsImage()
        self.load()

    def load(self):
        with open(self.filename, 'rb') as laytonIn:
            self.lengthPalette = int.from_bytes(laytonIn.read(4), byteorder = 'little')
            for indexColour in range(self.lengthPalette):
                self.palette.append(colour.fromBytesLayton(int.from_bytes(laytonIn.read(2), byteorder = 'little')))
                
            self.countTile = int.from_bytes(laytonIn.read(4), byteorder = 'little')
            for index in range(self.countTile):
                self.tiles.append(tile())
                self.tiles[-1].decode(laytonIn.read(int((self.statAlignedBpp * 64) / 8)), self.statAlignedBpp, self.palette)
            
            resTileX = int.from_bytes(laytonIn.read(2), byteorder = 'little')
            resTileY = int.from_bytes(laytonIn.read(2), byteorder = 'little')

            for indexTile in range(int(resTileX * resTileY)):
                tempSelectedTile = int.from_bytes(laytonIn.read(2), byteorder = 'little')

                tileSelectedIndex = tempSelectedTile & (2 ** 10 - 1)
                tileSelectedFlipX = tempSelectedTile & (2 ** 11)
                tileSelectedFlipY = tempSelectedTile & (2 ** 10)
                tileSelectedPaletteId = tempSelectedTile >> 14

                if tileSelectedIndex == (2 ** 10 - 1):
                    tempTile = tile()
                    for xResFill in range(8):
                        tempTile.image.append([])
                        for yResFill in range(8):
                            tempTile.image[xResFill].append(colour(0,0,0,0))
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
