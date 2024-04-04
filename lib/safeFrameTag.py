import c4d
from c4d import plugins

class SafeFrameTag(plugins.TagData):
    def Init(self, node):
        # Define a boolean user data to toggle the safe frame display
        bc = c4d.GetCustomDataTypeDefault(c4d.DTYPE_BOOL)
        bc[c4d.DESC_NAME] = "Show Safe Frame"
        userDataId = 1
        node.AddUserData(bc)
        node[c4d.ID_USERDATA, userDataId] = True  # Set the default state to True (show safe frame)
        return True

    def Execute(self, tag, doc, op, bt, priority, flags):
        # Check if the tag's host object is either an Alembic Generator or a Cinema 4D camera
        isCamera = op.GetType() in [1028083, 5103]  # IDs for Alembic Generator and Cinema 4D camera

        # Get the active base draw and the currently active camera in the viewport
        bd = doc.GetActiveBaseDraw()
        if not bd:
            return True  # Early exit if there's no base draw available

        activeCamera = bd.GetSceneCamera(doc) if bd.GetSceneCamera(doc) else bd.GetEditorCamera()

        # Determine if we're viewing through this camera
        viewingThroughThisCamera = isCamera and (op == activeCamera or (op.GetDown() and op.GetDown() == activeCamera))

        # Retrieve user preference for showing the safe frame
        userDataId = 1
        showSafeFrame = tag[c4d.ID_USERDATA, userDataId]

        # Control the safe frame display based on whether we're viewing through this camera and user preference
        if viewingThroughThisCamera and showSafeFrame:
            # Only enable the safe frame if the user setting is True and we're viewing through this camera
            bd[c4d.BASEDRAW_DATA_SHOWSAFEFRAME] = True
        else:
            # Otherwise disable safe frame
            bd[c4d.BASEDRAW_DATA_SHOWSAFEFRAME] = False

        # Update the scene to reflect the change
        c4d.EventAdd() 

        return True