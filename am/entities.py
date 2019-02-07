import datetime


class OveMeta:
    def __init__(self, name: str = "", description: str = "", uploaded: bool = False, permissions: str = "", history=None, index_file: str = ""):
        if history is None:
            history = []

        self.name = name
        self.description = description
        self.index_file = index_file
        self.uploaded = uploaded
        self.permissions = permissions
        self.history = history
        self.file_location = self.file_location()

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

    def file_location(self):
        if len(self.history) is 0:
            return "None"
        else:
            return str(self.history[-1]["Version"]) + '/' + self.index_file


# Sanitizes meta files
class OvePublicMeta:
    def __init__(self, meta: OveMeta):
        self.name = meta.name
        self.description = meta.description
        self.index_file = meta.index_file
        self.history = meta.history
        self.file_location = self.file_location()

    def file_location(self):
        if len(self.history) is 0:
            return "None"
        else:
            return str(self.history[-1]["Version"]) + '/' + self.index_file

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
