import c4d
import os
import sys

# Add lib folder to the system path
current_path = os.path.abspath(__file__)
parent_directory = os.path.dirname(current_path)
lib_path = os.path.join(parent_directory, 'lib')
sys.path.insert(0, lib_path)

import OmniscientImporter as omniscient_importer
from safeFrameTag import SafeFrameTag

# Unique plugin IDs
PLUGIN_ID = 1063004
SAFE_FRAME_TAG_ID = 1063016  # Replace with your actual unique ID for SafeFrameTag

class OmniscientImporterPlugin(c4d.plugins.CommandData):
    def Execute(self, doc):
        omniscient_importer.main(doc)
        return True

def main():
    icon_path = os.path.join(parent_directory, "res", "icon.png")
    icon_bitmap = c4d.bitmaps.BaseBitmap()
    result, _ = icon_bitmap.InitWith(icon_path)
    if result != c4d.IMAGERESULT_OK:
        raise MemoryError("Failed to initialize BaseBitmap with icon.png.")

    # Register the Omniscient Importer plugin
    if not c4d.plugins.RegisterCommandPlugin(
            id=PLUGIN_ID,
            str="Omniscient Importer",
            info=0,
            icon=icon_bitmap,
            help="Import files with the Omniscient Importer.",
            dat=OmniscientImporterPlugin()):
        raise RuntimeError("Failed to register Omniscient Importer plugin.")

    # Register the SafeFrame Tag
    if not c4d.plugins.RegisterTagPlugin(
            id=SAFE_FRAME_TAG_ID,
            str="SafeFrameTag",
            info=c4d.TAG_EXPRESSION | c4d.TAG_VISIBLE,
            g=SafeFrameTag,
            description="Tsafe_frame",
            icon=icon_bitmap):
        raise RuntimeError("Failed to register SafeFrame Tag.")

if __name__ == "__main__":
    main()
