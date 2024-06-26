import c4d
import json
import logging
import os
from c4d import documents
from cameraBaker import bake_alembic_camera_animation
from videoBackground import create_background_with_video_material
from projectSettings import set_project_settings_from_video
from adjustScale import adjust_scale
import plugin_version
from OmniscientMessage import OMNISCIENT_DIALOG_EVENT_ID, DialogDataStorage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OMNISCIENT_SCENE_CONTROL_TAG_ID = 1063027

def get_object_dict(objects):
    return {obj.GetGUID(): obj for obj in objects}

def process_import(doc, file_path, default_name, import_options=None):
    if import_options is None:
        import_options = {}

    bake_camera = import_options.get("bake_camera", False)
    is_camera = import_options.get("is_camera", False)
    camera_fps = import_options.get("camera_fps")
    video_fps = import_options.get("video_fps")
    
    # Check if the file is an Alembic file when importing a camera
    if is_camera and not file_path.lower().endswith('.abc'):
        error_message = "Camera import failed. The Omniscient importer requires the camera as an Alembic (.abc)"
        logger.error("{}: {}".format(error_message, file_path))
        c4d.gui.MessageDialog(error_message)
        return
    
    # Check if the file exists
    if not os.path.isfile(file_path):
        logger.warning("File not found: {}".format(file_path))
        if file_path.lower().endswith('.obj'):
            error_message = "Scan import failed. The scan '{}' needs to be in the same folder as the .omni file.".format(os.path.basename(file_path))
        else:
            error_message = "File '{}' not found.".format(os.path.basename(file_path))
        logger.error(error_message)
        c4d.gui.MessageDialog(error_message)
        return
    
    # Adjust scales before attempting import
    adjust_scale('abc', 1.0, c4d.DOCUMENT_UNIT_M)
    adjust_scale('obj', 1.0, c4d.DOCUMENT_UNIT_M)

    # Import the file
    objects_before_import = get_object_dict(doc.GetObjects())
    if c4d.documents.MergeDocument(doc, file_path, c4d.SCENEFILTER_OBJECTS | c4d.SCENEFILTER_MATERIALS):
        logger.info("Successfully imported: {}".format(file_path))
        objects_after_import = get_object_dict(doc.GetObjects())
        new_objects_guids = objects_after_import.keys() - objects_before_import.keys()
        new_objects = [objects_after_import[guid] for guid in new_objects_guids]
        
        for obj in new_objects:
            obj.SetName(default_name)
            if is_camera:
                handle_camera_operations(doc, new_objects, camera_fps=camera_fps, video_fps=video_fps, bake_camera=bake_camera)
        c4d.EventAdd()
    else:
        logger.error("Failed to import: {}".format(file_path))

def handle_camera_operations(doc, new_objects, camera_fps=None, video_fps=None, bake_camera=False):
    """Handles camera-specific operations, adjusts settings, and optionally replaces the Alembic camera with a baked one."""
    for obj in new_objects:
        if obj.GetType() == 1028083:  # Check if it's an Alembic camera

            # Adjust the Alembic camera settings first
            adjust_alembic_camera_settings(doc, obj, camera_fps=camera_fps, video_fps=video_fps)
            logger.info("Camera settings adjusted")
            
            if bake_camera:
                try:
                    # Bake the Alembic as a new camera
                    new_camera = bake_alembic_camera_animation(doc, obj)
                    logger.info("Alembic camera animation baked to: {}".format(new_camera.GetName()))
                    
                    # Assign omniscient scene control tag to the new camera
                    assign_omniscient_control_tag_to_camera(doc, [new_camera])
                    
                    # Make the viewport look through the Alembic camera
                    make_viewport_look_through_camera(doc, new_camera)

                    # Remove the Alembic camera, since it's replaced by the baked one
                    doc.AddUndo(c4d.UNDOTYPE_DELETE, obj)
                    obj.Remove()
                except Exception as e:
                    logger.error("Error during camera processing: {}".format(e))
            else:
                # If not baking, ensure the Alembic camera still receives any applicable updates
                assign_omniscient_control_tag_to_camera(doc, [obj])

                # Make the viewport look through the Alembic camera
                make_viewport_look_through_camera(doc, obj)

    c4d.EventAdd()

def assign_omniscient_control_tag_to_camera(doc, camera_objects):
    """Assigns omniscient scene control tag to given camera objects."""
    for camera in camera_objects:
        omniscient_control_tag = c4d.BaseTag(OMNISCIENT_SCENE_CONTROL_TAG_ID)
        camera.InsertTag(omniscient_control_tag)
        logger.info("OmniscientSceneControl assigned to: {}".format(camera.GetName()))
        
        # Link background to tag, assuming one background object named 'Background_Omni'
        background = doc.SearchObject('Background_Omni')
        if background:
            omniscient_control_tag[c4d.OMNISCIENTSCENECONTROL_BACKGROUND_LINK] = background


def adjust_alembic_camera_settings(doc, obj, animation_offset_frames=1, camera_fps=None, video_fps=None):
    # Check if the object is an Alembic camera
    if obj.GetType() == 1028083:
        animation_offset = c4d.BaseTime(animation_offset_frames, doc.GetFps())
        obj[c4d.ALEMBIC_ANIMATION_OFFSET] = animation_offset

        # Calculate the speed adjustment factor based on FPS values, if FPS values are provided
        if camera_fps is not None and video_fps is not None:
            speed_adjustment_factor = video_fps / camera_fps
            obj[c4d.ALEMBIC_ANIMATION_SPEED] = speed_adjustment_factor

def update_project_settings(doc, width, height, fps):
    rd = doc.GetActiveRenderData()
    rd[c4d.RDATA_XRES] = width
    rd[c4d.RDATA_YRES] = height
    rd[c4d.RDATA_FRAMERATE] = fps
    film_aspect_ratio = width / float(height)
    rd[c4d.RDATA_FILMASPECT] = film_aspect_ratio
    documents.SetActiveDocument(doc)
    c4d.EventAdd()

def set_viewport_to_lines(doc):
    """Sets the active viewport display to 'Lines' mode."""
    bd = doc.GetActiveBaseDraw()
    if bd is None:
        logger.error("No active BaseDraw found. Cannot set viewport to Lines mode.")
        return

    bd[c4d.BASEDRAW_DATA_SDISPLAYACTIVE] = c4d.BASEDRAW_SDISPLAY_NOSHADING

    c4d.EventAdd()

def make_viewport_look_through_camera(doc, camera):
    """Sets the active viewport to look through the given camera."""
    bd = doc.GetActiveBaseDraw()
    if bd is None:
        logger.error("No active BaseDraw found. Cannot set camera view.")
        return

    bd.SetSceneCamera(camera)

    c4d.EventAdd()

def import_omni_file(doc, file_path):
    logger.info("Selected .omni file: {}".format(file_path))
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
        
        # Extract FPS values
        video_fps = float(omni_data.get("data", {}).get("video", {}).get("fps")) if "fps" in omni_data.get("data", {}).get("video", {}) else None
        camera_fps = float(omni_data.get("data", {}).get("camera", {}).get("fps")) if "fps" in omni_data.get("data", {}).get("camera", {}) else None

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
            error_message = "Video import failed. The video file '{}' needs to be in the same folder as the .omni file.".format(os.path.basename(video_path))
            logger.error(error_message)
            c4d.gui.MessageDialog(error_message)

        # Handle geometry import
        geometry_paths = omni_data.get("data", {}).get("geometry", {}).get("relative_path", [])
        if geometry_paths:
            for geo_path in geometry_paths:
                if not geo_path.strip():
                    logger.warning("Gometry path is empty.")
                    continue 
                obj_path = os.path.join(os.path.dirname(file_path), geo_path)
                process_import(doc, obj_path, "Scan_Omni")

        # Handle camera import
        camera_path = omni_data.get("data", {}).get("camera", {}).get("relative_path", "")
        if camera_path:
            cam_path = os.path.join(os.path.dirname(file_path), camera_path)
            camera_import_options = {
                "is_camera": True,
                "camera_fps": camera_fps,
                "video_fps": video_fps,
                "bake_camera": True
            }
            process_import(doc, cam_path, "Camera_Omni", import_options=camera_import_options)
        
        set_viewport_to_lines(doc)

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
        logger.error("No file selected.")