# Professor Layton and the Curious Village Script Parser

from struct import unpack
from os import path

class gdOperation():
    def __init__(self, opcode, operands):
        self.opcode = opcode
        self.operands = operands

class gdScript():
    def __init__(self, playerState, filename):
        self.commands = []
        self.commandLoc = []
        self.length = 0
        self.playerState = playerState
        self.load(filename)
    def load(self, filename):
        try:
            self.length = path.getsize(filename)
            with open(filename, 'rb') as laytonScript:
                self.offsetEofc = int.from_bytes(laytonScript.read(4), 'little')
                laytonScript.seek(2,1)
                while laytonScript.tell() != self.offsetEofc + 4:
                    self.commands.append(self.parseCommand(laytonScript))
            print("[GDLIB] Reading complete!")
        except FileNotFoundError:
            print("[GDLIB] Err: GDS does not exist!")

    def resolveJumps(self):
        for command in self.commands:
            pass
            
    def parseCommand(self, reader):
        self.commandLoc.append(reader.tell())
        opcode = reader.read(1)
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
                if tempOperands[-1] > self.length:
                    print("[GDLIB] Err: Seek location out of bounds")
                    tempOperands[-1] == self.length - 2 # Set to location of break command
            
            elif paramId == 12: # End of entire file
                break
        
        if opcode == b'\x17':
            print("[GDLIB] Jump from " + str(reader.tell()) + " to " + str(tempOperands[0]))
            reader.seek(tempOperands[0])
            
        return gdOperation(opcode, tempOperands)