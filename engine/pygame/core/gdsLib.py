# Professor Layton and the Curious Village Script Parser

from struct import unpack

class gdOperation():
    def __init__(self, opcode, operands):
        self.opcode = opcode
        self.operands = operands

class gdScript():
    def __init__(self, filename):
        self.commands = []
        self.load(filename)
    def load(self, filename):
        try:
            with open(filename, 'rb') as laytonScript:
                self.offsetEofc = int.from_bytes(laytonScript.read(4), 'little')
                laytonScript.seek(2,1)
                while laytonScript.tell() != self.offsetEofc + 4:
                    self.commands.append(self.parseCommand(laytonScript))
            print("[GDLIB] Reading complete!")
        except FileNotFoundError:
            print("[GDLIB] GDS does not exist!")
    def parseCommand(self, reader):
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
            elif paramId == 6:
                tempOperands.append(int.from_bytes(reader.read(4), 'little'))
            elif paramId == 7:
                tempOperands.append(int.from_bytes(reader.read(4), 'little'))
            
            elif paramId == 12: # End of entire file
                break
            
        return gdOperation(opcode, tempOperands)
