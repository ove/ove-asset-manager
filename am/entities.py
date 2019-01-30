import datetime


class OveMeta:
    def __init__(self, name: str = "", description: str = "", uploaded: bool = False, permissions: str = "", history: list = [], indexfile: str = ""):
        self.name = name
        self.description = description
        self.indexfile = indexfile
        self.uploaded = uploaded
        self.permissions = permissions
        self.history = history
        self.filelocation = self.filelocation()

    def update(self):
        self.history.append({
            "Type": "Updated",
            "Time": str(datetime.datetime.today()),
            "Version": len(self.history)
        })

    def created(self):
        if len(self.history) is 0:
            self.history.append({
                "Type": "Created",
                "Time": str(datetime.datetime.today()),
                "Version": 1})
        else:
            self.history.insert(0, {
                "Type": "Created",
                "Time": str(datetime.datetime.today()),
                "Version": 1})

    def filelocation(self):
        if len(self.history) is 0:
            return "None"
        else:
            return str(self.history[-1]["Version"]) + '/' + self.indexfile


# Sanitizes meta files
class OvePublicMeta():
    def __init__(self, OveMeta):
        self.name = OveMeta.name
        self.description = OveMeta.description
        self.indexfile = OveMeta.indexfile
        self.history = OveMeta.history
        self.filelocation = self.filelocation()

    def filelocation(self):
        if len(self.history) is 0:
            return "None"
        else:
            return str(self.history[-1]["Version"]) + '/' + self.indexfile


# potential to create an OveHistory class instead
# class OveHistory():
#     def __init__(self, detail: str = "", version: int = 0):
#         self.detail = detail
#         self.time = str(datetime.datetime.today())
#         self.version = version
#
#     def __str__(self):
#         return "Version number: " + self.version + " was " + self.detail + " at: " + self.time
#
#     def jsonify(self):
#         return self.__dict__
