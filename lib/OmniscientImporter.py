import c4d
import json
import logging
import os
from c4d import storage, documents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            safe_frame_tag = c4d.BaseTag(1063016)
            obj.InsertTag(safe_frame_tag)
            logger.info(f"SafeFrameTag assigned to: {obj.GetName()}")

def update_project_settings(doc, width, height, fps):
    rd = doc.GetActiveRenderData()
    rd[c4d.RDATA_XRES] = width
    rd[c4d.RDATA_YRES] = height
    rd[c4d.RDATA_FRAMERATE] = fps
    film_aspect_ratio = width / float(height)
    rd[c4d.RDATA_FILMASPECT] = film_aspect_ratio
    documents.SetActiveDocument(doc)
    c4d.EventAdd()

def main(doc):
    file_path = storage.LoadDialog(title="Select .omni File", flags=c4d.FILESELECT_LOAD, force_suffix="omni")
    if file_path:
        logger.info(f"Selected .omni file: {file_path}")
        try:
            with open(file_path, "r") as file:
                omni_data = json.load(file)
            logger.info("Parsed .omni data.")

            # Extract project settings from .omni data
            video_data = omni_data.get("data", {}).get("video", {})
            width = int(float(video_data.get("resolution", {}).get("width", "1920")))
            height = int(float(video_data.get("resolution", {}).get("height", "1080")))
            fps = float(video_data.get("fps", "30"))

            # Update Cinema 4D project settings
            update_project_settings(doc, width, height, fps)

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
    else:
        logger.warning("No .omni file selected.")