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
    def __init__(self, data, playerState, enableBranching=False, useBranchingHack=True):
        self.commands = []
        self.commandLoc = []
        self.length = 0
        self.contextPuzzle = None
        self.playerState = playerState
        self.load(binary.BinaryReader(data = data), enableBranching, useBranchingHack)
    def load(self, data, enableBranching, useBranchingHack):
        try:
            self.length = len(data.data)
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
        
        if enableBranching:
            if opcode == b'\x48':  # Select puzzle
                self.contextPuzzle = tempOperands[0]
            
            if self.contextPuzzle != None:
                if opcode in [b'\x49', b'\x4a', b'\x4d']:
                    if opcode == b'\x49' and self.playerState.puzzleData[self.contextPuzzle].countAttempts > 0: # Jump if puzzle reattempted
                        reader.seek(tempOperands[0])
                    elif opcode == b'\x4a' and self.playerState.puzzleData[self.contextPuzzle].wasCompleted: # Jump if puzzle finished
                        reader.seek(tempOperands[0])
                    elif opcode == b'\x4d' and self.playerState.puzzleData[self.contextPuzzle].wasQuit: # Jump if puzzle quit
                        reader.seek(tempOperands[0])
                    if useBranchingHack:                # The RE for branching is kind of shaky, so this hack allows more bad loops to be avoided
                        seekToNextOperation(reader)
                    invalidateCommand = True
            
        return (invalidateCommand, gdOperation(opcode, tempOperands))