import datetime,time

class OveMeta:
    def __init__(self, name: str = "", description: str = "", uploaded: bool = False, permissions: str = "", history: list = []):
        self.name = name
        self.description = description
        self.uploaded = uploaded
        self.permissions = permissions
        self.history = history

    def update(self):
        self.history.append("Updated at: " + str(datetime.datetime.today()))

    def created(self):
        self.history.insert(0, "Created at: " + str(datetime.datetime.today()))


# Sanitizes meta files
class OvePublicMeta():
    def __init__(self,OveMeta):
        self.name = OveMeta.name
        self.description = OveMeta.description
        self.history = OveMeta.history
