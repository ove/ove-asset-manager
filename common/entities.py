import datetime
from enum import Enum
from typing import Dict

from common.util import append_slash, to_bool


class OveProjectMeta:
    EDITABLE_FIELDS = ["name", "description", "tags", "authors", "publications", "notes", "thumbnail", "controller",
                       "video_controller", "html_controller", "default_mode", "versions", "presenter_notes"]

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", "") or ""
        self.name = kwargs.get("name", "") or ""
        self.description = kwargs.get("description", "") or ""
        self.authors = kwargs.get("authors", "") or ""
        self.publications = kwargs.get("publications", "") or ""
        self.notes = kwargs.get("notes", "") or ""
        self.thumbnail = kwargs.get("thumbnail", "") or ""
        self.controller = kwargs.get("controller", "") or ""
        self.video_controller = to_bool(kwargs.get("video_controller", False) or False)
        self.html_controller = to_bool(kwargs.get("html_controller", False) or False)
        self.permissions = kwargs.get("permissions", "") or ""
        self.tags = kwargs.get("tags", []) or []
        self.url = kwargs.get("url", "") or ""
        self.default_mode = kwargs.get("default_mode", "") or ""
        self.versions = kwargs.get("versions", "") or ""
        self.presenter_notes = kwargs.get("presenter_notes", "") or ""

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
            "notes": self.notes,
            "thumbnail": self.thumbnail,
            "controller": self.controller,
            "video_controller": self.video_controller,
            "html_controller": self.html_controller,
            "tags": self.tags,
            "url": self.url,
            "default_mode": self.default_mode,
            "versions": self.versions,
            "presenter_notes": self.presenter_notes
        }


class OveProjectAccessMeta:
    def __init__(self, **kwargs):
        self.groups = kwargs.get("groups", []) or []

    def to_json(self) -> Dict:
        return self.__dict__

    def to_public_json(self):
        return {"groups": self.groups}


class OveAssetMeta:
    EDITABLE_FIELDS = ["name", "description", "tags"]

    def __init__(self, **kwargs):
        self.id = kwargs.get("id", "") or ""
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
        self.upload()
        self.version = int(self.history[-1]["Version"])

    def upload(self):
        self.history.append({
            "Type": "Updated",
            "Time": str(datetime.datetime.today()),
            "Version": len(self.history)
        })
        self.index_file = self.proxy_file_path
        self.processing_status = ""
        self.processing_error = ""

    def created(self):
        self.history = [{
            "Type": "Created",
            "Time": str(datetime.datetime.today()),
            "Version": 1}]
        self.index_file = self.proxy_file_path

    @property
    def worker_root(self):
        return str(self.proxy_url) + self.project + "/" + self.id + "/" + str(self.version) + "/"

    @property
    def file_location(self):
        return str(self.version) + "/" + self.filename

    @property
    def relative_file_path(self):
        return self.project + "/" + self.id + "/" + self.file_location

    @property
    def proxy_file_path(self):
        return self.proxy_url + self.relative_file_path

    def to_json(self) -> Dict:
        result = dict(self.__dict__)
        result["file_location"] = self.file_location
        return result

    def to_public_json(self):
        return {
            "id": self.id,
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
    ERROR = "error"

    def __str__(self):
        return self.value


class TaskStatus(Enum):
    NEW = "new"
    PROCESSING = "processing"
    CANCELED = "canceled"
    DONE = "done"
    ERROR = "error"

    def __str__(self):
        return self.value


class UserAccessMeta:
    EDITABLE_FIELDS = ["read_groups", "write_groups", "admin_access"]

    def __init__(self, **kwargs):
        self.user = kwargs.get("user", None)
        self.read_groups = kwargs.get("read_groups", []) or []
        self.write_groups = kwargs.get("write_groups", []) or []
        self.admin_access = kwargs.get("admin_access", False) or False

    def to_db(self) -> Dict:
        return {"user": self.user, "am": {"read_groups": self.read_groups, "write_groups": self.write_groups, "admin_access": self.admin_access}}

    def public_json(self) -> Dict:
        return {"user": self.user, "read_groups": self.read_groups, "write_groups": self.write_groups, "admin_access": self.admin_access}
