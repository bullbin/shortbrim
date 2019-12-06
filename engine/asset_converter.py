import math, binary
from PIL import Image

USE_LIMITED_GAME_COLOUR = True
EXPORT_EXTENSION = "png"

class ArrayImage():
    def __init__(self):
        self.res = (0,0)
        self.image = []

    def getPilImage(self):
        multiplier = 255
        if USE_LIMITED_GAME_COLOUR:
            multiplier = 248
        writer = binary.BinaryWriter()
        for row in self.image:
            for pixel in row:
                writer.writeIntList([round(pixel.r * multiplier), round(pixel.g * multiplier), round(pixel.b * multiplier)] , 1)
        return Image.frombytes("RGB", self.res, bytes(writer.data))
        
class Colour():
    def __init__(self, r = 1, g = 1, b = 1):
        self.r = r
        self.g = g
        self.b = b
    
    @staticmethod
    def fromInt(encodedColour):
        colourOut = Colour()
        colourOut.b = ((encodedColour >> 10) & 0x1f) / 31
        colourOut.g = ((encodedColour >> 5) & 0x1f) / 31
        colourOut.r = (encodedColour & 0x1f) / 31
        return colourOut
    
    def toList(self):
        if USE_LIMITED_GAME_COLOUR:
            return ([int(self.r * 248), int(self.g * 248), int(self.b * 248)])
        return ([int(self.r * 255), int(self.g * 255), int(self.b * 255)])

class Tile(ArrayImage):
    def __init__(self, data=None):
        ArrayImage.__init__(self)
        self.data = data
        self.offset = (0,0)
        self.res = (8,8)
    
    def fetchData(self, reader, bpp):
        self.offset = (reader.readU2(), reader.readU2())
        self.res = (2 ** (3 + reader.readU2()), 2 ** (3 + reader.readU2()))
        self.data = reader.read(int(bpp / 8 * self.res[0] * self.res[1]))

    def decodeToPil(self, palette, bpp):
        image = Image.new("P", self.res)
        image.putpalette(palette)
        pixelY = -1
        for indexPixel in range(int(self.res[0] * self.res[1] * (bpp/8))):
            pixelByte = self.data[indexPixel]
            if indexPixel % int(self.res[0] * bpp/8) == 0:
                pixelY += 1
                pixelX = 0
            for _indexSubPixel in range(int(1/(bpp/8))):
                image.putpixel((pixelX, pixelY), (pixelByte & ((2**bpp) - 1)) % len(palette))
                pixelByte = pixelByte >> bpp
                pixelX += 1
        return image
    
    def decodeToPilArj(self, palette, bpp):
        image = Image.new("P", self.res)
        image.putpalette(palette)
        pixelIndex = 0
        for ht in range(self.res[1] // 8):
            for wt in range(self.res[0] // 8):
                for h in range(8):
                    for w in range(8):
                        if bpp == 4:
                            pixelByte = self.data[pixelIndex // 2]
                            if pixelIndex % 2 == 1:
                                pixelByte = pixelByte >> bpp
                            pixelByte = pixelByte & ((2**bpp) - 1)
                        else:
                            pixelByte = self.data[pixelIndex]
                        image.putpixel((w + wt * 8, h + ht * 8), pixelByte % len(palette))
                        pixelIndex += 1
        return image

class TiledImage(ArrayImage):
    def __init__(self):
        ArrayImage.__init__(self)
        self.tiles = []
    
    def getPilConstructedImage(self, palette, bpp, isArj):
        # TODO : Fill with transparency
        outputImage = Image.new('P', self.res)
        outputImage.putpalette(palette)
        for tile in self.tiles:
            if isArj:
                outputImage.paste(tile.decodeToPilArj(palette, bpp), box=tile.offset)
            else:
                outputImage.paste(tile.decodeToPil(palette, bpp), box=tile.offset)
        return outputImage

class AnimationBasicSequence():
    def __init__(self):
        self.indexFrames = []
        self.frameDuration = []
        self.indexImages = []
        self.name = "Create an Animation"
    def __str__(self):
        return "Animation Details\nName:\t" + self.name + "\nFrmIdx:\t" + str(self.indexFrames) + "\nImgIdx:\t" + str(self.indexImages) + "\nUnkFrm:\t" + str(self.frameDuration) + "\n"

class LaytonAnimatedImage():
    def __init__(self):
        self.filename = None
        self.images = []
        self.anims = []
    
    def load(self, filename, isArj = False):
        reader = binary.BinaryReader(filename = filename)
        self.filename = filename
        countImages = reader.readU2()
        bpp = 2 ** (reader.readU2() - 1)
        if isArj:
            countColours = reader.readU4()

        for indexImage in range(countImages):
            self.images.append(TiledImage())
            self.images[indexImage].res = (reader.readU2(), reader.readU2())
            imageCountTiles = reader.readU4()
            for indexTile in range(imageCountTiles):
                self.images[indexImage].tiles.append(Tile())
                if isArj:
                    reader.seek(4,1)
                self.images[indexImage].tiles[indexTile].fetchData(reader, bpp)
        
        if not(isArj):
            countColours = reader.readU4()

        palette = self.getPaletteAndAnimations(reader, countColours)
        for indexImage, image in enumerate(self.images):
            self.images[indexImage] = image.getPilConstructedImage(palette, bpp, isArj)
            
    def getPaletteAndAnimations(self, reader, countColours):
        palette = []
        for _indexColour in range(countColours):
            palette.extend(Colour.fromInt(reader.readU2()).toList())
        
        reader.seek(30, 1)
        countAnims = reader.readU4()
        for indexAnim in range(countAnims):
            self.anims.append(AnimationBasicSequence())
            tempName = ((reader.read(30)).decode("ascii")).split("\x00")[0]
            self.anims[indexAnim].name = tempName

        for indexAnim in range(countAnims):
            countFrames = reader.readU4()
            for _indexFrame in range(countFrames):
                self.anims[indexAnim].indexFrames.append(reader.readU4())
            for _indexFrame in range(countFrames):
                self.anims[indexAnim].frameDuration.append(reader.readU4())
            for _indexFrame in range(countFrames):
                self.anims[indexAnim].indexImages.append(reader.readU4())
        return palette

    def generate(self):
        tileSize = 64
        maxRes = (0,0)
        for image in self.images:
            maxRes = (maxRes[0] + image.size[0], max(maxRes[1], image.size[1]))
        paletteSurface = Image.new('RGB', maxRes)
        offsetX = 0
        for image in self.images:
            paletteSurface.paste(image, box=(offsetX, 0))
            offsetX += image.size[0]

        paletteSurface = paletteSurface.quantize(colors=10)

        writer = binary.BinaryWriter()
        writer.writeU2(len(self.images))
        bpp = math.log(int(math.ceil(math.ceil(math.log(len(paletteSurface.getcolors()), 2)) / 4) * 4), 2)
        writer.writeU2(int(bpp) + 1)
        bpp = 2 ** bpp

        offsetX = 0
        for indexImage, image in enumerate(self.images):
            imageTilemap = []
            imageTiles = []
            image = paletteSurface.crop((offsetX, 0, offsetX + image.size[0], image.size[1]))
            
            for tileResY in range(self.images[indexImage].size[1] // tileSize):
                for tileResX in range(self.images[indexImage].size[0] // tileSize):
                    tempTile = paletteSurface.crop(((tileResX * tileSize) + offsetX,
                                                    tileResY * tileSize,
                                                    ((tileResX + 1) * tileSize) + offsetX,
                                                    (tileResY + 1) * tileSize))
                    if tempTile in imageTiles:
                        imageTilemap.append(imageTiles.index(tempTile))
                    else:
                        imageTilemap.append(len(imageTiles))
                        imageTiles.append(tempTile)
            offsetX += image.size[0]

            writer.writeIntList([image.size[0], image.size[1]], 2)

    def export(self):
        for i, image in enumerate(self.images):
            image.save('.'.join(self.filename.split("//")[-1].split(".")[0:-1]) + "_" + str(i) + "." + EXPORT_EXTENSION)
    
class LaytonArjReader(LaytonAnimatedImage):
    def __init__(self, filename):
        LaytonAnimatedImage.__init__(self)
        self.load(filename, isArj=True)

class LaytonArcReader(LaytonAnimatedImage):
    def __init__(self, filename):
        LaytonAnimatedImage.__init__(self)
        self.load(filename, isArj=False)

class LaytonBackgroundImage():
    def __init__(self):
        self.filename = None
        self.statAlignedBpp = 8
        self.image = None

    def load(self, filename):
        reader = binary.BinaryReader(filename = filename)
        self.filename = filename

        lengthPalette = reader.readU4()
        palette = []
        for _indexColour in range(lengthPalette):
            palette.extend(Colour.fromInt(reader.readU2()).toList())

        self.countTile = reader.readU4()
        tilePilMap = {}
        for index in range(self.countTile):
            tilePilMap[index] = Tile(data=reader.read(int((self.statAlignedBpp * 64) / 8))).decodeToPil(palette, self.statAlignedBpp)
        
        resTile = [reader.readU2(), reader.readU2()]
        self.image = Image.new("P", (int(resTile[0] * 8), int(resTile[1] * 8)))
        self.image.putpalette(palette)

        for y in range(resTile[1]):
            for x in range(resTile[0]):
                tempSelectedTile = reader.readU2()
                tileSelectedIndex = tempSelectedTile & (2 ** 10 - 1)
                tileSelectedFlipX = tempSelectedTile & (2 ** 11)
                tileSelectedFlipY = tempSelectedTile & (2 ** 10)

                if tileSelectedIndex < (2 ** 10 - 1):
                    # TODO: Blank out tile (should be default if alpha added)
                    tileFocus = tilePilMap[tileSelectedIndex % self.countTile]
                    if tileSelectedFlipX:
                        tileFocus = tileFocus.transpose(method=Image.FLIP_LEFT_RIGHT)
                    if tileSelectedFlipY:
                        tileFocus = tileFocus.transpose(method=Image.FLIP_TOP_BOTTOM)
                    self.image.paste(tileFocus, (x*8, y*8))

    def export(self):
        self.image.save('.'.join(self.filename.split("//")[-1].split(".")[0:-1]) + "." + EXPORT_EXTENSION)

debug = LaytonArjReader("anna.arj")
#debug = LaytonArcReader("aroma.arc")
debug = LaytonBackgroundImage()
debug.load("chapter1.arc")
debug.export()
#debug.generate()