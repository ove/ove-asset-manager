import datetime
from typing import Dict


class OveMeta:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("description", "")
        self.file_name = kwargs.get("index_file", "")
        self.proxy_url = kwargs.get("proxy_url", "")
        self.index_file = kwargs.get("index_file", "")
        self.uploaded = kwargs.get("uploaded", False)
        self.permissions = kwargs.get("permissions", "")
        self.history = kwargs.get("history", [{
            "Type": "Placeholder",
            "Time": str(datetime.datetime.today()),
            "Version": 1}])
        self.tags = kwargs.get("tags", [])
        self.version = kwargs.get("version", 1)

    def update(self):
        self.history.append({
            "Type": "Updated",
            "Time": str(datetime.datetime.today()),
            "Version": len(self.history)
        })
        self.version = int(self.history[-1]["Version"])
        self.index_file = self.proxy_url + self.name + "/" + str(self.version) + "/" + self.file_name

    def upload(self):
        self.history.append({
            "Type": "Updated",
            "Time": str(datetime.datetime.today()),
            "Version": len(self.history)
        })
        self.index_file = self.proxy_url + self.name + "/" + str(self.version) + "/" + self.file_name

    def created(self):
        self.history = [{
            "Type": "Created",
            "Time": str(datetime.datetime.today()),
            "Version": 1}]
        self.index_file = self.proxy_url + self.name + "/" + str(self.version) + "/" + self.file_name

    @property
    def file_location(self):
        return str(self.history[-1]["Version"]) + "/" + self.file_name

    def to_json(self) -> Dict:
        result = dict(self.__dict__)
        result["file_location"] = self.file_location
        return result

    def to_public_json(self):
        return {
            "name": self.name,
            "description": self.description,
            "index_file": self.index_file,
            "version": str(self.version),
            "history": self.history,
            "tags": self.tags
        }
