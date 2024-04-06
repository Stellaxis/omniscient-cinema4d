import c4d
import json
import logging
import os
from c4d import storage, documents

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_obj_import_scale_factor():
    obj_import_id = c4d.FORMAT_OBJIMPORT if c4d.GetC4DVersion() < 17000 else c4d.FORMAT_OBJ2IMPORT
    prefs = c4d.plugins.GetWorldPluginData(obj_import_id)

    if prefs is None:
        print("No global plugin data found for OBJ Importer.")
        return None

    unit_scale_data = prefs[2010]
    if unit_scale_data:
        scale_factor, unit_identifier = unit_scale_data.GetUnitScale()
        return scale_factor, unit_identifier
    else:
        return None

def get_abc_import_scale_factor():
    abc_import_id = c4d.FORMAT_ABCIMPORT
    prefs = c4d.plugins.GetWorldPluginData(abc_import_id)

    if prefs is None:
        print("No global plugin data found for Alembic Importer.")
        return None

    unit_scale_data = prefs[1010]

    if unit_scale_data:
        scale_factor, unit_identifier = unit_scale_data.GetUnitScale()
        return scale_factor, unit_identifier
    else:
        print("Scale factor data not found in Alembic Importer preferences.")
        return None
    
def calculate_scale_factor_to_meters(scale_factor, unit_identifier):
    # Dictionary to convert scale factor from various units to meters
    unit_to_meter_conversion = {
        c4d.PREF_UNITS_BASIC_KM: 1000,
        c4d.PREF_UNITS_BASIC_M: 1,
        c4d.PREF_UNITS_BASIC_CM: 0.01,
        c4d.PREF_UNITS_BASIC_MM: 0.001,
        c4d.PREF_UNITS_BASIC_MICRO: 1e-6,
        c4d.PREF_UNITS_BASIC_NM: 1e-9,
        c4d.PREF_UNITS_BASIC_MILE: 1609.34,
        c4d.PREF_UNITS_BASIC_YARD: 0.9144,
        c4d.PREF_UNITS_BASIC_FOOT: 0.3048,
        c4d.PREF_UNITS_BASIC_INCH: 0.0254,
    }
    
    meter_conversion = unit_to_meter_conversion.get(unit_identifier, None)
    if meter_conversion is not None:
        adjusted_scale_factor = scale_factor * meter_conversion
        return adjusted_scale_factor
    else:
        print("Unknown unit identifier, cannot calculate scale factor to meters.")
        return None

def adjust_object_scale(obj, scale_factor, is_camera=False):
    """Scales an object or a camera's position by a given factor."""
    mg = obj.GetMg()  # Get the current global matrix
    
    if is_camera:
        # For cameras, only adjust the position
        mg.off /= scale_factor
    else:
        # For other objects, scale the entire matrix
        mg.v1 /= scale_factor  # Scale X axis
        mg.v2 /= scale_factor  # Scale Y axis
        mg.v3 /= scale_factor  # Scale Z axis
        mg.off /= scale_factor  # Scale position
    
    obj.SetMg(mg)  # Update the object with the modified matrix

def process_import(doc, file_path, default_name, is_camera=False):
    # Attempt to retrieve the scale factor based on OBJ import settings
    scale_factor, unit_identifier = get_obj_import_scale_factor()
    adjusted_scale_factor = calculate_scale_factor_to_meters(scale_factor, unit_identifier) if scale_factor else 1

    if os.path.isfile(file_path):
        objects_before_import = set(doc.GetObjects())
        if c4d.documents.MergeDocument(doc, file_path, c4d.SCENEFILTER_OBJECTS | c4d.SCENEFILTER_MATERIALS):
            logger.info(f"Successfully imported: {file_path}")
            objects_after_import = set(doc.GetObjects())
            new_objects = objects_after_import - objects_before_import
        for obj in new_objects:
            obj.SetName(default_name)
            adjust_object_scale(obj, adjusted_scale_factor, is_camera)
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

def import_omni_file(doc, file_path):
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

def main(doc):
    file_path = c4d.storage.LoadDialog(title="Select .omni File", flags=c4d.FILESELECT_LOAD, force_suffix="omni")
    if file_path:
        import_omni_file(doc, file_path)
    else:
        print("No file selected.")