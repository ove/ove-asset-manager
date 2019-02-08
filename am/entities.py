import datetime
from typing import Dict


class OveMeta:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("description", "")
        self.index_file = kwargs.get("index_file", "")
        self.uploaded = kwargs.get("uploaded", False)
        self.permissions = kwargs.get("permissions", "")
        self.history = kwargs.get("history", [])
        self.tags = kwargs.get("tags", [])

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

    @property
    def file_location(self):
        if len(self.history) is 0:
            return "None"
        else:
            return str(self.history[-1]["Version"]) + "/" + self.index_file

    def to_json(self) -> Dict:
        result = dict(self.__dict__)
        result["file_location"] = self.file_location
        return result

    def to_public_json(self):
        return {
            "name": self.name,
            "description": self.description,
            "index_file": self.index_file,
            "history": self.history,
            "tags": self.tags
        }
