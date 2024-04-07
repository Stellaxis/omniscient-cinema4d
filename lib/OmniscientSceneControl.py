import c4d
from c4d import plugins

class OmniscientSceneControl(plugins.TagData):
    def Init(self, node):
        node[c4d.OMNISCIENTSCENECONTROL_BACKGROUND_VISIBILITY] = c4d.OMNISCIENTSCENECONTROL_VIEW_THROUGH_CAMERA
        node[c4d.OMNISCIENTSCENECONTROL_SAFE_FRAME_VISIBILITY] = c4d.OMNISCIENTSCENECONTROL_VIEW_THROUGH_CAMERA
        node[c4d.OMNISCIENTSCENECONTROL_VIEWPORT_GRID_VISIBILITY] = c4d.OMNISCIENTSCENECONTROL_ONLY_NOT_THROUGH_CAM
        return True

    def apply_visibility_setting(self, doc, user_setting, base_draw, c4d_attributes, viewing_through_camera, obj=None):
        visibility_state_map = {
            c4d.OMNISCIENTSCENECONTROL_VIEW_THROUGH_CAMERA: viewing_through_camera,     # Through Camera
            c4d.OMNISCIENTSCENECONTROL_ALWAYS: True,                                    # Always
            c4d.OMNISCIENTSCENECONTROL_NEVER: False,                                    # Never
            c4d.OMNISCIENTSCENECONTROL_ONLY_NOT_THROUGH_CAM: not viewing_through_camera # Only When Not Viewing Through Camera
        }
        visibility_state = visibility_state_map.get(user_setting, True)

        visibility_mode = c4d.MODE_ON if visibility_state else c4d.MODE_OFF

        if obj:
            obj[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = visibility_mode
            obj[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = visibility_mode
        else:
            if base_draw and c4d_attributes:
                for attr in c4d_attributes:
                    if attr is not None:
                        base_draw[attr] = c4d.MODE_OFF if visibility_state else c4d.MODE_ON

    def Execute(self, tag, doc, op, bt, priority, flags):
        if not tag:
            return False

        # Check if the tag's host object is either an Alembic Generator or a Cinema 4D camera
        isCamera = op.GetType() in [1028083, 5103]  # IDs for Alembic Generator and Cinema 4D camera

        # Get the active base draw and the currently active camera in the viewport
        bd = doc.GetActiveBaseDraw()
        if not bd:
            return True  # Early exit if there's no base draw available

        activeCamera = bd.GetSceneCamera(doc) if bd.GetSceneCamera(doc) else bd.GetEditorCamera()
        viewingThroughThisCamera = isCamera and (op == activeCamera or (op.GetDown() and op.GetDown() == activeCamera))

        # Retrieve user preferences for viewport grid, background, and safe frame visibility
        background_visibility_setting = tag[c4d.OMNISCIENTSCENECONTROL_BACKGROUND_VISIBILITY]
        safe_frame_visibility_setting = tag[c4d.OMNISCIENTSCENECONTROL_SAFE_FRAME_VISIBILITY]
        viewport_grid_visibility_setting = tag[c4d.OMNISCIENTSCENECONTROL_VIEWPORT_GRID_VISIBILITY]

        # Control the viewport grid, world axis, and horizon visibility based on the user setting
        self.apply_visibility_setting(
            doc,
            viewport_grid_visibility_setting,
            bd,
            [c4d.BASEDRAW_DISPLAYFILTER_GRID, c4d.BASEDRAW_DISPLAYFILTER_WORLDAXIS, c4d.BASEDRAW_DISPLAYFILTER_HORIZON],
            viewingThroughThisCamera
        )
        # Control the background object visibility based on the user setting
        background_object = tag[c4d.OMNISCIENTSCENECONTROL_BACKGROUND_LINK]
        if background_object:
            self.apply_visibility_setting(
                doc,
                background_visibility_setting,
                None,
                None,
                viewingThroughThisCamera,
                background_object
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