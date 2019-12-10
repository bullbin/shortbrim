# All little-endian

from struct import unpack, pack

class BinaryReader():
    def __init__(self, filename='', data=b''):
        if filename != '':
            try:
                with open(filename, 'rb') as dataIn:
                    self.data = bytearray(dataIn.read())
            except FileNotFoundError:
                print("Path", filename, "doesn't exist!")
                self.data = bytearray(data)
            except IOError:
                self.data = bytearray(data)
        else:
            self.data = bytearray(data)

        self.pos = 0

    def seek(self, newPos, mode=0):
        if mode == 0:
            self.pos = newPos
        elif mode == 1:
            self.pos += newPos
        else:
            self.pos = len(self.data) - newPos - 1

    def hasDataRemaining(self):
        if self.tell() <= len(self.data) - 1:
            return True
        return False

    def tell(self):
        return self.pos

    def read(self, length):
        self.pos += length
        return self.data[self.pos - length:self.pos]

    def readFloat(self, length):
        return unpack("<f", self.read(length))[0]

    def readF4(self):
        return self.readFloat(4)

    def readUInt(self, length):
        return int.from_bytes(self.read(length), byteorder = 'little')

    def readU2(self):
        return self.readUInt(2)

    def readU4(self):
        return self.readUInt(4)
    
    def readU4List(self, length):
        out = []
        for _index in range(length):
            out.append(self.readU4())
        return out

    def readU8(self):
        return int.from_bytes(self.read(8), byteorder = 'little')
    
    def readS2(self):
        return int.from_bytes(self.read(2), byteorder = 'little', signed = True)

    def readS4(self):
        return int.from_bytes(self.read(4), byteorder = 'little', signed = True)
    
    def readS8(self):
        return int.from_bytes(self.read(8), byteorder = 'little', signed = True)
    
    def readNullTerminatedString(self, encoding):
        out = bytearray(b'')
        while self.data[self.pos] != 0:
            out.extend(self.read(1))
        return out.decode(encoding)
    
    def readPaddedString(self, length, encoding, padChar=b'\x00'):
        out = self.read(length).split(padChar)
        return out[0].decode(encoding)

class BinaryWriter():
    def __init__(self):
        self.data = bytearray(b'')
    
    def getLength(self):
        return len(self.data)

    def pad(self, padLength, padChar = b'\x00'):
        for _index in range(padLength):
            self.data.extend(padChar)

    def align(self, alignment, padChar = b'\x00'):
        while self.getLength() % alignment > 0:
            self.data.extend(padChar)

    def dsAlign(self, alignment, extraPad, padChar = b'\x00'):
        tempAlignmentLength = self.getLength()
        self.align(alignment, padChar = padChar)
        if self.getLength() == tempAlignmentLength:
            self.pad(extraPad, padChar = padChar)

    def write(self, data):
        self.data.extend(data)
    
    def writeFloat(self, data):
        self.data.extend(pack("<f", data))

    def writeString(self, data, encoding):
        self.data.extend(data.encode(encoding))

    def writeInt(self, data, length, signed = False):
        self.data.extend(data.to_bytes(length, byteorder = 'little', signed = signed))
    
    def writeIntList(self, dataList, length, signed = False):
        for data in dataList:
            self.writeInt(data, length, signed = signed)

    def writeLengthAndString(self, data, encoding, lengthSize=2, extraPadLength=1, padChar=b'\x00'):
        tempString = data.encode(encoding)
        self.writeInt(len(tempString) + extraPadLength, lengthSize)
        self.data.extend(tempString)
        self.pad(extraPadLength, padChar=padChar)

    def writeU2(self, data):
        self.writeInt(data, 2)

    def writeU4(self, data):
        self.writeInt(data, 4)
    
    def writeU8(self, data):
        self.writeInt(data, 8)

    def writeS4(self, data):
        self.writeInt(data, 4, signed=True)
    
    def writeU4L(self, dataList):
        self.writeIntList(dataList, 4)
    
    def insert(self, data, pos):
        insertionPos = pos
        for singleByte in data:
            self.data[insertionPos] = singleByte
            insertionPos += 1