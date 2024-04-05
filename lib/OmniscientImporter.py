import c4d
import json
import logging
import os
from c4d import storage
from c4d import gui

# Define custom IDs for UI elements
IDC_RESOLUTION = 1000
IDC_ORIENTATION = 1001
IDC_ASPECT_RATIO = 1002
IDC_OK = 1003
IDC_CANCEL = 1004
IDC_RESULT_TEXT = 1005
IDC_SELECT_OMNI_FILE = 1006
IDC_OMNI_FILE_PATH_DISPLAY = 1007

class CustomDialog(gui.GeDialog):
    def __init__(self):
        # Initialize with defaults for HD, Vertical orientation, and 16:9 aspect ratio
        self.width = 1080
        self.height = 1920
        self.resolutionSelection = 1  # Default to HD
        self.orientationSelection = 2  # Default to Vertical
        self.aspectRatioSelection = 2  # Default to 16:9
        self.dialogConfirmed = False
        self.omniFilePath = ""
    
    def CreateLayout(self):
        self.SetTitle("Omniscient Importer")

        # Resolution ComboBox with default selection
        self.AddComboBox(IDC_RESOLUTION, c4d.BFH_SCALEFIT)
        self.AddChild(IDC_RESOLUTION, 1, "HD")
        self.AddChild(IDC_RESOLUTION, 2, "4K")
        self.SetInt32(IDC_RESOLUTION, self.resolutionSelection)

        # Aspect Ratio ComboBox
        self.AddComboBox(IDC_ASPECT_RATIO, c4d.BFH_SCALEFIT)
        self.AddChild(IDC_ASPECT_RATIO, 1, "4:3")
        self.AddChild(IDC_ASPECT_RATIO, 2, "16:9")
        self.SetInt32(IDC_ASPECT_RATIO, self.aspectRatioSelection)

        # Orientation ComboBox with default selection
        self.AddComboBox(IDC_ORIENTATION, c4d.BFH_SCALEFIT)
        self.AddChild(IDC_ORIENTATION, 1, "Horizontal")
        self.AddChild(IDC_ORIENTATION, 2, "Vertical")
        self.SetInt32(IDC_ORIENTATION, self.orientationSelection)

        # Static text field for displaying result
        self.AddStaticText(IDC_RESULT_TEXT, c4d.BFH_CENTER, name="", borderstyle=c4d.BORDER_NONE)

        self.AddButton(IDC_SELECT_OMNI_FILE, c4d.BFH_SCALE, name="Select .omni File")
        self.AddStaticText(IDC_OMNI_FILE_PATH_DISPLAY, c4d.BFH_CENTER, name="                                        ", borderstyle=c4d.BORDER_NONE)

        # Group for buttons, centered horizontally
        if self.GroupBegin(0, c4d.BFH_CENTER, 2, 0):
            self.GroupBorderSpace(10, 0, 10, 10)

            # Cancel and OK Buttons inside the group, Cancel on the left
            self.AddButton(IDC_CANCEL, c4d.BFH_SCALE, initw=100, name="Cancel")
            self.AddButton(IDC_OK, c4d.BFH_SCALE, initw=100, name="OK")

            self.GroupEnd()

        # Initial UI state update based on defaults
        self.updateUIState()
        self.updateResultTextField()

        return True

    def Command(self, id, msg):
        if id == IDC_RESOLUTION:
            self.resolutionSelection = self.GetInt32(IDC_RESOLUTION)
            self.updateUIState()
        elif id in [IDC_ORIENTATION, IDC_ASPECT_RATIO]:
            pass
        
        self.updateDimensionsAndAspectRatio()
        self.updateResultTextField()
        
        if id == IDC_OK:
            self.dialogConfirmed = True  # Set to True when OK is pressed
            self.Close()
            return True
        elif id == IDC_CANCEL:
            self.dialogConfirmed = False  # Set to False when Cancel is pressed
            self.Close()
            return True  # It's still True because the action was handled
        
        if id == IDC_SELECT_OMNI_FILE:
            # Open the file selection dialog when the button is clicked
            self.omniFilePath = storage.LoadDialog(title="Select .omni File", flags=c4d.FILESELECT_LOAD, force_suffix="omni")
            if self.omniFilePath:
                # Extract just the file name from the full path
                fileName = os.path.basename(self.omniFilePath)
                # Update the static text element to display the file name
                self.SetString(IDC_OMNI_FILE_PATH_DISPLAY, fileName)
            else:
                # If no file is selected, clear the file name display
                self.SetString(IDC_OMNI_FILE_PATH_DISPLAY, "")
            return True
        
        return True


    def updateDimensionsAndAspectRatio(self):
        self.orientationSelection = self.GetInt32(IDC_ORIENTATION)
        self.aspectRatioSelection = self.GetInt32(IDC_ASPECT_RATIO)
        
        if self.resolutionSelection == 1:  # HD
            if self.aspectRatioSelection == 1:  # 4:3
                base_width, base_height = 1440, 1080
            else:  # 16:9
                base_width, base_height = 1920, 1080
        else:  # 4K, only 16:9 is considered valid for 4K in this setup
            base_width, base_height = 3840, 2160
        
        if self.orientationSelection == 1:  # Horizontal
            self.width, self.height = base_width, base_height
        else:  # Vertical
            self.width, self.height = base_height, base_width

    def updateResultTextField(self):
        result_text = f"{self.width}x{self.height}"
        self.SetString(IDC_RESULT_TEXT, result_text)

    def updateUIState(self):
        # Disable and set aspect ratio to 16:9 if resolution is 4K
        if self.resolutionSelection == 2:  # 4K
            self.Enable(IDC_ASPECT_RATIO, False)
            self.SetInt32(IDC_ASPECT_RATIO, 2)  # Force select 16:9
        else:
            self.Enable(IDC_ASPECT_RATIO, True)

    def GetValues(self):
        # Retrieve width, height, and other settings as needed
        return self.width, self.height, ("4:3" if self.aspectRatioSelection == 1 else "16:9")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(doc):
    dlg = CustomDialog()
    if dlg.Open(c4d.DLG_TYPE_MODAL, defaultw=300, defaulth=100) and dlg.dialogConfirmed:
        # Get width, height, and orientation after the dialog has been closed
        width, height, orientation = dlg.GetValues()
        file_path = dlg.omniFilePath

        if file_path:
            logger.info(f"Selected .omni file: {file_path}")
            try:
                # Read the contents of the .omni file
                with open(file_path, "r") as file:
                    omni_data = json.load(file)
                logger.info("Parsed .omni data.")

                doc = c4d.documents.GetActiveDocument()

                # Handling geometry import
                geometry_paths = omni_data.get("data", {}).get("geometry", {}).get("relative_path", [])
                if geometry_paths:
                    for geo_path in geometry_paths:
                        obj_path = os.path.join(os.path.dirname(file_path), geo_path)
                        process_import(doc, obj_path, "Scan_Omni")

                # Handling camera import
                camera_path = omni_data.get("data", {}).get("camera", {}).get("relative_path", "")
                if camera_path:
                    cam_path = os.path.join(os.path.dirname(file_path), camera_path)
                    process_import(doc, cam_path, "Camera_Omni", is_camera=True)

                # Updating project settings
                update_project_settings(doc, width, height)

            except Exception as e:
                logger.exception("An error occurred: ", exc_info=e)
        else:
            logger.warning("No .omni file selected.")

def process_import(doc, file_path, default_name, is_camera=False):
    if os.path.isfile(file_path):
        objects_before_import = set(doc.GetObjects())
        if c4d.documents.MergeDocument(doc, file_path, c4d.SCENEFILTER_OBJECTS | c4d.SCENEFILTER_MATERIALS):
            logger.info(f"Successfully imported: {file_path}")
            objects_after_import = set(doc.GetObjects())
            new_objects = objects_after_import - objects_before_import
            for obj in new_objects:
                obj.SetName(default_name)
            if is_camera:
                assign_safe_frame_tag_to_camera(new_objects)
            c4d.EventAdd()
        else:
            logger.error(f"Failed to import: {file_path}")
    else:
        logger.warning(f"File not found: {file_path}")

def assign_safe_frame_tag_to_camera(new_objects):
    for obj in new_objects:
        if obj.GetType() == 1028083 or obj.GetType() == 5103:
            safe_frame_tag = c4d.BaseTag(1063016)  # Ensure this is your SafeFrameTag plugin ID
            obj.InsertTag(safe_frame_tag)
            logger.info(f"SafeFrameTag assigned to: {obj.GetName()}")
            break  # Assuming only one camera import at a time

def update_project_settings(doc, width, height):
    rd = doc.GetActiveRenderData()
    rd[c4d.RDATA_XRES] = int(float(width))
    rd[c4d.RDATA_YRES] = int(float(height))
    film_aspect_ratio = float(width) / float(height)
    rd[c4d.RDATA_FILMASPECT] = film_aspect_ratio
    c4d.EventAdd()
