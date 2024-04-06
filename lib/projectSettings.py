import c4d
from videoBackground import get_movie_info

def set_project_settings_from_video(doc, video_path):
    """
    Sets the document's project settings based on the given video file.

    Parameters:
    - doc: The Cinema 4D document to set the project settings for.
    - video_path: The path to the video file.

    Returns:
    - True if the settings were successfully applied, False otherwise.
    """
    movie_info = get_movie_info(video_path)
    if not movie_info:
        print(f"Failed to open video file: {video_path}")
        return False

    frame_count, fps = movie_info
    fps_int = int(round(fps))

    start_frame = c4d.BaseTime(1, fps_int)
    end_frame = c4d.BaseTime(frame_count, fps_int) 

    doc.SetFps(fps_int)
    doc.SetLoopMinTime(start_frame)
    doc.SetLoopMaxTime(end_frame)
    doc.SetMinTime(start_frame)
    doc.SetMaxTime(end_frame)
    doc.SetTime(start_frame)

    c4d.EventAdd()

    return True
