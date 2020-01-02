# Professor Layton and the Curious Village Script Parser

from struct import unpack
from os import path
from hat_io import binary, asset
import conf

def debugPrint(line):   # Function needs to be moved from coreState to avoid cyclical dependency
    if conf.ENGINE_DEBUG_MODE:
        print(line)

def seekToNextOperation(reader):
    reader.read(2)
    while True:
        paramId = int.from_bytes(reader.read(2), 'little')
        if paramId == 0 or paramId == 12:    # End of command
            break
        elif paramId in [1,2,6,7]:
            int.from_bytes(reader.read(4), 'little', signed = True)
        elif paramId == 3:
            reader.read(int.from_bytes(reader.read(2), 'little'))

class gdOperation():
    def __init__(self, opcode, operands):
        self.opcode = opcode
        self.operands = operands

class gdScript(asset.File):
    def __init__(self):
        self.commands = []
        self.commandLoc = []
        self.length = 0
    
    @staticmethod
    def fromData(data):
        output = gdScript()
        output.load(data, False, False)
        return output

    def load(self, data, enableBranching, useBranchingHack):
        try:
            data = binary.BinaryReader(data=data)
            self.length = len(data.data)
            if self.length > 0: # TODO - Why is this crashing so hard on 0 lengths?
                if enableBranching:
                    self.lastJump = 0
                self.offsetEofc = data.readU4()
                data.seek(2,1)
                while data.tell() != self.offsetEofc + 4:
                    tempCommand = self.parseCommand(data, enableBranching, useBranchingHack)
                    if not(tempCommand[0]):
                        self.commands.append(tempCommand[1])
                debugPrint("LogGdsLoad: Reading complete!")
        except FileNotFoundError:
            debugPrint("ErrGdsLoad: GDS does not exist!")

    def parseCommand(self, reader, enableBranching, useBranchingHack):
        self.commandLoc.append(reader.tell())
        invalidateCommand = False
        opcode = bytes(reader.read(1))
        reader.seek(1,1)
        tempOperands = []
        while True:
            paramId = int.from_bytes(reader.read(2), 'little')
            if paramId == 0:    # End of command
                break
            elif paramId == 1:
                tempOperands.append(int.from_bytes(reader.read(4), 'little', signed = True))
            elif paramId == 2:
                tempOperands.append(unpack("<f", reader.read(4))[0])
            elif paramId == 3:
                tempOperands.append(reader.read(int.from_bytes(reader.read(2), 'little')).decode("ascii")[0:-1])

            # Flow
            elif paramId == 6 or paramId == 7:
                tempOperands.append(int.from_bytes(reader.read(4), 'little') + 6)
                if tempOperands[-1] >= self.length:
                    debugPrint("ErrGdsParseFatal: Seek location out of bounds")
                    tempOperands[-1] == self.length - 2 # Set to location of break command
                else:
                    previousLength = reader.tell()
                    reader.seek(tempOperands[-1] - 2)
                    if int.from_bytes(reader.read(2), byteorder = 'little') != 0:        # Resolve if using direct addressing
                        tempOperands[-1] = int.from_bytes(reader.read(4), 'little') + 6
                    reader.seek(previousLength)
            
            elif paramId == 12: # End of entire file
                break
            
        return (invalidateCommand, gdOperation(opcode, tempOperands))