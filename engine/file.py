# File components of LAYTON1

import ndspy.rom, conf, const
from os import path

class FileInterface():

    if conf.ENGINE_LOAD_FROM_ROM:
        RomFile = ndspy.rom.NintendoDSRom()
        if path.exists(conf.PATH_ROM):
            RomFile = ndspy.rom.NintendoDSRom.fromFile(conf.PATH_ROM)
            print("LOADED ROM!!!!")
        else:
            raise Exception("ROM path incorrect!")

    def __init__(self):
        if conf.ENGINE_LOAD_FROM_ROM:
            self.isPathAvailable = self.isPathAvailableRom
            self.getData = self.dataFromRom
        else:
            self.isPathAvailable = self.isPathAvailableFile
            self.getData = self.dataFromFile

    def isPathAvailableRom(self):
        pass

    def isPathAvailableFile(self):
        pass

    def dataFromRom(self):
        pass

    def dataFromFile(self):
        pass

    def reload(self):
        pass