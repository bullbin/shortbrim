# Professor Layton and the Curious Village Script Parser

from struct import unpack

commandsVerified = [b'\x0b', b'\x0c',
                    b'\x1b', b'\x1c', b'\x1f',
                    b'\x25', b'\x26', b'\x27', b'\x2a', b'\x2b', b'\x2d',
                    b'\x31', b'\x32', b'\x38', b'\x39', b'\x3a', b'\x3b', b'\x3c', b'\x3d', b'\x3e', b'\x3f',
                    b'\x48',
                    b'\x51', b'\x53', b'\x5c', b'\x5d', b'\x5e',
                    b'\x6c', b'\x6d',
                    b'\x73', b'\x74', b'\x75', b'\x76',
                    b'\x8a', b'\x8b',
                    b'\x9c', b'\x9d',
                    b'\xa0', b'\xa1', b'\xa6',
                    b'\xba', b'\xb6',
                    b'\xc3',
                    b'\xd3', b'\xd4', b'\xdc',
                    
                    b'\xfa', b'\xfb', b'\xfc', b'\xfd']

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
                    tempStatus, tempCommand = self.parseCommand(laytonScript)
                    if tempStatus:
                        self.commands.append(tempCommand)
                    elif tempCommand == None:
                        print("[ERROR] Failed while reading GDS!")
                        break
                    else:           # Unused but can be useful when debugging
                        pass
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

            # Unk
            elif paramId == 8:
                pass
            elif paramId == 9:
                pass
            
            elif paramId == 12: # End of entire file
                break
            else:
                print("[ERROR] Failed to obtain operands.")
                print(paramId)
                return (False, None)
            
        # if opcode in commandsVerified:
        #     return (True, gdOperation(opcode, tempOperands))
        # return (False, False)
        return (True, gdOperation(opcode, tempOperands))
