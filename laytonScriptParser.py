# Professor Layton and the Curious Village Script Parser

import sys
from struct import unpack

class LAYTON_CONSTANTS():
    CURIOUS_VILLAGE = 0
    DIABOLICAL_BOX = 1
    UNWOUND_FUTURE = 2

class gdScript():
    def __init__(self, filename):
        
        self.filename = filename
        self.lengthPad = 0
        self.offsetEofc = 0
        self.typeGame = LAYTON_CONSTANTS.CURIOUS_VILLAGE
        self.commands = []
        
    def load(self):

        print("LD: Decoding GDScript...")
        
        if self.typeGame == LAYTON_CONSTANTS.CURIOUS_VILLAGE:
            self.lengthPad = 2
        try:
            
            with open(self.filename, 'rb') as laytonScript:

                self.offsetEofc = int.from_bytes(laytonScript.read(4), 'little')
                self.jumpPadding(laytonScript)

                while laytonScript.tell() != self.offsetEofc + 4:

                    self.commands.append(self.parseCommand(laytonScript))

            print("LD: Complete!")
            return True
            
        except FileNotFoundError:
            print("LD: GDS does not exist!")
            return False

    def parseCommand(self,reader):

        # ? is substituted by the selected language

        
        command = reader.read(1)
        reader.read(1)

        params = []
        while True:
            paramId = int.from_bytes(reader.read(2), 'little')
            if paramId == 0:
                break
            elif paramId == 1:
                params.append(int.from_bytes(reader.read(4), 'little'))
            elif paramId == 2:
                params.append(unpack("<f", reader.read(4))[0])
            elif paramId == 3:
                params.append(reader.read(int.from_bytes(reader.read(2), 'little')).decode("ascii")[0:-1])
                

            # Unk params
            elif paramId == 6:
                params.append(int.from_bytes(reader.read(4), 'little'))
            elif paramId == 7:
                params.append(int.from_bytes(reader.read(2), 'little'))
            elif paramId == 8:
                pass
            elif paramId == 9:
                pass
            elif paramId == 14:
                pass
            elif paramId == 18:
                pass

            
            elif reader.tell() == self.offsetEofc + 4:
                if paramId != 12:
                    print("End of file readed, bad command!")
                    print(paramId)
                    print(reader.tell())
            else:
                print("Unhandled command!")
                print(paramId)
                print(reader.tell())
                sys.exit()

        if command == b'\x0c':
            print("GD: [GRAPHICS] Draw TS image " + params[0])
        elif command == b'\x0b':
            print("GD: [GRAPHICS] Draw BS image " + params[0])
        elif command == b'\x0e':
            print("GD: [GRAPHICS] ?? Init stack")
        elif command == b'\x0f':
            print("GD: [GRAPHICS] ?? Fade in!")
        elif command == b'\x05':
            print("GD: [GRAPHICS] ?? Fade out!")
            
        elif command == b'\x6b':
            print("GD: [GRAPHICS] Pause for " + str(params[0]) + " frames (" + str(round(params[0]/60, 2)) + " seconds)")
        elif command == b'\x6c':
            print("GD: [GRAPHICS] Draw static image!")
        elif command == b'\x6d':
            print("GD: [GRAPHICS] Draw animated image!")

        elif command == b'\xc3':
            print("GD: [PUZZLE  ] Set puzzle " + str(params[0]) + " picarot decay!\nStage 0: " + str(params[1]) + "\nStage 1: " + str(params[2]) + "\nStage 2: " + str(params[3]))            

        # General puzzle commands
        elif command == b'\x1b':
            print("GD: [PUZZLE  ] Set puzzle applet!\n               Handler: " + params[0])
        elif command == b'\x1f':
            print("GD: [PUZZLE  ] Set internal puzzle reference!\n               ID     : " + str(params[0]))
            if params[1] != 0:
                print("               Inconsistent secondary index!")
        elif command == b'\x1c':
            if params[0] == 3:
                print("GD: [PUZZLE  ] 0x1C Constant 3")
            else:
                print("GD: [PUZZLE  ] UNK 0x1C")

        # Drag puzzle mode                    
        elif command == b'\x38':
            print("GD: [PUZZLE  ] Set answer region!")
  
        elif command == b'\xba':
            print("GD: [PUZZLE  ] Set puzzle title!\n               ID     : " + str(params[0]) + "\n               Name   : " + params[1])


        # Matchstick puzzle mode - Finished
        elif command == b'\x27':
            print("GD: [PUZZLE  ] Set move limit to " + str(params[0]))
        elif command == b'\x2a':
            print("GD: [PUZZLE  ] Place match!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")" + "\n               Rotation: " + str(params[2]) + " degrees")
        elif command == b'\x2b':
            print("GD: [PUZZLE  ] Set match answer region!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")" + "\n               Rotation: " + str(params[2]) + " degrees")
            
            
        # DrawInput puzzle mode - Finish
        elif command == b'\xfb':
            if type(params[0]) == type(int()):
                print("GD: [PUZZLE  ] Set HL puzzle answer index " + str(params[0]) + " to " + str(params[1]))
            else:
                print("GD: [PUZZLE  ] Set HL puzzle answer to " + str(params[0]))
                if params[1] != 0:
                    print("               Inconsistent secondary index!")
        elif command == b'\xfc':
            print("GD: [PUZZLE  ] Change answer box to alternative image " + params[0])
          

        # On Off puzzle mode - ? 
        elif command == b'\x5d':
            print("GD: [PUZZLE  ] Draw interactable sprite " + params[2] + ["", ", solution"][params[3]] + "\n               SpawnFr: " + str(params[4]))  

        # Tile puzzle mode - Finished
        elif command == b'\x73':
            print("GD: [PUZZLE  ] Place moveable tile!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")\n               Sprite  : " + params[2] + "\n               SpwAnim : " + str(params[3]))
        elif command == b'\x74':
            print("GD: [PUZZLE  ] Set tile target!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")
        elif command == b'\x75':
            print("GD: [PUZZLE  ] Map tile to target!\n               Map     : " + str(params[0]) + " -> " + str(params[1]))
        elif command == b'\x76':
            print("GD: [PUZZLE  ] Set amount of valid solutions!")
        
        # Cup puzzle mode - Finished
        elif command == b'\x3a':
            print("GD: [PUZZLE  ] Place cup!\n               Sprite  : " + params[0] + "\n               Location: (" + str(params[1]) + ", " + str(params[2]) + ")\n               SpwAnim : " + str(params[3]) + "\n               Capacity: " + str(params[4]) + "\n               Target  : " + str(params[5]))
        
        elif command == b'\x10':
            print("GD: [AUDIO   ] Play SWAV " + str(params[0]))
        else:
            print("--  Unimplemented command: " + str(command))
        
        return [command, params]

    def jumpPadding(self, reader):
        reader.seek(self.lengthPad, 1)
