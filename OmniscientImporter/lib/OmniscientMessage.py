import c4d
import webbrowser

OMNISCIENT_DIALOG_EVENT_ID = 1063030

class DialogDataStorage:
    _instance = None
    title = ""
    message = ""
    update_url = ""

    @staticmethod
    def getInstance():
        if DialogDataStorage._instance is None:
            DialogDataStorage._instance = DialogDataStorage()
        return DialogDataStorage._instance

    def set_data(self, title, message, update_url=""):
        self.title = title
        self.message = message
        self.update_url = update_url

    def clear_data(self):
        self.title = ""
        self.message = ""
        self.update_url = ""

class OmniscientMessage(c4d.plugins.MessageData):
    def CoreMessage(self, id, bc):
        if id == OMNISCIENT_DIALOG_EVENT_ID:
            data_storage = DialogDataStorage.getInstance()
            title = data_storage.title
            message = data_storage.message
            update_url = data_storage.update_url
            
            dialog = CustomDialog(title, message, update_url)
            dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL, defaultw=400, defaulth=100)
            
            data_storage.clear_data()
            
        return True

class CustomDialog(c4d.gui.GeDialog):
    ID_BUTTON_OK = 1001
    ID_BUTTON_UPDATE = 1002

    def __init__(self, title, message, update_url=""):
        self.title = title
        self.message = message
        self.update_url = update_url

    def CreateLayout(self):
        self.SetTitle(self.title)
        
        if self.GroupBegin(0, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 1, 0, ""):
            self.GroupBorderSpace(10, 10, 10, 10)
            
            message_lines = self.message.split("|")
            for line in message_lines:
                self.AddStaticText(1000, c4d.BFH_SCALEFIT, name=line, borderstyle=c4d.BORDER_NONE)
            
            self.AddSeparatorH(c4d.gui.SizePix(5))
            
            if self.GroupBegin(0, c4d.BFH_CENTER, 2, 0, ""):
                self.GroupBorderSpace(0, 10, 0, 0)
                
                if self.update_url:
                    self.AddButton(self.ID_BUTTON_UPDATE, c4d.BFH_LEFT, name="Get the latest version")
                else:
                    self.AddButton(self.ID_BUTTON_OK, c4d.BFH_LEFT, name="OK")
                
            self.GroupEnd()  # Buttons group
        self.GroupEnd()  # Main group
        return True

    def Command(self, id, msg):
        if id == self.ID_BUTTON_OK:
            self.Close()
            return True
        elif id == self.ID_BUTTON_UPDATE and self.update_url:
            webbrowser.open(self.update_url)
            self.Close()
            return True
        return False
