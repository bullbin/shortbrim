import sys, ndspy.rom, ndspy.lz10, asset_converter, io
from PIL import Image
from os import path, makedirs, remove

# To-do: For extraction of PCM archives, format extraction needs to be moved to a function. Format polling should also use the extension, although the filepath
#        will still need to be used for images since ARCs have different formats with the only distinction being their root folder

ROM_UNPACK_WITHOUT_TERMINAL = False
ROM_RECOMPRESS_ASSETS = True                # When this is enabled, accurate colours for decoding MUST be enabled as the Pillow DDS plugin has low compatibility
                                            # Please note that again the masking code in the plugin must be modified to work properly
ROM_LOCATION = r""
ROM_EXPORT_LOCATION = path.dirname(path.dirname(path.realpath(__file__))) + "\\assets"

def pngExport(dataIn, filenameOut):
    imageCompress = Image.open(io.BytesIO(dataIn))
    imageCompress.save(filenameOut, optimise=True)
    imageCompress.close()

def extractAndIsExtractable(path, asset):
    with open(path, 'wb') as laytonRomFileOut:
        if path[-4:] == ".pcm" and asset[0] == 16:
            laytonRomFileOut.write(ndspy.lz10.decompress(asset))    # ndspy might not be extracting these properly, as the original contents are stuck on the end
            return True                                             #     Luckily this isn't an issue as the files store a filecount and will be deleted after usage
        elif asset[4] == 16:                    
            laytonRomFileOut.write(ndspy.lz10.decompress(asset[4:]))
            return True
        laytonRomFileOut.write(asset)
    if asset[4] == 48:
        if path[-4:] == ".pcm":
            asset_converter.RleArchive(path)
        else:
            asset_converter.RleArchive(path, offsetIn=4)
        return True
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
                    if "data\\" in filename:
                        filename = filename[5:]
                        filepath = ROM_EXPORT_LOCATION + "\\" + filename
                        doesExist = False
                        if filename[-4:] == ".arc" or filename[-4:] == ".arj":
                            if path.exists(filepath):
                                doesExist = True
                            else:
                                if "bg\\" in filename:
                                    if ROM_RECOMPRESS_ASSETS:
                                        doesExist = path.exists(filepath[0:-4] + ".png")
                                    else:
                                        doesExist = path.exists(filepath[0:-4] + ".dds")
                                elif ".pcm" in filename:
                                    doesExist = path.exists(filepath[0:-4])
                                else:
                                    if ROM_RECOMPRESS_ASSETS:
                                        doesExist = path.exists(filepath[0:-4] + "_0.png")
                                    else:
                                        doesExist = path.exists(filepath[0:-4] + "_0.dds")
                        else:
                            doesExist = path.exists(filepath)
                        if not(doesExist):
                            makedirs(path.dirname(filepath), exist_ok=True)
                            if "bg\\" in filename:
                                if extractAndIsExtractable(filepath, laytonRom.files[fileIndex]):
                                    laytonBgDecoder = asset_converter.LaytonImage(filepath)
                                    remove(filepath)
                                    if ROM_RECOMPRESS_ASSETS:
                                        pngExport(laytonBgDecoder.outputImage.getData(), ROM_EXPORT_LOCATION + "\\" + '.'.join(filename.split(".")[0:-1]) + ".png")
                                    else:
                                        laytonBgDecoder.export()
                                    del laytonBgDecoder
                            elif "ani\\" in filename:
                                if extractAndIsExtractable(filepath, laytonRom.files[fileIndex]):
                                    if filename[-3:] == "arc" or filename[-3:] == "arj":
                                        try:
                                            if filename[-3:] == "arc":
                                                laytonAnimDecoder = asset_converter.LaytonArc(filepath)
                                            else:
                                                laytonAnimDecoder = asset_converter.LaytonArj(filepath)
                                            remove(filepath)
                                            if ROM_RECOMPRESS_ASSETS:
                                                laytonAnimDecoder.exportAnimText()
                                                for indexImage in range(len(laytonAnimDecoder.images)):
                                                    pngExport(laytonAnimDecoder.images[indexImage].getData(), ROM_EXPORT_LOCATION + "\\" + '.'.join(filename.split(".")[0:-1]) + "_" + str(indexImage) + ".png")
                                            else:
                                                laytonAnimDecoder.export()
                                            del laytonAnimDecoder
                                        except OverflowError:
                                            print("Could not load " + filename)
                            elif ".pcm" in filename:
                                if extractAndIsExtractable(filepath, laytonRom.files[fileIndex]):
                                    laytonPcmDecoder = asset_converter.LaytonPackArchive(filepath)
                            else:
                                with open(filepath, 'wb') as laytonRomFileOut:
                                    laytonRomFileOut.write(laytonRom.files[fileIndex])
            print("Unpacking completed!")
        else:
            print("Invalid Curious Village ROM.")
    else:
        print("ROM doesn't exist!")
else:
    print("No import path provided!")