import datetime
from enum import Enum
from typing import Dict


class OveMeta:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.description = kwargs.get("description", "")
        self.filename = kwargs.get("filename", "")
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
        self.index_file = self.proxy_url + self.name + "/" + str(self.version) + "/" + self.filename

    def upload(self):
        self.history.append({
            "Type": "Updated",
            "Time": str(datetime.datetime.today()),
            "Version": len(self.history)
        })
        self.index_file = self.proxy_url + self.name + "/" + str(self.version) + "/" + self.filename

    def created(self):
        self.history = [{
            "Type": "Created",
            "Time": str(datetime.datetime.today()),
            "Version": 1}]
        self.index_file = self.proxy_url + self.name + "/" + str(self.version) + "/" + self.filename

    @property
    def file_location(self):
        return str(self.history[-1]["Version"]) + "/" + self.filename

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


class WorkerData:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", None)
        self.extensions = kwargs.get("extensions", [])
        self.type = WorkerType(kwargs.get("type", None))
        self.description = kwargs.get("description", self.type.description)
        self.status = WorkerStatus(kwargs.get("status", None))
        self.callback = kwargs.get("callback", "")

    def __eq__(self, other):
        if isinstance(other, WorkerData):
            return self.name == other.name
        else:
            return self.name == str(other)

    def to_json(self):
        return {k: v if isinstance(v, list) else str(v) for k, v in self.__dict__.items()}

    def to_public_json(self):
        return {
            "name": self.name,
            "type": str(self.type),
            "description": self.description,
            "extensions": self.extensions,
            "status": str(self.status),
            "callback": self.callback
        }


class WorkerStatus(Enum):
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"

    def __str__(self):
        return self.value


class WorkerType(Enum):
    IMAGE = "image", "DZI image processor"
    ZIP = "zip", "Unzip processor"

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: str, description: str = None):
        self._description_ = description

    def __str__(self):
        return self.value

    @property
    def description(self):
        return self._description_
