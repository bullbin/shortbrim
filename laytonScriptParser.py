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

        # '#?' is substituted by the selected language

        command = reader.read(1)
        reader.read(1)

        params = []
        while True:
            paramId = int.from_bytes(reader.read(2), 'little')
            if paramId == 0:
                break
            elif paramId == 1:
                params.append(int.from_bytes(reader.read(4), 'little', signed = True))
            elif paramId == 2:
                params.append(unpack("<f", reader.read(4))[0])
            elif paramId == 3:
                params.append(reader.read(int.from_bytes(reader.read(2), 'little')).decode("ascii")[0:-1])

            # Unk params
            elif paramId == 6:
                params.append(int.from_bytes(reader.read(4), 'little'))
            elif paramId == 7:
                params.append(int.from_bytes(reader.read(4), 'little'))
            elif paramId == 8:
                pass
            elif paramId == 9:
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

        elif command == b'\x10':
            # After testing, this command is audio related, but changing the value causes the audio to not be played
            # This could maybe be an offset for the sound bank or something - there is invalidation checking
            print("GD: [AUDIO   ] ?? Play SWAV " + str(params[0]))

        # General puzzle commands
        elif command == b'\x1b':
            print("GD: [PUZZLE  ] Set puzzle applet!\n               Handler : " + params[0])
        elif command == b'\x1c':
            print("GD: [PUZZLE  ] ?? Set hint count!\n               Hints   : " + str(params[0]))
        elif command == b'\x1f':
            print("GD: [PUZZLE  ] Set internal puzzle reference!\n               ID      : " + str(params[0]))
            if params[1] != 0:
                print("               Inconsistent secondary index!")

        # Coin puzzle mode - Finished
        elif command == b'\x25':
            print("GD: [PUZZLE  ] Place coin!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")
        elif command == b'\x26':
            print("GD: [PUZZLE  ] Set coin target!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")
        
        elif command == b'\x27':
            print("GD: [PUZZLE  ] Set move limit to " + str(params[0]))

        # Matchstick puzzle mode - Finished
        elif command == b'\x2a':
            print("GD: [PUZZLE  ] Place match!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")" + "\n               Rotation: " + str(params[2]) + " degrees")
        elif command == b'\x2b':
            print("GD: [PUZZLE  ] Set match answer region!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")" + "\n               Rotation: " + str(params[2]) + " degrees")

        # Scale puzzle mode
        elif command == b'\x2d':
            print("GD: [PUZZLE  ] Set weight quantity!\n               CntWght : " + str(params[0]))

        # Connect puzzle mode - Finished
        elif command == b'\x31':
            print("GD: [PUZZLE  ] Place chick!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")
        elif command == b'\x32':
            print("GD: [PUZZLE  ] Place wolf!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")

        # Drag puzzle mode                    
        elif command == b'\x38':
            print("GD: [PUZZLE  ] Set answer location!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")
        elif command == b'\x39':
            print("GD: [PUZZLE  ] Set target rotation!\n               Rotation: " + str(params[0]) + " degrees")

        # Cup puzzle mode - Finished
        elif command == b'\x3a':
            print("GD: [PUZZLE  ] Place cup!\n               Sprite  : " + params[0] + "\n               Location: (" + str(params[1]) + ", " + str(params[2]) + ")\n               SpwAnim : " + str(params[3]) + "\n               Capacity: " + str(params[4]) + "\n               Target  : " + str(params[5]))

        # Queens puzzle mode
        elif command == b'\x3b':
            print("GD: [PUZZLE  ] Set board parameters!\n               tlCorner: (" + str(params[0]) + ", " + str(params[1]) + ")\n               BoardSze: " + str(params[2]))
        elif command == b'\x3c':
            print("GD: [PUZZLE  ] Set piece quantity!\n               CntQueen: " + str(params[0]))
        elif command == b'\x3d':
            print("GD: [PUZZLE  ] Set pre-placed piece!\n               BoardLoc: (" + str(params[0]) + ", " + str(params[1]) + ")")
        elif command == b'\x3e':
            print("GD: [PUZZLE  ] Set chess board solving method!\n               Cndition: " + ["No intersections", "No remaining useable board space"][params[0]])
        
        # Trace Button mode
        elif command == b'\x3f':
            print("GD: [PUZZLE  ] Set trace answer location!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")

        elif command == b'\x48':
            print("GD: [EVENT   ] Select puzzle " + str(params[0]) + "!")

        elif command == b'\x50':
            print("GD: [EVENT   ] Place object!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")\n               Bounding: (" + str(params[2]) + ", " + str(params[3]) + ")\n               ObjIndex: " + str(params[4]) + "\n               EvtIndex: " + str(params[5]))
            if len(params) > 6:
                for param in params[5:]:
                    print(param)

        elif command == b'\x51':
            print("GD: [STATE   ] ?? Set environment type: " + params[0])
        elif command == b'\x53':
            # Carried from reversing notes - untested
            print("GD: [STATE   ] ?? Set room index " + str(params[0]))
        elif command == b'\x5c':
            print("GD: [GRAPHICS] Draw animated sprite!\n               Name   : " + params[2] + "\n               Loc    : (" + str(params[0]) + ", " + str(params[1]) + ")")
        
        # On Off puzzle mode - ? 
        elif command == b'\x5d':
            print("GD: [PUZZLE  ] Draw interactable sprite " + params[2] + ["", ", solution"][params[3]] + "\n               SpawnFrm: " + str(params[4]))  

        # Place Target mode
        elif command == b'\x5e':
            print("GD: [PUZZLE  ] Set sprite target!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")\n               Sprite  : " + params[2] + "\n               Radius  : " + str(params[3]) + "\n               Unknown : " + str(params[4]))
        
        elif command == b'\x6b':
            print("GD: [GRAPHICS] Pause for " + str(params[0]) + " frames (" + str(round(params[0]/60, 2)) + " seconds)")
        elif command == b'\x6c':
            print("GD: [GRAPHICS] Draw static image!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")\n               Sprite  : " + params[2] + "\n               SpwnAnim: " + params[3])
        elif command == b'\x6d':
            print("GD: [GRAPHICS] Draw animated image!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")\n               Sprite  : " + params[2] + "\n               SpwnAnim: " + params[3] + "\n               SpawnFrm: " + str(params[4]))

        # Event-related stuff (untested)
        elif command == b'\x6e':
            if len(params) == 2:
                print("GD: [EVENT   ] ?? Set anim for character " + str(params[0]) + ": " + params[1])
            else:
                print("GD: [EVENT   ] ??")
        elif command == b'\x6f':
            if len(params) == 2:
                print("GD: [EVENT   ] ?? Set alt anim for character " + str(params[0]) + ": " + params[1])
            else:
                print("GD: [EVENT   ] ??")
          
        # Tile puzzle mode - Finished
        elif command == b'\x73':
            print("GD: [PUZZLE  ] Place moveable tile!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")\n               Sprite  : " + params[2] + "\n               SpwnAnim : " + str(params[3]))
        elif command == b'\x74':
            print("GD: [PUZZLE  ] Set tile target!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")
        elif command == b'\x75':
            print("GD: [PUZZLE  ] Map tile to target!\n               Map     : " + str(params[0]) + " -> " + str(params[1]))
        elif command == b'\x76':
            print("GD: [PUZZLE  ] Set amount of valid solutions!\n               Max     : " + str(params[0]))

        # River Cross 2 mode
        elif command == b'\x8a':
            print("GD: [PUZZLE  ] Place cabbage!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")
        elif command == b'\x8b':
            print("GD: [PUZZLE  ] Place sheep!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")


        # More event-related codes

        elif command == b'\x8e':
            print("GD: [EVENT   ] ?? Reference event script!\n               ID      : " + str(params[0]))
            for param in params[1:]:
                    print("               Unknown : " + str(param))
    
        elif command == b'\x9c':
            print("GD: [EVENT   ] Select right character event script!\n               TextIndx: " + str(params[0]) + "\n               ChrIndex: " + str(params[1]))
            if len(params) > 2: 
                for param in params[2:]:
                    print("               Unknown : " + str(param))
        elif command == b'\x9d':
            print("GD: [EVENT   ] Select left character event script!\n               TextIndx: " + str(params[0]) + "\n               ChrIndex: " + str(params[1]))
            if len(params) > 2: 
                for param in params[2:]:
                    print("               Unknown : " + str(param))      




        
        # Cut Puzzle mode
        elif command == b'\xa0':
            print("GD: [PUZZLE  ] Define cut node!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")
        elif command == b'\xa1':
            print("GD: [PUZZLE  ] Define node connection!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")" + " to (" + str(params[2]) + ", " + str(params[3]) + ")")

        # Slide puzzles use a range of commands from a4 to aa
        elif command == b'\xa6':
            if params[2] < 4:
                print("GD: [PUZZLE  ] Draw sliding component! (slidepuzzle.arc)\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")
                print("               CompType: " + str(params[2]) + ", " + {0:"Horizontal", 1:"Vertical", 2:"Boundary", 3:"Solution"}[params[2]] + "\n               SpawnAnm: " + params[3])
            else:
                print("GD: [PUZZLE  ] Draw sliding component! (slidepuzzle2.arc)\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")
                print("               CompType: " + str(params[2]) + ", " + {4:"External asset"}[params[2]] + "\n               SpawnAnm: " + params[3])

        elif command == b'\xba':
            print("GD: [PUZZLE  ] Set puzzle title!\n               ID     : " + str(params[0]) + "\n               Name   : " + params[1])
        
        elif command == b'\xb6':
            print("GD: [DEBUG   ] " + params[1] + "\t: " + params[0])

        elif command == b'\xc3':
            print("GD: [PUZZLE  ] Set puzzle " + str(params[0]) + " picarot decay!\nStage 0: " + str(params[1]) + "\nStage 1: " + str(params[2]) + "\nStage 2: " + str(params[3]))

        elif command == b'\xd3':
            print("GD: [VIDEO   ] Play MODS " + str(params[0]))
        elif command == b'\xd4':
            print("GD: [PUZZLE  ] Set interactable region!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")\n               Radius  : " + str(params[2]) + "\n               IsAnswer: " + str(params[3]))
        elif command == b'\xdc':
            print("GD: [PUZZLE  ] Add puzzle DB entry!\n               ID     : " + str(params[0]) + "\n               Type   : " + str(params[1]) + "\n               Loc    : " + str(params[2]))
            
        # DrawInput puzzle mode - Finish
        elif command == b'\xfa':
            print("GD: [PUZZLE  ] Set character recognition box!\n               AnsIndex: " + str(params[0]) + "\n               Location: (" + str(params[1]) + ", " + str(params[2]) + ")\n               BoxLen  : " + str(params[3]))
        elif command == b'\xfb':
            print("GD: [PUZZLE  ] Set HL puzzle answer!\n               AnsIndex: " + str(params[0]) + "\n               Answer  : " + str(params[1]))
        elif command == b'\xfc':
            print("GD: [PUZZLE  ] Change answer box to alternative image " + params[0])
        elif command == b'\xfd':
            print("GD: [VIDEO   ] Display subtitle!\n               File   : " + self.filename.split("\\")[-1][0:-4] + "_" + str(params[0]) + ".txt\n               Start  : " + str(params[1]) + "\n               Length : " + str(params[2]))
        
        else:
            print("--  Unimplemented command: " + str(command))
            for param in params:
                print("\t" + str(param))
        
        return [command, params]

    def jumpPadding(self, reader):
        reader.seek(self.lengthPad, 1)

