from typing import Dict, Union, List

import requests

from common.errors import ValidationError
from common.util import append_slash

_RESERVED_NAMES = {"list", "validate", "create"}


class BackendController:
    def __init__(self, backend_url: str):
        self._backend_url = append_slash(backend_url)

    def list_workers(self) -> List:
        return _get_data(self._backend_url + "api/workers") or []

    def edit_worker(self, action: str, name: str):
        if action == "reset":
            _post_data(self._backend_url + "api/workers/status", data={"name": name})
        elif action == "delete":
            _delete_data(self._backend_url + "api/workers", data={"name": name})

    def list_stores(self) -> List:
        return _get_data(self._backend_url + "api/list") or []

    def list_projects(self, store_name: str) -> List:
        projects = _get_data(self._backend_url + "api/{}/list".format(store_name)).get("Projects", [])
        projects_with_project = set(_get_data(self._backend_url + "api/{}/list?hasObject=project".format(store_name)).get("Projects", []))
        return [{"name": project, "has_project": project in projects_with_project} for project in projects]

    def create_project(self, store_name: str, project_name: str) -> None:
        _post_data(self._backend_url + "api/{}/create".format(store_name), data={"name": project_name})

    def list_assets(self, store_name: str, project_name: str) -> List:
        assets = _get_data(self._backend_url + "api/{}/{}/list".format(store_name, project_name)).get("Assets", {})
        return [v for v in assets.values()]

    def get_asset(self, store_name: str, project_name: str, asset_name: str) -> Dict:
        return _get_data(self._backend_url + "api/{}/{}/meta/{}".format(store_name, project_name, asset_name))

    def create_asset(self, store_name: str, project_name: str, asset: Dict) -> Dict:
        _post_data(self._backend_url + "/api/{}/{}/create".format(store_name, project_name), data=asset)
        return self.get_asset(store_name=store_name, project_name=project_name, asset_name=asset.get("name", ""))

    def edit_asset(self, store_name: str, project_name: str, asset: Dict) -> Dict:
        return _post_data(self._backend_url + "/api/{}/{}/meta/{}".format(store_name, project_name, asset.get("name", "")), data=asset)

    # def upload_asset(self, project_name: str, asset_name: str, filename: str, meta: OveMeta, upload_filename: str, store_name: str = None) -> None:
    #     meta.filename = filename
    #     self._manager.upload_asset(store_name=store_name, project_name=project_name, asset_name=asset_name, filename=meta.file_location,
    #                                upload_filename=upload_filename)
    #     logging.debug("Setting uploaded flag to True")
    #     meta.uploaded = True
    #     meta.upload()
    #     self._manager.set_asset_meta(store_name=store_name, project_name=project_name, asset_name=asset_name, meta=meta)
    #
    # def get_object(self, project_name: str, object_name: str, store_name: str = None) -> Union[None, Dict]:
    #     return self._manager.get_object(store_name=store_name, project_name=project_name, object_name=object_name)
    #
    # def set_object(self, project_name: str, object_name: str, object_data: Dict, store_name: str = None, update: bool = False) -> None:
    #     if not update and self._manager.has_object(store_name=store_name, project_name=project_name, object_name=object_name):
    #         raise ObjectExistsError(store_name=store_name, project_name=project_name, object_name=object_name)
    #
    #     return self._manager.set_object(store_name=store_name, project_name=project_name, object_name=object_name, object_data=object_data)


def _get_data(url: str) -> Union[List, Dict]:
    response = requests.get(url)
    if 200 <= response.status_code < 300:
        return response.json()
    else:
        raise ValidationError(**response.json())


def _post_data(url: str, data: Dict) -> Union[List, Dict]:
    response = requests.post(url, json=data)
    if 200 <= response.status_code < 300:
        return response.json()
    else:
        raise ValidationError(**response.json())


def _delete_data(url: str, data: Dict) -> Union[List, Dict]:
    response = requests.delete(url, json=data)
    if 200 <= response.status_code < 300:
        return response.json()
    else:
        raise ValidationError(**response.json())
