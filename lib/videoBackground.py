import c4d
import os

def get_movie_info(video_path: str):
    """
    Uses Cinema 4D's MovieLoader to get frame count and fps of a movie file.
    
    Parameters:
    - video_path: The path to the video file.
    
    Returns:
    - Tuple of frame count and fps if successful, None otherwise.
    """
    ml = c4d.bitmaps.MovieLoader()
    if not ml.Open(video_path):
        print(f"Failed to open video file: {video_path}")
        return None
    
    frame_count, fps = ml.GetInfo()
    ml.Close()
    return frame_count, fps

def calculate_and_set_frame_range(shader: c4d.BaseShader, video_path: str, doc: c4d.documents.BaseDocument):
    """
    Calculates and sets the frame range for the video texture shader based on the actual video file.
    
    Parameters:
    - shader: The shader to set frame range for.
    - video_path: The path to the video file.
    - doc: The active Cinema 4D document.
    """
    movie_info = get_movie_info(video_path)
    if not movie_info:
        print("Unable to get movie info.")
        return

    frame_count, fps = movie_info

    # Set the timing mode to 'Range'
    shader[c4d.BITMAPSHADER_TIMING_MODE] = c4d.BITMAPSHADER_TIMING_MODE_SIMPLE
    shader[c4d.BITMAPSHADER_TIMING_TIMING] = c4d.BITMAPSHADER_TIMING_TIMING_AREA

    # Set the start and end frame.
    start_frame = 1
    end_frame = frame_count

    shader[c4d.BITMAPSHADER_TIMING_RANGEFROM] = c4d.BaseTime(start_frame, fps)
    shader[c4d.BITMAPSHADER_TIMING_RANGETO] = c4d.BaseTime(end_frame, fps)

    # Set the movie start frame and end frame
    shader[c4d.BITMAPSHADER_TIMING_FROM] = 0
    shader[c4d.BITMAPSHADER_TIMING_TO] = frame_count - 1

    # Set the shader fps to match the video fps
    shader[c4d.BITMAPSHADER_TIMING_FPS] = fps

def create_background_with_video_material(doc, video_path: str):
    # First, create the video material
    material = create_video_material(video_path, doc)
    if material is None:
        logger.error("Failed to create material from video.")
        return False

    # Now create the background object and apply the material
    background = c4d.BaseObject(c4d.Obackground)
    if not background:
        logger.error("Failed to create a new background object.")
        return False

    textureTag = c4d.TextureTag()
    if not textureTag:
        logger.error("Failed to create a new texture tag.")
        return False

    textureTag.SetMaterial(material)
    textureTag[c4d.TEXTURETAG_PROJECTION] = c4d.TEXTURETAG_PROJECTION_FRONTAL
    background.InsertTag(textureTag)
    doc.InsertObject(background)
    c4d.EventAdd()

    return True

def create_video_material(video_path: str, doc: c4d.documents.BaseDocument):
    video_filename = os.path.basename(video_path)
    material_name = f"Omni_{video_filename}"

    mat = c4d.BaseMaterial(c4d.Mmaterial)
    if not mat:
        print("Failed to create a new material.")
        return None

    mat.SetName(material_name)
    mat[c4d.MATERIAL_USE_COLOR] = False
    mat[c4d.MATERIAL_USE_REFLECTION] = False
    mat[c4d.MATERIAL_USE_LUMINANCE] = True

    shader = c4d.BaseShader(c4d.Xbitmap)
    if not shader:
        print("Failed to create a shader.")
        return None
    shader[c4d.BITMAPSHADER_FILENAME] = video_path
    shader[c4d.BITMAPSHADER_COLORPROFILE] = c4d.BITMAPSHADER_COLORPROFILE_SRGB

    # Additional shader settings for timing
    calculate_and_set_frame_range(shader, video_path, doc)

    mat.InsertShader(shader)
    mat[c4d.MATERIAL_LUMINANCE_SHADER] = shader

    mat[c4d.MATERIAL_PREVIEWSIZE] = c4d.MATERIAL_PREVIEWSIZE_512
    mat[c4d.MATERIAL_ANIMATEPREVIEW] = True

    mat.SetParameter(c4d.MATERIAL_GLOBALILLUM_GENERATE, False, c4d.DESCFLAGS_SET_0)
    mat.SetParameter(c4d.MATERIAL_GLOBALILLUM_RECEIVE, False, c4d.DESCFLAGS_SET_0)
    mat.SetParameter(c4d.MATERIAL_CAUSTICS_GENERATE, False, c4d.DESCFLAGS_SET_0)
    mat.SetParameter(c4d.MATERIAL_CAUSTICS_RECEIVE, False, c4d.DESCFLAGS_SET_0)

    doc.InsertMaterial(mat)
    c4d.EventAdd()

    return mat