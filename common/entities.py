import datetime
from enum import Enum
from typing import Dict

from common.util import append_slash


class OveMeta:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "")
        self.project = kwargs.get("project", "")
        self.description = kwargs.get("description", "")
        self.filename = kwargs.get("filename", "")
        self.proxy_url = append_slash(kwargs.get("proxy_url", ""))
        self.index_file = kwargs.get("index_file", "")
        self.uploaded = kwargs.get("uploaded", False)
        self.permissions = kwargs.get("permissions", "")
        self.history = kwargs.get("history", [{
            "Type": "Placeholder",
            "Time": str(datetime.datetime.today()),
            "Version": 1}])
        self.tags = kwargs.get("tags", [])
        self.version = kwargs.get("version", 1)
        self.worker = kwargs.get("worker", "")

    def update(self):
        self.history.append({
            "Type": "Updated",
            "Time": str(datetime.datetime.today()),
            "Version": len(self.history)
        })
        self.version = int(self.history[-1]["Version"])
        self.index_file = self.proxy_file_path

    def upload(self):
        self.history.append({
            "Type": "Updated",
            "Time": str(datetime.datetime.today()),
            "Version": len(self.history)
        })
        self.index_file = self.proxy_file_path

    def created(self):
        self.history = [{
            "Type": "Created",
            "Time": str(datetime.datetime.today()),
            "Version": 1}]
        self.index_file = self.proxy_file_path

    @property
    def file_location(self):
        return str(self.version) + "/" + self.filename

    @property
    def relative_file_path(self):
        return self.project + "/" + self.name + "/" + self.file_location

    @property
    def proxy_file_path(self):
        return self.proxy_url + self.relative_file_path

    def to_json(self) -> Dict:
        result = dict(self.__dict__)
        result["file_location"] = self.file_location
        return result

    def to_public_json(self):
        return {
            "name": self.name,
            "project": self.project,
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
        # workers are not restricted to WorkerTypes
        self.type = kwargs.get("type", None)
        self.description = kwargs.get("description", "")
        self.status = WorkerStatus(kwargs.get("status", None))
        self.callback = kwargs.get("callback", "")
        self.status_callback = kwargs.get("status_callback", "")

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
            "callback": self.callback,
            "status_callback": self.status_callback
        }


class WorkerStatus(Enum):
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"

    def __str__(self):
        return self.value


# Provided for convenience
class WorkerType(Enum):
    DZ_IMAGE = "dz-image"
    EXTRACT = "extract"

    def __str__(self):
        return self.value
