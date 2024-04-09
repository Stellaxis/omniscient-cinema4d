import c4d
import json
import logging
import os
from c4d import documents
from videoBackground import create_background_with_video_material
from projectSettings import set_project_settings_from_video
from adjustScale import adjust_scale
import plugin_version
from OmniscientMessage import OMNISCIENT_DIALOG_EVENT_ID, DialogDataStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OMNISCIENT_SCENE_CONTROL_TAG_ID = 1063027

def process_import(doc, file_path, default_name, is_camera=False):
    # Check if the file is an Alembic file when importing a camera
    if is_camera and not file_path.lower().endswith('.abc'):
        error_message = "Camera import failed. The Omniscient importer requires the camera as an Alembic (.abc)"
        logger.error(f"{error_message}: {file_path}")
        c4d.gui.MessageDialog(error_message)
        return
    
    adjust_scale('abc', 1.0, c4d.DOCUMENT_UNIT_M)
    adjust_scale('obj', 1.0, c4d.DOCUMENT_UNIT_M)

    if os.path.isfile(file_path):
        objects_before_import = set(doc.GetObjects())
        if c4d.documents.MergeDocument(doc, file_path, c4d.SCENEFILTER_OBJECTS | c4d.SCENEFILTER_MATERIALS):
            logger.info(f"Successfully imported: {file_path}")
            objects_after_import = set(doc.GetObjects())
            new_objects = objects_after_import - objects_before_import
            for obj in new_objects:
                obj.SetName(default_name)
                if is_camera:
                    adjust_alembic_camera_settings(doc, obj)
                    assign_safe_frame_tag_to_camera(doc, new_objects)
                c4d.EventAdd()
        else:
            logger.error(f"Failed to import: {file_path}")
    else:
        logger.warning(f"File not found: {file_path}")

def assign_safe_frame_tag_to_camera(doc, new_objects):
    for obj in new_objects:
        if obj.GetType() == 1028083 or obj.GetType() == 5103:
            safe_frame_tag = c4d.BaseTag(OMNISCIENT_SCENE_CONTROL_TAG_ID)
            obj.InsertTag(safe_frame_tag)
            logger.info(f"OmniscientSceneControl assigned to: {obj.GetName()}")

            # Link background to tag
            background = doc.SearchObject('Background_Omni')
            if background:
                safe_frame_tag[c4d.OMNISCIENTSCENECONTROL_BACKGROUND_LINK] = background

def adjust_alembic_camera_settings(doc, obj, animation_offset_frames=1):
    if obj.GetType() == 1028083:  # Check if the object is an Alembic camera
        animation_offset = c4d.BaseTime(animation_offset_frames, doc.GetFps())
        obj[c4d.ALEMBIC_ANIMATION_OFFSET] = animation_offset

def update_project_settings(doc, width, height, fps):
    rd = doc.GetActiveRenderData()
    rd[c4d.RDATA_XRES] = width
    rd[c4d.RDATA_YRES] = height
    rd[c4d.RDATA_FRAMERATE] = fps
    film_aspect_ratio = width / float(height)
    rd[c4d.RDATA_FILMASPECT] = film_aspect_ratio
    documents.SetActiveDocument(doc)
    c4d.EventAdd()

def import_omni_file(doc, file_path):
    logger.info(f"Selected .omni file: {file_path}")
    try:
        with open(file_path, "r") as file:
            omni_data = json.load(file)
        logger.info("Parsed .omni data.")

        # Version check
        minimum_required_version = omni_data.get("cinema4d", {}).get("minimum_plugin_version", "0.0.0")
        try:
            plugin_version.check_plugin_version(minimum_required_version)
        except plugin_version.UnsupportedVersionException as e:
            data_storage = DialogDataStorage.getInstance()
            data_storage.set_data("Omniscient", str(e), e.update_url)
            c4d.SpecialEventAdd(OMNISCIENT_DIALOG_EVENT_ID)
            return
        
        # Extract project settings from .omni data
        video_data = omni_data.get("data", {}).get("video", {})
        width = int(float(video_data.get("resolution", {}).get("width", "1920")))
        height = int(float(video_data.get("resolution", {}).get("height", "1080")))
        fps = float(video_data.get("fps", "30"))

        # Update Cinema 4D project settings
        update_project_settings(doc, width, height, fps)

        # Create material from video and set project settings
        video_path = os.path.join(os.path.dirname(file_path), video_data.get("relative_path", ""))
        if os.path.exists(video_path):
            create_background_with_video_material(doc, video_path)
            set_project_settings_from_video(doc, video_path)
        else:
            logger.warning(f"Video file not found: {video_path}")

        # Handle geometry import
        geometry_paths = omni_data.get("data", {}).get("geometry", {}).get("relative_path", [])
        if geometry_paths:
            for geo_path in geometry_paths:
                obj_path = os.path.join(os.path.dirname(file_path), geo_path)
                process_import(doc, obj_path, "Scan_Omni")

        # Handle camera import
        camera_path = omni_data.get("data", {}).get("camera", {}).get("relative_path", "")
        if camera_path:
            cam_path = os.path.join(os.path.dirname(file_path), camera_path)
            process_import(doc, cam_path, "Camera_Omni", is_camera=True)

    except Exception as e:
        logger.exception("An error occurred while processing the .omni file: ", exc_info=e)

def main(doc):
    file_path = c4d.storage.LoadDialog(title="Select .omni File", flags=c4d.FILESELECT_LOAD, force_suffix="omni")
    
    # Check if a file was selected
    if file_path:
        # Check if the selected file has the .omni extension
        if not file_path.lower().endswith('.omni'):
            c4d.gui.MessageDialog("Please select a file with the .omni extension.")
            return
        import_omni_file(doc, file_path)
    else:
        print("No file selected.")