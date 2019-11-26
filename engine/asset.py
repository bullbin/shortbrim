import binary, ndspy
from os import remove, rename, makedirs

class File():
    def __init__(self, name, data = b'', extension = ''):
        self.name = name
        self.data = bytearray(data)
        self.extension = extension
    
    def __str__(self):
        return str(len(self.data)) + "\t" + self.name
    
    def decompress(self):
        pass

    def compressHuffman(self):
        pass

    def decompressHuffman(self, offsetIn=0):
        pass

    def compressRle(self):
        writer = binary.BinaryWriter()
        reader = binary.BinaryReader(data = self.data)

        tempCompressedByte = b''
        tempCompressedByteLength = 0
        tempUncompressedSection = bytearray(b'')
        compressRepetition = False

        def getRleFlagByte(isCompressed, length):
            if isCompressed:
                return (0x80 | (length - 3)).to_bytes(1, byteorder = 'little')
            return (length - 1).to_bytes(1, byteorder = 'little')
        
        def writeData():
            if len(tempUncompressedSection) > 0:
                writer.write(getRleFlagByte(False, len(tempUncompressedSection)) + tempUncompressedSection)
            if tempCompressedByteLength > 0:
                writer.write(getRleFlagByte(True, tempCompressedByteLength) + tempCompressedByte)
        
        while reader.hasDataRemaining():
            tempByte = reader.read(1)
            if compressRepetition:
                if tempByte == tempCompressedByte:
                    tempCompressedByteLength += 1
                if tempCompressedByteLength == 130 or tempByte != tempCompressedByte:   # If max size has been reached or there's no more repetition
                    compressRepetition = False
                    if tempCompressedByteLength < 3:                                    # Free data if compression won't do much
                        tempUncompressedSection.extend((tempCompressedByte * tempCompressedByteLength) + tempByte)
                    else:                                                               # Else, write uncompressed section, then compressed data
                        writeData()
                        if tempByte == tempCompressedByte:                              # If the compression ended because the max block size was met,
                            tempUncompressedSection = bytearray(b'')                    #     reinitiate the uncompressed section.
                        else:
                            tempUncompressedSection = bytearray(tempByte)               # Else, continue the uncompressed section as normal.
                    tempCompressedByteLength = 0
            else:
                tempUncompressedSection.extend(tempByte)
                if len(tempUncompressedSection) == 128:                                 # Reinitiate block if max size met
                    writeData()
                    tempUncompressedSection = bytearray(b'')
                elif len(tempUncompressedSection) > 1 and tempUncompressedSection[-2] == tempUncompressedSection[-1]:
                    tempCompressedByte = tempByte
                    tempCompressedByteLength = 2
                    compressRepetition = True
                    tempUncompressedSection = tempUncompressedSection[0:-2]
        # Write anything left, as there may be blocks remaining after the reader ran out of data
        writeData()
        self.data = bytearray(b'\x30' + len(self.data).to_bytes(3, byteorder = 'little') + writer.data)
            
    def decompressRle(self, offsetIn=0):
        reader = binary.BinaryReader(data = self.data)
        reader.seek(offsetIn + 1)
        tempFilesize = int.from_bytes(reader.read(3), byteorder = 'little')
        writer = binary.BinaryWriter()
        while writer.getLength() < tempFilesize:
            flag = int.from_bytes(reader.read(1), byteorder = 'little')
            isCompressed = (flag & 0x80) > 0
            if isCompressed:
                decompressedLength = (flag & 0x7f) + 3
                decompressedData = reader.read(1)
                for _indexByte in range(decompressedLength):
                    writer.write(decompressedData)
            else:
                decompressedLength = (flag & 0x7f) + 1
                writer.write(reader.read(decompressedLength))
        self.data = writer.data
    
    def compressLz10(self, addHeader=False):
        self.data = ndspy.lz10.compress(self.data)

    def decompressLz10(self, offsetIn=0):
        self.data = ndspy.lz10.decompress(self.data[offsetIn:])

    def export(self, filepath):
        # Add a method to BinaryWriter to do this
        try:
            if self.extension != '':
                extension = '.' + self.extension
            else:
                extension = ''
            with open(filepath + self.name + extension, 'wb') as dataOut:
                dataOut.write(self.data)
            return True
        except IOError:
            print("Error writing file!")
            return False
    
    @staticmethod
    def create(filepath):
        reader = binary.BinaryReader(filename = filepath)
        tempName = filepath.split("//")[-1]
        if tempName == "":
            print("Warning: Invalid filename!")
            tempName = "NULL"
        return File(tempName, reader.data)

class Archive(File):
    def __init__(self, name):
        File.__init__(self, name)
        self.files = []
    
    def load(self, data):
        pass

    def save(self):
        pass

    def extract(self, filepath):
        outputFilepath = "\\".join(filepath.split("\\")) + "\\" + self.name.split("\\")[-1]
        makedirs(outputFilepath, exist_ok=True)
        for fileChunk in self.files:
            with open(outputFilepath + "\\" + fileChunk.name, 'wb') as dataOut:
                dataOut.write(fileChunk.data)

    def export(self, filepath):
        self.save()
        super().export(filepath)
    
    @staticmethod
    def create(filepath):
        pass

class LaytonPack(Archive):

    METADATA_BLOCK_SIZE = 16
    MAGIC               = [b'LPCK', b'PCK2']

    def __init__(self, name, version = 0):
        Archive.__init__(self, name)
        self._version = version

    def load(self, data):
        reader = binary.BinaryReader(data = data)
        offsetHeader = reader.readU4()
        lengthArchive = reader.readU4()
        magic = reader.read(4)
        try:
            self._version = LaytonPack.MAGIC.index(magic)
            reader.seek(offsetHeader)
            while reader.tell() != lengthArchive:
                metadata = reader.readU4List(4)
                self.files.append(File(name = reader.readPaddedString(metadata[0] - LaytonPack.METADATA_BLOCK_SIZE, encoding = 'shift-jis'),
                                       data = reader.read(metadata[3])))
                reader.seek(metadata[1] - (metadata[3] + metadata[0]), 1)
            return True
        except ValueError:
            return False
    
    def save(self):
        writer = binary.BinaryWriter()
        writer.writeU4(16)
        writer.writeU4(0)
        writer.write(LaytonPack.MAGIC[self._version])
        writer.writeU4(0)
        for fileChunk in self.files:
            header = binary.BinaryWriter()
            data = binary.BinaryWriter()
            data.writeString(fileChunk.name, 'shift-jis')
            data.align(4)
            header.writeU4(data.getLength() + LaytonPack.METADATA_BLOCK_SIZE)
            data.write(fileChunk.data)
            data.dsAlign(4, 4)
            header.writeU4(data.getLength() + LaytonPack.METADATA_BLOCK_SIZE)
            header.writeU4(0)
            header.writeU4(len(fileChunk.data))
            writer.write(header.data)
            writer.write(data.data)
        writer.insert(writer.getLength().to_bytes(4, byteorder = 'little'), 4)
        self.data = writer.data

class LaytonPack2(Archive):

    HEADER_BLOCK_SIZE = 32

    def __init__(self, name):
        Archive.__init__(self, name)
    
    def load(self, data):
        reader = binary.BinaryReader(data = data)
        if reader.read(4) == b'LPC2':
            countFile = reader.readU4()
            offsetFile = reader.readU4()
            _lengthArchive = reader.readU4()
            offsetMetadata = reader.readU4()
            offsetName = reader.readU4()
            
            for indexFile in range(countFile):
                reader.seek(offsetMetadata + (12 * indexFile))
                fileOffsetName = reader.readU4()
                fileOffsetData = reader.readU4()
                fileLengthData = reader.readU4()

                reader.seek(offsetName + fileOffsetName)
                tempName = reader.readNullTerminatedString('shift-jis')
                reader.seek(offsetFile + fileOffsetData)
                tempData = reader.read(fileLengthData)
                self.files.append(File(tempName, data=tempData))

            return True

        return False
    
    def save(self):
        metadata = binary.BinaryWriter()
        sectionName = binary.BinaryWriter()
        sectionData = binary.BinaryWriter()
        for fileIndex, fileChunk in enumerate(self.files):
            metadata.writeU4(sectionName.getLength())
            metadata.writeU4(sectionData.getLength())
            metadata.writeU4(len(fileChunk.data))

            sectionName.writeString(fileChunk.name, 'shift-jis')
            if fileIndex < len(self.files):
                sectionName.write(b'\x00')

            sectionData.write(fileChunk.data)
            sectionData.dsAlign(4, 4)

        sectionName.dsAlign(4, 4)
        
        writer = binary.BinaryWriter()
        writer.write(b'LPC2')
        writer.writeU4(len(self.files))
        writer.writeU4(LaytonPack2.HEADER_BLOCK_SIZE + metadata.getLength() + sectionName.getLength())
        writer.writeU4(0) # EOFC, not written until end
        writer.writeU4(LaytonPack2.HEADER_BLOCK_SIZE)
        writer.writeU4(LaytonPack2.HEADER_BLOCK_SIZE + metadata.getLength())
        writer.writeU4(LaytonPack2.HEADER_BLOCK_SIZE + metadata.getLength() + sectionName.getLength())
        writer.pad(LaytonPack2.HEADER_BLOCK_SIZE - writer.getLength())
        writer.write(metadata.data)
        writer.write(sectionName.data)
        writer.write(sectionData.data)
        writer.insert(writer.getLength().to_bytes(4, byteorder = 'little'), 12)

        self.data = writer.data

debug = File("akira", data = binary.BinaryReader(filename='akira_e_face.arc').data)
debug.decompressRle(offsetIn=4)
debug.compressRle()
debug.decompressRle()