# Professor Layton and the Curious Village Script Parser

import sys
from struct import unpack
from os import path

class LAYTON_CONSTANTS():
    CURIOUS_VILLAGE = 0
    DIABOLICAL_BOX = 1
    UNWOUND_FUTURE = 2

class gdScript():
    def __init__(self, filename):
        
        self.filename = filename
        self.lengthPad = 0
        self.length = 0
        self.offsetEofc = 0
        self.typeGame = LAYTON_CONSTANTS.CURIOUS_VILLAGE
        self.commands = []
        
    def load(self):

        print("LD: Decoding GDScript...")
        
        if self.typeGame == LAYTON_CONSTANTS.CURIOUS_VILLAGE:
            self.lengthPad = 2
        try:
            self.length = path.getsize(self.filename)

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

        commandLoc = reader.tell()
        print("\n" + str(commandLoc))
        command = reader.read(1)
        reader.read(1)

        params = []
        paramsType = {}
        while True:
            paramId = int.from_bytes(reader.read(2), 'little')
            if len(params) in paramsType.keys():
                paramsType[len(params)].append(paramId)
            else:
                paramsType[len(params)] = [paramId]
            
            if paramId == 0:
                break
            elif paramId == 1:
                params.append(int.from_bytes(reader.read(4), 'little', signed = True))
            elif paramId == 2:
                params.append(unpack("<f", reader.read(4))[0])
            elif paramId == 3:
                params.append(reader.read(int.from_bytes(reader.read(2), 'little')).decode("ascii")[0:-1])
                
            elif paramId == 4 or paramId == 5:
                print("ERROR READING: UNK PARAM!")

            # Control parameters (conditional jumping?)
            elif paramId == 6 or paramId == 7:
                params.append(int.from_bytes(reader.read(4), 'little') + 6)
                if params[-1] < self.length:
                    previousLength = reader.tell()
                    reader.seek(params[-1] - 2)
                    if int.from_bytes(reader.read(2), byteorder = 'little') != 0:   # Resolve if using direct addressing
                        params[-1] = int.from_bytes(reader.read(4), 'little') + 6
                    reader.seek(previousLength)

            # Unk parameters
            elif paramId in [8,9]:
                pass
            
            elif reader.tell() == self.offsetEofc + 4:
                if paramId != 12:
                    print("Reached EOFC late!")
                    break
            else:
                print("Unhandled parameter " + str(paramId) + "@" + str(reader.tell()))
                sys.exit()
        
        if command == b'\x06' and len(params) == 0:
            print("GD: [FLOW    ] ?? End execution after next instruction!")

        elif command == b'\x0b':
            print("GD: [GRAPHICS] Draw BS image " + params[0])
        elif command == b'\x0c':
            print("GD: [GRAPHICS] Draw TS image " + params[0])

        elif command == b'\x10':
            # After testing, this command is audio related, but changing the value causes the audio to not be played
            # This could maybe be an offset for the sound bank or something - there is invalidation checking
            print("GD: [AUDIO   ] ?? Play SWAV " + str(params[0]))

        elif command == b'\x17':
            print("GD: [FLOW    ] ?? Jump to " + str(params[0]))

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
            print("GD: [PUZZLE  ] Set match answer region!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")" + "\n               Rotation: " + str(params[2]) + " degrees\n               Region  : (" + str(params[3]) + ", " + str(params[4]) + ")" )

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
        elif command == b'\x42':
            print("GD: [PUZZLE  ] Set trace cursor colour!\n               RGB     : (" + str(params[0]) + ", " + str(params[1]) + ", " + str(params[2]) + ")")
                  
        elif command == b'\x43':
            print("GD: [EVENT   ] Set tobj text region!\n               ChrIndex: " + str(params[0]) + "\n               Location: (" + str(params[1]) + ", " + str(params[2]) + ")\n               Region  : (" + str(params[3]) + ", " + str(params[4]) + ")\n               TxtIndex: " + str(params[5]) + "\n               Unknown : " + str(params[6]))
        
        elif command == b'\x48':
            print("GD: [EVENT   ] Select puzzle " + str(params[0]) + "!")
        elif command == b'\x49':
            print("GD: [FLOW    ] ?? Jump if puzzle reattempted to next instruction after " + str(params[0]) + "!")
        
        elif command == b'\x4a':
            print("GD: [FLOW    ] ?? Jump if puzzle finished to next instruction after " + str(params[0]) + "!")

        elif command == b'\x4d':
            print("GD: [FLOW    ] ?? Jump if puzzle quit to next instruction after " + str(params[0]) + "!")

        elif command == b'\x50':
            print("GD: [EVENT   ] Place object!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")\n               Bounding: (" + str(params[2]) + ", " + str(params[3]) + ")\n               ObjIndex: " + str(params[4]) + "\n               EvtIndex: " + str(params[5]))
            if len(params) > 6:
                for param in params[5:]:
                    print(param)

        elif command == b'\x51':
            print("GD: [STATE   ] ?? Set environment type: " + params[0])
        elif command == b'\x52':
            print("GD: [STATE   ] ?? Hold environment type: " + params[0])
        elif command == b'\x53':
            # Carried from reversing notes - untested
            print("GD: [STATE   ] ?? Set room index " + str(params[0]))

        elif command == b'\x58':
            if len(params) == 1:
                print("GD: [EVENT   ] ?? Jump if completed!\n               Unknown : " + str(params[0]))
            else:
                print("GD: [EVENT   ] ?? Jump if completed!\n               Unknown : " + str(params[0]) + "\n               DestIndx: " + str(params[1]))
        
        elif command == b'\x5c':
            print("GD: [GRAPHICS] Draw animated sprite!\n               Name    : " + params[2] + "\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")
        
        # On Off puzzle mode - ? 
        elif command == b'\x5d':
            print("GD: [PUZZLE  ] Draw interactable sprite " + params[2] + ["", ", solution"][params[3]] + "\n               SpawnFrm: " + str(params[4]))  

        # Place Target mode
        elif command == b'\x5e':
            print("GD: [PUZZLE  ] Set sprite target!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")\n               Sprite  : " + params[2] + "\n               Radius  : " + str(params[3]) + "\n               Unknown : " + str(params[4]))

        elif command == b'\x63' and len(params) == 2:
            print("GD: [EVENT   ] ?? Branch if room visited!\n               RoomIndx: " + str(params[0]) + "\n               BrnchDes: " + str(params[1]))
        elif command == b'\x68':
            print("GD: [EVENT   ] Spawn hint coin!\n               Unknown : " + str(params[0]) + "\n               Location: (" + str(params[1]) + ", " + str(params[2]) + ")\n               Bounding: (" + str(params[3]) + ", " + str(params[4]) + ")\n               Unknown : " + str(params[5]))    
        
        elif command == b'\x6b':
            print("GD: [GRAPHICS] Pause for " + str(params[0]) + " frames (" + str(round(params[0]/60, 2)) + " seconds)")
        elif command == b'\x6c':
            print("GD: [GRAPHICS] Draw static image!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")\n               Sprite  : " + params[2] + "\n               SpwnAnim: " + params[3])
        elif command == b'\x6d':
            print("GD: [GRAPHICS] Draw animated image!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")\n               Sprite  : " + params[2] + "\n               SpwnAnim: " + params[3] + "\n               SpawnFrm: " + str(params[4]))

        # Event-related stuff (untested)
        elif command == b'\x6e':
            if len(params) == 2:
                print("GD: [EVENT   ] ?? Set body anim for character " + str(params[0]) + ": " + params[1])
            else:
                print("GD: [EVENT   ] ??")
        elif command == b'\x6f':
            if len(params) == 2:
                print("GD: [EVENT   ] ?? Set mouth anim for character " + str(params[0]) + ": " + params[1])
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

        # b'\x78', b'\x79' appear to be event character-related
        
        elif command == b'\x7e':
            print("GD: [GRAPHICS] Draw TS animated image!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")\n               Sprite  : " + params[2] + "\n               SpwnAnim: " + params[3])
            for param in params[4:]:
                print(param)
        
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
        
        #elif command == b'\x98':
        #    print("GD: [EVENT   ] ?? Select character puzzle start script!")
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

        # Slide Puzzle mode
        elif command == b'\xa3':
            print("GD: [PUZZLE  ] Set board TL corner!\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")
        elif command == b'\xa4':
            print("GD: [PUZZLE  ] Set board dimensions as " + str(params[0]) + " by " + str(params[1]) + " tiles!")
        elif command == b'\xa5':
            print("GD: [PUZZLE  ] Set puzzle tile width as " + str(params[0]) + " px!")
        elif command == b'\xa6':
            if params[2] < 4:
                print("GD: [PUZZLE  ] Draw sliding component! (slidepuzzle.arc)\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")
                print("               CompType: " + str(params[2]) + ", " + {0:"Horizontal", 1:"Vertical", 2:"Boundary", 3:"Solution"}[params[2]] + "\n               SpawnAnm: " + params[3])
            else:
                print("GD: [PUZZLE  ] Draw sliding component! (slidepuzzle2.arc)\n               Location: (" + str(params[0]) + ", " + str(params[1]) + ")")
                print("               CompType: " + str(params[2]) + ", " + {4:"External asset"}[params[2]] + "\n               SpawnAnm: " + params[3])

        elif command == b'\xac':
            print("GD: [PUZZLE  ] Set line drawn colour!\n               RGB     : (" + str(params[0]) + ", " + str(params[1]) + ", " + str(params[2]) + ")")
        elif command == b'\xad':
            print("GD: [PUZZLE  ] Set line guide colour!\n               RGB     : (" + str(params[0]) + ", " + str(params[1]) + ", " + str(params[2]) + ")")
        
        elif command == b'\xb1':
            print("GD: [PUZZLE  ] Set sliding puzzle parameters!\n               SolLoc  : (" + str(params[0]) + ", " + str(params[1]) + ")\n               Unknown : " + str(params[2]))

        elif command == b'\xb4':
            print("GD: [GRAPHICS] ?? Set horizontal mirroring parameter!\n               SpriteId: " + str(params[0]) + "\n               IsMirror: " + params[1])

        elif command == b'\xb6':
            print("GD: [DEBUG   ] " + params[1] + "\t: " + params[0])
        elif command == b'\xba':
            print("GD: [PUZZLE  ] Set puzzle title!\n               ID     : " + str(params[0]) + "\n               Name   : " + params[1])

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

        # Video playback
        elif command == b'\xfd':
            print("GD: [VIDEO   ] Display subtitle!\n               File   : " + self.filename.split("\\")[-1][0:-4] + "_" + str(params[0]) + ".txt\n               Start  : " + str(params[1]) + "\n               Length : " + str(params[2]))
        elif command == b'\xfe':
            print("GD: [VIDEO   ] Start video playback!\n               ClipIndx: " + str(params[0]))
        else:
            print("--  Unimplemented command: " + str(command))
            paramCount = 0
            for paramIndex in range(len(params)):
                for paramType in paramsType[paramIndex]:
                    if paramType in [8,9]:
                        print("\t" + str(paramType) + ":")
                    else:
                        print("\t" + str(paramType) + ": " + str(params[paramCount]))
                        paramCount += 1
        
        return [command, params]

    def jumpPadding(self, reader):
        reader.seek(self.lengthPad, 1)

