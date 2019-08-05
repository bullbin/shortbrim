import sys, ndspy.rom, ndspy.lz10, asset_bg, io
from PIL import Image
from os import path, makedirs, remove

ROM_UNPACK_WITHOUT_TERMINAL = False
ROM_RECOMPRESS_ASSETS = True                # When this is enabled, accurate colours for decoding MUST be enabled as the Pillow DDS plugin has low compatibility
                                            # Please note that again the masking code in the plugin must be modified to work properly
ROM_LOCATION = r""

if len(sys.argv) > 1 or ROM_UNPACK_WITHOUT_TERMINAL:
    if ROM_UNPACK_WITHOUT_TERMINAL:
        romPath = ROM_LOCATION
    else:
        romPath = sys.argv[1]
    if path.exists(romPath):
        with open(romPath, 'rb') as ndsRom:
            laytonRom = ndsRom.read()

        laytonRom = ndspy.rom.NintendoDSRom(laytonRom)
        if laytonRom.name == bytearray(b'LAYTON1'):
            for fileIndex in range(len(laytonRom.files)):
                if laytonRom.filenames.filenameOf(fileIndex) != None:
                    
                    filename = laytonRom.filenames.filenameOf(fileIndex).replace("/", "\\")
                    filepath = path.dirname(path.dirname(path.realpath(__file__)) + "\\" + filename)

                    if not(path.exists(path.dirname(path.realpath(__file__)) + "\\" + filename)):
                        makedirs(filepath, exist_ok=True)
                        if "\\bg\\" in filename:
                            with open(path.dirname(path.realpath(__file__)) + "\\" + filename, 'wb') as laytonRomFileOut:
                                if laytonRom.files[fileIndex][4] == 16:
                                    laytonRomFileOut.write(ndspy.lz10.decompress(laytonRom.files[fileIndex][4:]))
                                else:
                                    laytonRomFileOut.write(laytonRom.files[fileIndex])
                            if laytonRom.files[fileIndex][4] == 16:
                                laytonBgDecoder = asset_bg.laytonImage(path.dirname(path.realpath(__file__)) + "\\" + filename)
                                remove(path.dirname(path.realpath(__file__)) + "\\" + filename)
                                laytonBgDecoder.export()
                                if ROM_RECOMPRESS_ASSETS:
                                    imageCompress = Image.open(path.dirname(path.realpath(__file__)) + "\\" + '.'.join(filename.split(".")[0:-1]) + ".dds")
                                    imageCompress.save(path.dirname(path.realpath(__file__)) + "\\" + '.'.join(filename.split(".")[0:-1]) + ".png", optimise=True)
                                    imageCompress.close()
                                    remove(path.dirname(path.realpath(__file__)) + "\\" + '.'.join(filename.split(".")[0:-1]) + ".dds")
                        else:
                            with open(path.dirname(path.realpath(__file__)) + "\\" + filename, 'wb') as laytonRomFileOut:
                                laytonRomFileOut.write(laytonRom.files[fileIndex])
        else:
            print("Invalid Curious Village ROM.")

print("Unpacking completed!")
