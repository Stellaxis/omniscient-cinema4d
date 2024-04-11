import c4d

def CreateKey(doc, curve, time, value, interpolation=c4d.CINTERPOLATION_LINEAR):
    """Creates a Key on the given curve at the given time with a given value and with the given interpolation."""
    keyDict = curve.AddKey(time)
    if keyDict is None:
        raise MemoryError("Failed to create a key")
    key = keyDict["key"]
    keyIndex = keyDict["nidx"]
    key.SetValue(curve, value)
    curve.SetKeyDefault(doc, keyIndex)
    key.SetInterpolation(curve, interpolation)
    return key, keyIndex

def set_camera_properties(new_camera, alembic_camera):
    """Sets the properties of the new camera based on the Alembic camera."""
    def get_property(container, primary_id, secondary_id, property_id):
        try:
            # Try primary ID first
            return container[1028637, primary_id, property_id]
        except:
            # Fallback to secondary ID
            return container[1028637, secondary_id, property_id]

    # Focal Length
    focal_length = get_property(alembic_camera, 1057516, 5103, 500)
    new_camera[c4d.CAMERA_FOCUS] = focal_length

    # Sensor Size (Aperture)
    sensor_size_width = get_property(alembic_camera, 1057516, 5103, 1006)
    new_camera[c4d.CAMERAOBJECT_APERTURE] = sensor_size_width

    # Film Offset
    film_offset_x = get_property(alembic_camera, 1057516, 5103, 1118)
    film_offset_y = get_property(alembic_camera, 1057516, 5103, 1119)

    new_camera[c4d.CAMERAOBJECT_FILM_OFFSET_X] = film_offset_x
    new_camera[c4d.CAMERAOBJECT_FILM_OFFSET_Y] = film_offset_y

    # Projection Type
    projection_id = get_property(alembic_camera, 1057516, 5103, 1001)
    new_camera[c4d.CAMERA_PROJECTION] = projection_id

def bake_alembic_camera_animation(doc, alembic_camera):
    if alembic_camera.GetType() != 1028083:
        raise ValueError('Selected object is not an Alembic camera.')
    
    original_time = doc.GetTime()
    
    new_camera = c4d.BaseObject(c4d.Ocamera)
    new_camera.SetName(alembic_camera.GetName())

    set_camera_properties(new_camera, alembic_camera)

    doc.InsertObject(new_camera)
    doc.StartUndo()
    doc.AddUndo(c4d.UNDOTYPE_NEW, new_camera)
    startFrame = doc.GetMinTime().GetFrame(doc.GetFps())
    endFrame = doc.GetMaxTime().GetFrame(doc.GetFps())
    tracks = {}
    for frame in range(startFrame, endFrame + 1):
        time = c4d.BaseTime(frame, doc.GetFps())
        doc.SetTime(time)
        doc.ExecutePasses(None, True, True, True, c4d.BUILDFLAGS_NONE)
        new_camera.SetMg(alembic_camera.GetMg())
        for descId, value in [(c4d.ID_BASEOBJECT_POSITION, alembic_camera.GetMg().off),
                              (c4d.ID_BASEOBJECT_ROTATION, c4d.utils.MatrixToHPB(alembic_camera.GetMg()))]:
            for i, component in enumerate("xyz"):
                vector_id = c4d.DescLevel(descId, c4d.DTYPE_VECTOR, 0)
                real_id = c4d.DescLevel(i+1000, c4d.DTYPE_REAL, 0)
                trackId = c4d.DescID(vector_id, real_id)
                key = (descId, i)
                if key not in tracks:
                    track = c4d.CTrack(new_camera, trackId)
                    new_camera.InsertTrackSorted(track)
                    tracks[key] = track.GetCurve()
                curve = tracks[key]
                CreateKey(doc, curve, time, value[i])
    doc.EndUndo()
    
    # Reset the timeline to its original position
    doc.SetTime(original_time)
    c4d.EventAdd()
    
    return new_camera