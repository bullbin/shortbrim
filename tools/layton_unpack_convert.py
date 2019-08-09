import sys, ndspy.rom, ndspy.lz10, asset_converter
from PIL import Image
from os import path, makedirs, remove

# To-do: For extraction of PCM archives, format extraction needs to be moved to a function. Format polling should also use the extension, although the filepath
#        will still need to be used for images since ARCs have different formats with the only distinction being their root folder

ROM_UNPACK_WITHOUT_TERMINAL = False
ROM_RECOMPRESS_ASSETS = True                # When this is enabled, accurate colours for decoding MUST be enabled as the Pillow DDS plugin has low compatibility
                                            # Please note that again the masking code in the plugin must be modified to work properly
ROM_LOCATION = r""

def extractAndIsExtractable(path, asset):
    with open(path, 'wb') as laytonRomFileOut:
        if asset[4] == 16:
            laytonRomFileOut.write(ndspy.lz10.decompress(asset[4:]))
            return True
        laytonRomFileOut.write(asset)
        return False

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
                            if extractAndIsExtractable(path.dirname(path.realpath(__file__)) + "\\" + filename, laytonRom.files[fileIndex]):
                                laytonBgDecoder = asset_converter.LaytonImage(path.dirname(path.realpath(__file__)) + "\\" + filename)
                                remove(path.dirname(path.realpath(__file__)) + "\\" + filename)
                                laytonBgDecoder.export()
                                if ROM_RECOMPRESS_ASSETS:
                                    imageCompress = Image.open(path.dirname(path.realpath(__file__)) + "\\" + '.'.join(filename.split(".")[0:-1]) + ".dds")
                                    imageCompress.save(path.dirname(path.realpath(__file__)) + "\\" + '.'.join(filename.split(".")[0:-1]) + ".png", optimise=True)
                                    imageCompress.close()
                                    remove(path.dirname(path.realpath(__file__)) + "\\" + '.'.join(filename.split(".")[0:-1]) + ".dds")
                                del laytonBgDecoder
                        elif "\\ani\\" in filename:
                            if extractAndIsExtractable(path.dirname(path.realpath(__file__)) + "\\" + filename, laytonRom.files[fileIndex]):
                                if filename[-3:] == "arc" or filename[-3:] == "arj":
                                    try:
                                        if filename[-3:] == "arc":
                                            laytonAnimDecoder = asset_converter.LaytonArc(path.dirname(path.realpath(__file__)) + "\\" + filename)
                                        else:
                                            laytonAnimDecoder = asset_converter.LaytonArj(path.dirname(path.realpath(__file__)) + "\\" + filename)
                                        remove(path.dirname(path.realpath(__file__)) + "\\" + filename)
                                        laytonAnimDecoder.export()
                                        if ROM_RECOMPRESS_ASSETS:
                                            for indexImage in range(len(laytonAnimDecoder.images)):
                                                imageCompress = Image.open(path.dirname(path.realpath(__file__)) + "\\" + '.'.join(filename.split(".")[0:-1]) + "_" + str(indexImage) + ".dds")
                                                imageCompress.save(path.dirname(path.realpath(__file__)) + "\\" + '.'.join(filename.split(".")[0:-1]) + "_" + str(indexImage) + ".png", optimise=True)
                                                imageCompress.close()
                                                remove(path.dirname(path.realpath(__file__)) + "\\" + '.'.join(filename.split(".")[0:-1]) + "_" + str(indexImage) + ".dds")
                                        del laytonAnimDecoder
                                    except OverflowError:
                                        print("Could not load " + filename)
                        else:
                            with open(path.dirname(path.realpath(__file__)) + "\\" + filename, 'wb') as laytonRomFileOut:
                                laytonRomFileOut.write(laytonRom.files[fileIndex])
        else:
            print("Invalid Curious Village ROM.")
print("Unpacking completed!")