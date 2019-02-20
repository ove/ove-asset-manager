from typing import Dict

import requests

from common.errors import ValidationError
from common.util import append_slash

_RESERVED_NAMES = {"list", "validate", "create"}


class BackendController:
    def __init__(self, backend_url: str):
        self._backend_url = append_slash(backend_url)

    # def list_stores(self):
    #     return self._manager.list_stores()

    def list_projects(self, store_name: str = "*", with_object: str = None) -> Dict:
        response = requests.get(self._backend_url + "api/{}/list".format(store_name))
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            raise ValidationError(**response.json())

    # def list_assets(self, project_name: str, store_name: str = None, result_filter: Callable = None) -> Dict:
    #     return self._manager.list_assets(store_name=store_name, project_name=project_name, result_filter=result_filter)
    #
    # def create_project(self, project_name: str, store_name: str = None) -> None:
    #     # To avoid confusion, we reserve certain names for projects
    #     if project_name in _RESERVED_NAMES:
    #         raise ProjectExistsError(store_name=store_name, project_name=project_name)
    #     if self._manager.check_exists(store_name=store_name, project_name=project_name):
    #         raise ProjectExistsError(store_name=store_name, project_name=project_name)
    #
    #     self._manager.create_project(store_name=store_name, project_name=project_name)
    #
    # def check_exists_project(self, project_name: str, store_name: str = None) -> bool:
    #     return self._manager.check_exists(store_name=store_name, project_name=project_name)
    #
    # def create_asset(self, project_name: str, meta: OveMeta, store_name: str = None) -> OveMeta:
    #     if self._manager.has_asset_meta(store_name=store_name, project_name=project_name, asset_name=meta.name):
    #         raise AssetExistsError(store_name=store_name, project_name=project_name, asset_name=meta.name)
    #     return self._manager.create_asset(store_name=store_name, project_name=project_name, meta=meta)
    #
    # def upload_asset(self, project_name: str, asset_name: str, filename: str, meta: OveMeta, upload_filename: str, store_name: str = None) -> None:
    #     meta.filename = filename
    #     self._manager.upload_asset(store_name=store_name, project_name=project_name, asset_name=asset_name, filename=meta.file_location,
    #                                upload_filename=upload_filename)
    #     logging.debug("Setting uploaded flag to True")
    #     meta.uploaded = True
    #     meta.upload()
    #     self._manager.set_asset_meta(store_name=store_name, project_name=project_name, asset_name=asset_name, meta=meta)
    #
    # def update_asset(self, project_name: str, asset_name: str, filename: str, meta: OveMeta, upload_filename: str, store_name: str = None) -> None:
    #     meta.filename = filename
    #     meta.update()
    #     self._manager.set_asset_meta(store_name=store_name, project_name=project_name, asset_name=asset_name, meta=meta)
    #     self._manager.upload_asset(store_name=store_name, project_name=project_name, asset_name=asset_name, filename=meta.file_location,
    #                                upload_filename=upload_filename)
    #
    # def get_asset_meta(self, project_name: str, asset_name: str, store_name: str = None) -> OveMeta:
    #     return self._manager.get_asset_meta(store_name=store_name, project_name=project_name, asset_name=asset_name)
    #
    # def edit_asset_meta(self, project_name: str, asset_name: str, meta: OveMeta, store_name: str = None) -> None:
    #     self._manager.set_asset_meta(project_name=project_name, asset_name=asset_name, meta=meta, store_name=store_name)
    #
    # def get_object(self, project_name: str, object_name: str, store_name: str = None) -> Union[None, Dict]:
    #     return self._manager.get_object(store_name=store_name, project_name=project_name, object_name=object_name)
    #
    # def set_object(self, project_name: str, object_name: str, object_data: Dict, store_name: str = None, update: bool = False) -> None:
    #     if not update and self._manager.has_object(store_name=store_name, project_name=project_name, object_name=object_name):
    #         raise ObjectExistsError(store_name=store_name, project_name=project_name, object_name=object_name)
    #
    #     return self._manager.set_object(store_name=store_name, project_name=project_name, object_name=object_name, object_data=object_data)
