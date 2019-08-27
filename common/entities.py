import datetime
from enum import Enum
from typing import Dict

from common.util import append_slash


class OveProjectMeta:
    EDITABLE_FIELDS = ['name', 'description', 'tags', 'authors', 'publications', 'thumbnail', 'controller']

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", "") or ""
        self.name = kwargs.get("name", "") or ""
        self.description = kwargs.get("description", "") or ""
        self.authors = kwargs.get("authors", "") or ""
        self.publications = kwargs.get("publications", "") or ""
        self.thumbnail = kwargs.get("thumbnail", "") or ""
        self.controller = kwargs.get("controller", "") or ""
        self.permissions = kwargs.get("permissions", "") or ""
        self.tags = kwargs.get("tags", []) or []
        self.url = kwargs.get("url", "") or ""

    def to_json(self) -> Dict:
        result = dict(self.__dict__)
        del result["url"]
        return result

    def to_public_json(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "authors": self.authors,
            "publications": self.publications,
            "thumbnail": self.thumbnail,
            "controller": self.controller,
            "tags": self.tags,
            "url": self.url,
        }


class OveAssetMeta:
    EDITABLE_FIELDS = ['description', 'tags']

    def __init__(self, **kwargs):
        self.name = kwargs.get("name", "") or ""
        self.project = kwargs.get("project", "") or ""
        self.description = kwargs.get("description", "") or ""
        self.filename = kwargs.get("filename", "") or ""
        self.proxy_url = append_slash(kwargs.get("proxy_url", "")) or ""
        self.index_file = kwargs.get("index_file", "") or ""
        self.uploaded = kwargs.get("uploaded", False) or ""
        self.permissions = kwargs.get("permissions", "") or ""
        self.history = kwargs.get("history", [{
            "Type": "Placeholder",
            "Time": str(datetime.datetime.today()),
            "Version": 1}]) or []
        self.tags = kwargs.get("tags", []) or []
        self.version = kwargs.get("version", 1) or 1
        self.worker = kwargs.get("worker", "") or ""
        self.processing_status = kwargs.get("processing_status", "") or ""
        self.processing_error = kwargs.get("processing_error", "") or ""

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
    def worker_root(self):
        return str(self.proxy_url) + self.project + "/" + self.name + "/" + str(self.version) + "/"

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
            "tags": self.tags,
            "worker": self.worker,
            "processing_status": self.processing_status,
            "processing_error": self.processing_error
        }


class WorkerData:
    def __init__(self, **kwargs):
        self.name = kwargs.get("name", None)
        self.extensions = kwargs.get("extensions", [])
        # workers are not restricted to WorkerTypes
        self.type = kwargs.get("type", None)
        self.description = kwargs.get("description", "")
        self.status = WorkerStatus(kwargs.get("status", None))
        self.error_msg = kwargs.get("error_msg", None)
        self.callback = kwargs.get("callback", "")
        self.status_callback = kwargs.get("status_callback", "")
        self.parameters = kwargs.get("parameters", {})
        self.docs = kwargs.get("docs", "")

    def __eq__(self, other):
        if isinstance(other, WorkerData):
            return self.name == other.name
        else:
            return self.name == str(other)

    def to_json(self):
        return {k: v if isinstance(v, (list, dict)) else str(v) for k, v in self.__dict__.items()}

    def to_public_json(self):
        return {
            "name": self.name,
            "type": str(self.type),
            "description": self.description,
            "extensions": self.extensions,
            "status": str(self.status),
            "callback": self.callback,
            "status_callback": self.status_callback,
            "parameters": self.parameters,
            "docs": self.docs
        }


class WorkerStatus(Enum):
    READY = "ready"
    PROCESSING = "processing"
    DONE = "done"
    ERROR = "error"

    def __str__(self):
        return self.value


# Provided for convenience
class WorkerType(Enum):
    DZ_IMAGE = "dz-image"
    EXTRACT = "extract"
    TULIP = "tulip"

    def __str__(self):
        return self.value
