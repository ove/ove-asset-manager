import json
from os.path import basename
from typing import Dict, List, Any, Union

from ui.backend import BackendClient

_RESERVED_NAMES = {"list", "validate", "create"}


class BackendController:
    def __init__(self, backend_url: str):
        self._backend = BackendClient(backend_url=backend_url)

    def list_workers(self) -> List:
        return self._backend.get("api/workers") or []

    def get_worker_types(self) -> List:
        return list({w['type']: {
            'type': w['type'],
            'extensions': w['extensions'],
            'description': w['description'],
            'parameters': json.dumps(w['parameters']),
            'docs': w.get('docs', '')
        } for w in self.list_workers()}.values())

    def edit_worker(self, action: str, name: str) -> None:
        if action == "reset":
            self._backend.post("api/workers/status", data={"name": name})
        elif action == "delete":
            self._backend.delete("api/workers", data={"name": name})

    def list_stores(self) -> List:
        return self._backend.get("api/list") or []

    def list_projects(self, store_name: str) -> List:
        return self._backend.get("api/{}/list".format(store_name), params={"metadata": True})

    def create_project(self, store_name: str, project_name: str) -> None:
        self._backend.post("api/{}/create".format(store_name), data={"name": project_name})

    def get_project(self, store_name: str, project_name: str) -> Dict:
        return self._backend.get("/api/{}/{}/projectMeta".format(store_name, project_name))

    def edit_project(self, store_name: str, project_name: str, project_data: Dict) -> Dict:
        return self._backend.post("/api/{}/{}/projectMeta".format(store_name, project_name), data=project_data)

    def list_assets(self, store_name: str, project_name: str) -> List:
        return [_mutate(d, "short_index", basename(d.get("index_file", ""))) for d in self._backend.get("api/{}/{}/list".format(store_name, project_name))]

    def list_files(self, store_name: str, project_name: str, asset_name: str, hierarchical: bool = False) -> List[Dict]:
        files = self._backend.get("api/{}/{}/files/{}".format(store_name, project_name, asset_name))

        if hierarchical:
            file_tree = []
            if files:
                for file in files:
                    _add_item(item=file["name"], url=file["url"], node_type="leaf", results=file_tree)
            return file_tree
        else:
            return files

    def get_asset(self, store_name: str, project_name: str, asset_name: str) -> Dict:
        return self._backend.get("api/{}/{}/meta/{}".format(store_name, project_name, asset_name))

    def create_asset(self, store_name: str, project_name: str, asset: Dict) -> Dict:
        self._backend.post("api/{}/{}/create".format(store_name, project_name), data=asset)
        return self.get_asset(store_name=store_name, project_name=project_name, asset_name=asset.get("name", ""))

    def edit_asset(self, store_name: str, project_name: str, asset: Dict) -> Dict:
        return self._backend.post("/api/{}/{}/meta/{}".format(store_name, project_name, asset.get("name", "")), data=asset)

    def upload_asset(self, store_name: str, project_name: str, asset_name: str, filename: str, stream: Any, update: bool = False) -> None:
        if update:
            url = "api/{}/{}/update/{}".format(store_name, project_name, asset_name)
        else:
            url = "api/{}/{}/createUpload/{}".format(store_name, project_name, asset_name)

        headers = {"content-disposition": "filename='{}'".format(filename)}
        self._backend.upload(api_url=url, stream=stream, headers=headers)

    def schedule_worker(self, store_name: str, project_name: str, asset_name: str, worker_type: str, parameters: Dict):
        self._backend.post("api/{}/{}/process/{}".format(store_name, project_name, asset_name), data={"worker_type": worker_type, "parameters": parameters})

    def check_objects(self, store_name: str, project_name: str, object_names: List[str]) -> List[Dict]:
        return [self.get_object_info(store_name=store_name, project_name=project_name, object_name=item)
                for item in object_names if self.has_object(store_name=store_name, project_name=project_name, object_name=item)]

    def has_object(self, store_name: str, project_name: str, object_name: str) -> bool:
        return self._backend.head("api/{}/{}/object/{}".format(store_name, project_name, object_name))

    def get_object(self, store_name: str, project_name: str, object_name: str) -> Union[None, Dict]:
        return self._backend.get("api/{}/{}/object/{}".format(store_name, project_name, object_name))

    def get_object_info(self, store_name: str, project_name: str, object_name: str) -> Union[None, Dict]:
        return self._backend.get("api/{}/{}/object/{}/info".format(store_name, project_name, object_name))

    def set_object(self, store_name: str, project_name: str, object_name: str, object_data: Dict) -> None:
        return self._backend.put("api/{}/{}/object/{}".format(store_name, project_name, object_name), data=object_data)


def _mutate(d: Dict, field: str, value: Any) -> Dict:
    d[field] = value
    return d


def _add_item(item: str, node_type: str, results: List[Dict], url: str = None):
    if len(item) > 0:
        path = item.rsplit("/", maxsplit=1)
        if len(path) == 1:
            if not _has_item(key=item, results=results):
                results.append({"id": item, "type": node_type, "url": url, "parent": "#", "text": item})
        else:
            if not _has_item(key=item, results=results):
                results.append({"id": item, "type": node_type, "url": url, "parent": path[0], "text": path[1]})
                _add_item(item=path[0], node_type="parent", results=results)


def _has_item(key: str, results: List[Dict]) -> bool:
    return any([x.get("id", "") == key for x in results])
