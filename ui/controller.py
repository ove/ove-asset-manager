import json
from os.path import basename
from typing import Dict, List, Any, Union

from ui.backend import BackendClient

_RESERVED_NAMES = {"list", "validate", "create"}


class BackendController:
    def __init__(self, backend_url: str):
        self._backend = BackendClient(backend_url=backend_url)

    @property
    def backend_url(self) -> str:
        return self._backend.backend_url

    def login(self, user: str, password: str) -> Union[str, None]:
        try:
            result = self._backend.post("api/auth", data={"user": user, "password": password}, auth_token=None)
            return result.get("token", None)
        except:
            return None

    def user_info(self, auth_token: Union[str, None]) -> Dict:
        return self._backend.get("api/user/info", auth_token=auth_token)

    def list_workers(self, auth_token: Union[str, None]) -> List:
        return self._backend.get("api/workers", auth_token=auth_token) or []

    def get_worker_types(self, auth_token: Union[str, None]) -> List:
        return list({w['type']: {
            'type': w['type'],
            'extensions': w['extensions'],
            'description': w['description'],
            'parameters': json.dumps(w['parameters']),
            'docs': w.get('docs', '')
        } for w in self.list_workers(auth_token=auth_token)}.values())

    def edit_worker(self, action: str, name: str, auth_token: Union[str, None]) -> None:
        if action == "reset":
            self._backend.post("api/workers/status", data={"name": name}, auth_token=auth_token)
        elif action == "delete":
            self._backend.delete("api/workers", data={"name": name}, auth_token=auth_token)

    def list_stores(self, auth_token: Union[str, None]) -> List:
        return self._backend.get("api/list", auth_token=auth_token) or []

    def list_projects(self, store_id: str, auth_token: Union[str, None]) -> List:
        return self._backend.get("api/{}/list".format(store_id), params={"metadata": True}, auth_token=auth_token)

    def create_project(self, store_id: str, project_id: str, project_name: str, groups: List[str], auth_token: Union[str, None]) -> None:
        self._backend.post("api/{}/create".format(store_id), data={"id": project_id, "name": project_name, "groups": groups}, auth_token=auth_token)

    def get_project(self, store_id: str, project_id: str, auth_token: Union[str, None]) -> Dict:
        return self._backend.get("/api/{}/{}/projectMeta".format(store_id, project_id), auth_token=auth_token)

    def edit_project(self, store_id: str, project_id: str, project_data: Dict, auth_token: Union[str, None]) -> Dict:
        return self._backend.post("/api/{}/{}/projectMeta".format(store_id, project_id), data=project_data, auth_token=auth_token)

    def get_auth_groups(self, auth_token: Union[str, None]) -> List:
        return self._backend.get("/api/user/groups", auth_token=auth_token)

    def get_access_meta(self, store_id: str, project_id: str, auth_token: Union[str, None]) -> Dict:
        return self._backend.get("/api/{}/{}/projectAccessMeta".format(store_id, project_id), auth_token=auth_token)

    def edit_access_meta(self, store_id: str, project_id: str, meta: Dict, auth_token: Union[str, None]) -> Dict:
        return self._backend.post("/api/{}/{}/projectAccessMeta".format(store_id, project_id), data=meta, auth_token=auth_token)

    def list_assets(self, store_id: str, project_id: str, auth_token: Union[str, None]) -> List:
        return [_mutate(d, "short_index", basename(d.get("index_file", ""))) for d in self._backend.get("api/{}/{}/list".format(store_id, project_id), auth_token=auth_token)]

    def list_files(self, store_id: str, project_id: str, asset_id: str, auth_token: Union[str, None], hierarchical: bool = False) -> List[Dict]:
        files = self._backend.get("api/{}/{}/files/{}".format(store_id, project_id, asset_id), auth_token=auth_token)

        if hierarchical:
            file_tree = []
            if files:
                for file in files:
                    _add_item(item=file["name"], url=file["url"], node_type="leaf", results=file_tree)
            return file_tree
        else:
            return files

    def get_asset(self, store_id: str, project_id: str, asset_id: str, auth_token: Union[str, None]) -> Dict:
        return self._backend.get("api/{}/{}/meta/{}".format(store_id, project_id, asset_id), auth_token=auth_token)

    def create_asset(self, store_id: str, project_id: str, asset: Dict, auth_token: Union[str, None]) -> Dict:
        self._backend.post("api/{}/{}/create".format(store_id, project_id), data=asset, auth_token=auth_token)
        return self.get_asset(store_id=store_id, project_id=project_id, asset_id=asset.get("id", ""), auth_token=auth_token)

    def edit_asset(self, store_id: str, project_id: str, asset: Dict, auth_token: Union[str, None]) -> Dict:
        return self._backend.post("/api/{}/{}/meta/{}".format(store_id, project_id, asset.get("id", "")), data=asset, auth_token=auth_token)

    def upload_asset(self, store_id: str, project_id: str, asset_id: str, filename: str, stream: Any, auth_token: Union[str, None],
                     update: bool = False, create: bool = False) -> None:
        self._backend.upload(api_url="api/{}/{}/upload/{}".format(store_id, project_id, asset_id), stream=stream,
                             params={"filename": filename, "update": update, "create": create}, auth_token=auth_token)

    def schedule_worker(self, store_id: str, project_id: str, asset_id: str, worker_type: str, parameters: Dict, auth_token: Union[str, None]):
        self._backend.post("api/{}/{}/process/{}".format(store_id, project_id, asset_id), data={"worker_type": worker_type, "parameters": parameters}, auth_token=auth_token)

    def check_objects(self, store_id: str, project_id: str, object_ids: List[str], auth_token: Union[str, None]) -> List[Dict]:
        return [self.get_object_info(store_id=store_id, project_id=project_id, object_id=item, auth_token=auth_token)
                for item in object_ids if self.has_object(store_id=store_id, project_id=project_id, object_id=item, auth_token=auth_token)]

    def has_object(self, store_id: str, project_id: str, object_id: str, auth_token: Union[str, None]) -> bool:
        return self._backend.head("api/{}/{}/object/{}".format(store_id, project_id, object_id), auth_token=auth_token)

    def get_object(self, store_id: str, project_id: str, object_id: str, auth_token: Union[str, None]) -> Union[None, Dict]:
        return self._backend.get("api/{}/{}/object/{}".format(store_id, project_id, object_id), auth_token=auth_token)

    def get_object_info(self, store_id: str, project_id: str, object_id: str, auth_token: Union[str, None]) -> Union[None, Dict]:
        return self._backend.get("api/{}/{}/object/{}/info".format(store_id, project_id, object_id), auth_token=auth_token)

    def set_object(self, store_id: str, project_id: str, object_id: str, object_data: Dict, auth_token: Union[str, None]) -> None:
        return self._backend.put("api/{}/{}/object/{}".format(store_id, project_id, object_id), data=object_data, auth_token=auth_token)

    def create_project_version(self, store_id: str, project_id: str, version_name: str, version_description: str):
        self._backend.post("api/{}/{}/version".format(store_id, project_id),
                           data={"version_name": version_name, "version_description": version_description})


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
