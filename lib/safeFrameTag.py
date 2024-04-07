import c4d
from c4d import plugins

class SafeFrameTag(plugins.TagData):
    # Define constants for our cycle options
    VISIBILITY_OPTIONS = {
        0: "Through Camera",                      # Visible only when viewing through the camera
        1: "Always",                              # Always visible
        2: "Never" ,                              # Never visible
        3: "Only When Not Viewing Through Camera" # Visible only when not viewing through the camera
    }

    def Init(self, node):
        self.add_visibility_option(node, 1, "Background Visibility")
        self.add_visibility_option(node, 2, "Safe Frame Visibility")
        self.add_visibility_option(node, 3, "Viewport Grid Visibility", default=3)

        return True
    
    def add_visibility_option(self, node, id, name, default=0):
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_LONG)
        bc[c4d.DESC_NAME] = name
        
        cycle = c4d.BaseContainer()
        cycle[0] = "Viewing Through Camera"
        cycle[1] = "Always"
        cycle[2] = "Never"
        cycle[3] = "Only When Not Viewing Through Camera"
        bc[c4d.DESC_CYCLE] = cycle
        
        userData = node.AddUserData(bc)
        node[userData] = default

    def apply_visibility_setting(self, doc, user_setting, base_draw, c4d_attributes, viewing_through_camera, search_object_name=None):
        visibility_state_map = {
            0: viewing_through_camera,     # Through Camera
            1: True,                       # Always
            2: False,                      # Never
            3: not viewing_through_camera  # Only When Not Viewing Through Camera
        }
        visibility_state = visibility_state_map.get(user_setting, True)

        visibility_mode = c4d.MODE_ON if visibility_state else c4d.MODE_OFF

        if search_object_name:
            obj = doc.SearchObject(search_object_name)
            if obj:
                obj[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = visibility_mode
                obj[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = visibility_mode
        else:
            if base_draw and c4d_attributes:
                for attr in c4d_attributes:
                    if attr is not None:
                        base_draw[attr] = c4d.MODE_OFF if visibility_state else c4d.MODE_ON

    def Execute(self, tag, doc, op, bt, priority, flags):
        # Check if the tag's host object is either an Alembic Generator or a Cinema 4D camera
        isCamera = op.GetType() in [1028083, 5103]  # IDs for Alembic Generator and Cinema 4D camera

        # Get the active base draw and the currently active camera in the viewport
        bd = doc.GetActiveBaseDraw()
        if not bd:
            return True  # Early exit if there's no base draw available

        activeCamera = bd.GetSceneCamera(doc) if bd.GetSceneCamera(doc) else bd.GetEditorCamera()
        viewingThroughThisCamera = isCamera and (op == activeCamera or (op.GetDown() and op.GetDown() == activeCamera))

        # Retrieve user preferences for viewport grid, background, and safe frame visibility
        background_visibility_setting = tag[c4d.ID_USERDATA, 1]
        safe_frame_visibility_setting = tag[c4d.ID_USERDATA, 2]
        viewport_grid_visibility_setting = tag[c4d.ID_USERDATA, 3]

        # Control the viewport grid, world axis, and horizon visibility based on the user setting
        self.apply_visibility_setting(
            doc,
            viewport_grid_visibility_setting,
            bd,
            [c4d.BASEDRAW_DISPLAYFILTER_GRID, c4d.BASEDRAW_DISPLAYFILTER_WORLDAXIS, c4d.BASEDRAW_DISPLAYFILTER_HORIZON],
            viewingThroughThisCamera
        )
        # Control the background object visibility based on the user setting
        self.apply_visibility_setting(
            doc,
            background_visibility_setting,
            None,
            None,
            viewingThroughThisCamera,
            search_object_name='Omni_Background'
        )
        # Control the safe frame visibility based on the user setting
        self.apply_visibility_setting(
            doc,
            safe_frame_visibility_setting,
            bd,
            [c4d.BASEDRAW_DATA_SHOWSAFEFRAME],
            viewingThroughThisCamera
        )

        c4d.EventAdd() 
        return True