import c4d
from c4d import plugins

class OmniscientSceneControl(plugins.TagData):
    def Init(self, node, isCloneInit=False):
        node[c4d.OMNISCIENTSCENECONTROL_BACKGROUND_VISIBILITY] = c4d.OMNISCIENTSCENECONTROL_VIEW_THROUGH_CAMERA
        node[c4d.OMNISCIENTSCENECONTROL_SAFE_FRAME_VISIBILITY] = c4d.OMNISCIENTSCENECONTROL_VIEW_THROUGH_CAMERA
        node[c4d.OMNISCIENTSCENECONTROL_VIEWPORT_GRID_VISIBILITY] = c4d.OMNISCIENTSCENECONTROL_ONLY_NOT_THROUGH_CAM
        return True

    def apply_visibility_setting(self, doc, user_setting, base_draw, c4d_attributes, viewing_through_camera, obj=None):
        changed = False
        visibility_state_map = {
            c4d.OMNISCIENTSCENECONTROL_VIEW_THROUGH_CAMERA: viewing_through_camera,
            c4d.OMNISCIENTSCENECONTROL_ALWAYS: True,
            c4d.OMNISCIENTSCENECONTROL_NEVER: False,
            c4d.OMNISCIENTSCENECONTROL_ONLY_NOT_THROUGH_CAM: not viewing_through_camera,
        }
        visibility_state = visibility_state_map.get(user_setting, True)

        if obj:
            desired_mode = c4d.MODE_ON if visibility_state else c4d.MODE_OFF
            # Only set when changed to avoid triggering unnecessary updates
            if obj[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] != desired_mode:
                obj[c4d.ID_BASEOBJECT_VISIBILITY_EDITOR] = desired_mode
                changed = True
            if obj[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] != desired_mode:
                obj[c4d.ID_BASEOBJECT_VISIBILITY_RENDER] = desired_mode
                changed = True
        elif base_draw and c4d_attributes:
            desired_mode = c4d.MODE_OFF if visibility_state else c4d.MODE_ON
            for attr in c4d_attributes:
                if attr is None:
                    continue
                current = base_draw[attr]
                if current in (True, 1, c4d.MODE_ON):
                    current_mode = c4d.MODE_ON
                elif current in (False, 0, c4d.MODE_OFF):
                    current_mode = c4d.MODE_OFF
                else:
                    current_mode = c4d.MODE_UNDEF

                if current_mode != desired_mode:
                    base_draw[attr] = desired_mode
                    changed = True

        return changed

    def Execute(self, tag, doc, op, bt, priority, flags):
        if not tag:
            return False

        # Check if the tag's host object is either an Alembic Generator or a Cinema 4D camera
        # Only operate when this tag is on the active camera (or its Alembic parent)
        is_camera_host = op.GetType() in [1028083, 5103]  # Alembic Generator or Cinema 4D camera

        bd = doc.GetActiveBaseDraw()
        if not bd:
            return True

        scene_cam = bd.GetSceneCamera(doc) or bd.GetEditorCamera()
        viewing_through_this = is_camera_host and (
            op == scene_cam or (op.GetDown() and op.GetDown() == scene_cam)
        )

        # Retrieve user preferences for viewport grid, background, and safe frame visibility
        background_visibility_setting = tag[c4d.OMNISCIENTSCENECONTROL_BACKGROUND_VISIBILITY]
        safe_frame_visibility_setting = tag[c4d.OMNISCIENTSCENECONTROL_SAFE_FRAME_VISIBILITY]
        viewport_grid_visibility_setting = tag[c4d.OMNISCIENTSCENECONTROL_VIEWPORT_GRID_VISIBILITY]

        # Always control the background object visibility, even for non-active cameras
        background_object = tag[c4d.OMNISCIENTSCENECONTROL_BACKGROUND_LINK]
        any_changes = False
        if background_object:
            any_changes = self.apply_visibility_setting(
                doc,
                background_visibility_setting,
                None,
                None,
                viewing_through_this,
                background_object,
            )

        # Decide if we should write BaseDraw (global) settings:
        # - When viewing through a tagged camera: only the active camera's tag writes them.
        # - When using the Editor Camera: allow tags to write their "not through" settings
        using_editor_cam = (scene_cam == bd.GetEditorCamera())
        should_write_bd = viewing_through_this or using_editor_cam

        if should_write_bd:
            # Control the viewport grid, world axis, and horizon visibility
            grid_changed = self.apply_visibility_setting(
                doc,
                viewport_grid_visibility_setting,
                bd,
                [
                    c4d.BASEDRAW_DISPLAYFILTER_GRID,
                    c4d.BASEDRAW_DISPLAYFILTER_WORLDAXIS,
                    c4d.BASEDRAW_DISPLAYFILTER_HORIZON,
                ],
                viewing_through_this,
            )

            # Control the safe frame visibility
            safe_changed = self.apply_visibility_setting(
                doc,
                safe_frame_visibility_setting,
                bd,
                [c4d.BASEDRAW_DATA_SHOWSAFEFRAME],
                viewing_through_this,
            )
            any_changes = any_changes or grid_changed or safe_changed

        if any_changes:
            c4d.EventAdd()
        return True
