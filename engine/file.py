# File components of LAYTON1

import ndspy.rom, conf, const
from hat_io import binary, asset
from os import path

def debugPrint(*args, **kwargs):
    if conf.ENGINE_DEBUG_FILESYSTEM_MODE and conf.ENGINE_DEBUG_ENABLE_LOG:
        print(*args, **kwargs)

def debugErrorPrint(*args, **kwargs):
    if conf.ENGINE_DEBUG_FILESYSTEM_MODE and conf.ENGINE_DEBUG_ENABLE_ERROR:
        print(*args, **kwargs)

def debugSeverePrint(*args, **kwargs):
    if conf.ENGINE_DEBUG_FILESYSTEM_MODE and conf.ENGINE_DEBUG_ENABLE_SEVERE:
        print(*args, **kwargs)

def _isValidLayton(romFile):
    if conf.ENGINE_GAME_VARIANT == conf.LAYTON_1:
        return True
    elif conf.ENGINE_GAME_VARIANT == conf.LAYTON_2:
        if romFile.name == bytearray(b'LAYTON2') and romFile.idCode[:3] == bytearray(b'YLT'):
            return True
    return False

def resolveFilepath(filepath):
    filepath = ("/".join(filepath.split("\\"))).replace("?", conf.LAYTON_ASSET_LANG)
    return filepath

def resolveEventIntegerAsString(eventInt):
    eventIndex          = "%02d" % (eventInt // 1000)
    eventSubIndex       = "%03d" % (eventInt % 1000)
    extendedEventIndex  = eventIndex
    if eventIndex == "24":
        if eventInt % 1000 < 300:
            extendedEventIndex = "24a"
        elif eventInt % 1000 < 600:
            extendedEventIndex = "24b"
        else:
            extendedEventIndex = "24c"
    return (eventIndex, extendedEventIndex, eventSubIndex)

class FileInterface():

    LAYTON_IMAGE_FORMAT = [".arc", ".arj", ".bgx"]

    if conf.ENGINE_LOAD_FROM_ROM:
        rom = ndspy.rom.NintendoDSRom()
        if path.exists(conf.PATH_ROM):
            debugPrint("Mode: Accessing ROM")

            rom = ndspy.rom.NintendoDSRom.fromFile(conf.PATH_ROM)

            # TODO - Cache management, free up items when complete
            # TODO - Don't use linear search for parsing item names

            romCache = {}

            if _isValidLayton(rom):                
                if conf.ENGINE_GAME_VARIANT == conf.LAYTON_2:
                    PATH_ASSET_ROOT     = "data_lt2\\"
                else:
                    PATH_ASSET_ROOT     = "data\\"
                    PATH_ASSET_ETEXT    = PATH_ASSET_ROOT + "etext\\"
                    PATH_ASSET_QTEXT    = PATH_ASSET_ROOT + "qtext\\"
                    PATH_ASSET_ROOM     = PATH_ASSET_ROOT + "room\\"
            
                PATH_ASSET_ANI      = PATH_ASSET_ROOT + "ani\\"
                PATH_ASSET_BG       = PATH_ASSET_ROOT + "bg\\"
                PATH_ASSET_FONT     = PATH_ASSET_ROOT + "font\\"
                PATH_ASSET_SCRIPT   = PATH_ASSET_ROOT + "script\\"
            else:
                raise Exception("ROM is invalid!")
        else:
            raise Exception("ROM path incorrect!")
    else:
        debugPrint("Mode: Not using ROM")

        PATH_ASSET_ROOT     = path.dirname(path.dirname(path.realpath(__file__))) + "\\assets\\"
        PATH_ASSET_ANI      = PATH_ASSET_ROOT + "ani\\"
        PATH_ASSET_BG       = PATH_ASSET_ROOT + "bg\\"
        PATH_ASSET_ETEXT    = PATH_ASSET_ROOT + "etext\\"
        PATH_ASSET_FONT     = PATH_ASSET_ROOT + "font\\"
        PATH_ASSET_QTEXT    = PATH_ASSET_ROOT + "qtext\\"
        PATH_ASSET_ROOM     = PATH_ASSET_ROOT + "room\\"
        PATH_ASSET_SCRIPT   = PATH_ASSET_ROOT + "script\\"

    @staticmethod
    def _isPathAvailableRom(filepath):
        debugSeverePrint("RomCheck", resolveFilepath(filepath))
        if FileInterface.rom.filenames.idOf(resolveFilepath(filepath)) != None:
            return True
        return False
    
    @staticmethod
    def _isPathAvailableFile(filepath):
        def deriveExtension(filepath):
            if len(path.splitext(filepath)) > 1:
                if path.splitext(filepath)[1] in FileInterface.LAYTON_IMAGE_FORMAT:
                    return conf.FILE_DECOMPRESSED_EXTENSION_IMAGE
                return path.splitext(filepath)[1]
            return ""

        filepath = resolveFilepath(filepath)
        if conf.ENGINE_LOAD_FROM_DECOMPRESSED:
            filepath = path.splitext(filepath)[0] + deriveExtension(filepath)
        debugPrint(filepath)
        return path.exists(filepath)

    @staticmethod
    def _dataFromRom(filepath):
        if FileInterface._isPathAvailableRom(filepath):
            testFile = asset.File(data=FileInterface.rom.getFileByName(resolveFilepath(filepath)))
            testFile.decompress()
            debugPrint("RomGrab", resolveFilepath(filepath))
            return testFile.data
        debugErrorPrint("RomGrabFailed", resolveFilepath(filepath))
        return b''
    
    @staticmethod
    def _packedDataFromRom(filepathArchive, filename, version = 0):
        filepathArchive = resolveFilepath(filepathArchive)
        if filepathArchive not in FileInterface.romCache.keys():
            tempFile = asset.File(data=FileInterface._dataFromRom(filepathArchive))
            tempFile.decompress()
            FileInterface.romCache[filepathArchive] = asset.LaytonPack(version = version)
            FileInterface.romCache[filepathArchive].load(tempFile.data)
        else:
            debugPrint("CacheRomGrab", filename)
        return FileInterface.romCache[filepathArchive].getFile(filename)

    @staticmethod
    def _dataFromFile(filepath):
        reader = binary.BinaryReader(filename=resolveFilepath(filepath))
        return reader.data
    
    @staticmethod
    def _packedDataFromFile(filepathArchive, filename, version = 0):
        filepathArchive = resolveFilepath(filepathArchive)
        if conf.ENGINE_LOAD_FROM_DECOMPRESSED:
            filepathArchive = path.splitext(filepathArchive)[0]
        return FileInterface._dataFromFile(filepathArchive + "//" + filename)
    
    @staticmethod   # Null methods
    def doesFileExist(filepath):
        pass
    @staticmethod
    def getData(filepath):
        pass
    @staticmethod
    def getPackedData(filepathArchive, filepath, version = 0):
        pass

    if conf.ENGINE_LOAD_FROM_ROM:
        doesFileExist = _isPathAvailableRom
        getData = _dataFromRom
        getPackedData = _packedDataFromRom
    else:
        doesFileExist = _isPathAvailableFile
        getData = _dataFromFile
        getPackedData = _packedDataFromFile
