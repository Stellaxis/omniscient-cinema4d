import c4d
from c4d import plugins

class OmniscientSceneControl(plugins.TagData):
    def Init(self, node, isCloneInit=False):
        node[c4d.OMNISCIENTSCENECONTROL_BACKGROUND_VISIBILITY] = c4d.OMNISCIENTSCENECONTROL_VIEW_THROUGH_CAMERA
        node[c4d.OMNISCIENTSCENECONTROL_SAFE_FRAME_VISIBILITY] = c4d.OMNISCIENTSCENECONTROL_VIEW_THROUGH_CAMERA
        node[c4d.OMNISCIENTSCENECONTROL_VIEWPORT_GRID_VISIBILITY] = c4d.OMNISCIENTSCENECONTROL_ONLY_NOT_THROUGH_CAM
        return True

    def _is_ancestor(self, ancestor, node):
        while node:
            if node == ancestor:
                return True
            node = node.GetUp()
        return False

    def apply_visibility_setting(self, doc, user_setting, base_draw, c4d_attributes, viewing_through_camera, obj=None):
        changed = False
        visibility_state_map = {
            c4d.OMNISCIENTSCENECONTROL_VIEW_THROUGH_CAMERA: viewing_through_camera,
            c4d.OMNISCIENTSCENECONTROL_ALWAYS: True,
            c4d.OMNISCIENTSCENECONTROL_NEVER: False,
            c4d.OMNISCIENTSCENECONTROL_ONLY_NOT_THROUGH_CAM: not viewing_through_camera,
        }
        visibility_state = bool(visibility_state_map.get(user_setting, True))

        if obj:
            desired_mode = c4d.MODE_ON if visibility_state else c4d.MODE_OFF
            # Only set when changed to avoid triggering unnecessary updates
            if obj.GetEditorMode() != desired_mode:
                obj.SetEditorMode(desired_mode)
                changed = True
            if obj.GetRenderMode() != desired_mode:
                obj.SetRenderMode(desired_mode)
                changed = True
        elif base_draw and c4d_attributes:
            desired_bool = visibility_state
            for attr in c4d_attributes:
                if attr is None:
                    continue
                current = base_draw[attr]
                if current is None:
                    continue
                if bool(current) != desired_bool:
                    base_draw[attr] = desired_bool
                    changed = True

        return changed

    def Execute(self, tag, doc, op, bt, priority, flags):
        if not tag:
            return False

        # Prefer the render view when available; fall back to the active view.
        bd = doc.GetRenderBaseDraw() or doc.GetActiveBaseDraw()
        if not bd:
            return True

        has_scene_cam = bd.HasCameraLink()
        scene_cam = bd.GetSceneCamera(doc) if has_scene_cam else None
        using_editor_cam = not has_scene_cam

        is_active_tag_camera = False
        if has_scene_cam and scene_cam and op:
            if op == scene_cam or self._is_ancestor(op, scene_cam):
                is_active_tag_camera = True

        viewing_through_this = has_scene_cam and is_active_tag_camera
        should_write_bd = using_editor_cam or is_active_tag_camera

        # Retrieve user preferences for viewport grid, background, and safe frame visibility
        background_visibility_setting = tag[c4d.OMNISCIENTSCENECONTROL_BACKGROUND_VISIBILITY]
        safe_frame_visibility_setting = tag[c4d.OMNISCIENTSCENECONTROL_SAFE_FRAME_VISIBILITY]
        viewport_grid_visibility_setting = tag[c4d.OMNISCIENTSCENECONTROL_VIEWPORT_GRID_VISIBILITY]

        # Always control the background object visibility, even for non-active cameras
        background_object = tag[c4d.OMNISCIENTSCENECONTROL_BACKGROUND_LINK]
        any_changes = False
        if background_object:
            any_changes |= self.apply_visibility_setting(
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
        if should_write_bd:
            # Control the viewport grid, world axis, and horizon visibility
            grid_changed = self.apply_visibility_setting(
                doc,
                viewport_grid_visibility_setting,
                bd,
                [
                    c4d.BASEDRAW_DISPLAYFILTER_GRID,
                    c4d.BASEDRAW_DISPLAYFILTER_BASEGRID,
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

        return True
