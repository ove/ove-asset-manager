# Module to allow connection to interpret connection to different store types
# Additonally acts as a transformer for multiple s3 APIs including Minio and AWS implementations
import logging
from typing import Dict, Union, Callable

from common.consts import DEFAULT_CONFIG
from common.entities import OveMeta
from common.errors import AssetExistsError, ObjectExistsError, ProjectExistsError
from common.s3minio import S3Manager

_RESERVED_NAMES = {"list", "validate", "create", "new"}


class FileController:
    def __init__(self, store_type: str = "s3", config_file: str = DEFAULT_CONFIG):
        if store_type == "s3":
            self._manager = S3Manager()
            self._manager.load(config_file=config_file)
        else:
            raise ValueError("Invalid store type provided")

    def get_store_config(self, store_name: str):
        return self._manager.get_store_config(store_name=store_name)

    def list_stores(self):
        return self._manager.list_stores()

    # List the projects in an storage (returning the names)
    def list_projects(self, store_name: str = None, with_object: str = None) -> Dict:
        return self._manager.list_projects(store_name=store_name, with_object=with_object)

    def list_assets(self, project_name: str, store_name: str = None, result_filter: Callable = None) -> Dict:
        return self._manager.list_assets(store_name=store_name, project_name=project_name, result_filter=result_filter)

    def create_project(self, project_name: str, store_name: str = None) -> None:
        # To avoid confusion, we reserve certain names for projects
        if project_name in _RESERVED_NAMES:
            raise ProjectExistsError(store_name=store_name, project_name=project_name)
        if self._manager.check_exists(store_name=store_name, project_name=project_name):
            raise ProjectExistsError(store_name=store_name, project_name=project_name)

        self._manager.create_project(store_name=store_name, project_name=project_name)

    def check_exists_project(self, project_name: str, store_name: str = None) -> bool:
        return self._manager.check_exists(store_name=store_name, project_name=project_name)

    def create_asset(self, project_name: str, meta: OveMeta, store_name: str = None) -> OveMeta:
        if meta.name in _RESERVED_NAMES:
            raise AssetExistsError(store_name=store_name, project_name=project_name, asset_name=meta.name)
        if self._manager.has_asset_meta(store_name=store_name, project_name=project_name, asset_name=meta.name):
            raise AssetExistsError(store_name=store_name, project_name=project_name, asset_name=meta.name)
        return self._manager.create_asset(store_name=store_name, project_name=project_name, meta=meta)

    def upload_asset(self, project_name: str, asset_name: str, filename: str, meta: OveMeta, upload_filename: str, store_name: str = None) -> None:
        meta.filename = filename
        self._manager.upload_asset(store_name=store_name, project_name=project_name, asset_name=asset_name, filename=meta.file_location,
                                   upload_filename=upload_filename)
        logging.debug("Setting uploaded flag to True")
        meta.uploaded = True
        meta.upload()
        self._manager.set_asset_meta(store_name=store_name, project_name=project_name, asset_name=asset_name, meta=meta)

    def update_asset(self, project_name: str, asset_name: str, filename: str, meta: OveMeta, upload_filename: str, store_name: str = None) -> None:
        meta.filename = filename
        meta.update()
        self._manager.set_asset_meta(store_name=store_name, project_name=project_name, asset_name=asset_name, meta=meta)
        self._manager.upload_asset(store_name=store_name, project_name=project_name, asset_name=asset_name, filename=meta.file_location,
                                   upload_filename=upload_filename)

    def get_asset_meta(self, project_name: str, asset_name: str, store_name: str = None) -> OveMeta:
        return self._manager.get_asset_meta(store_name=store_name, project_name=project_name, asset_name=asset_name)

    def edit_asset_meta(self, project_name: str, asset_name: str, meta: OveMeta, store_name: str = None) -> None:
        self._manager.set_asset_meta(project_name=project_name, asset_name=asset_name, meta=meta, store_name=store_name)

    def get_object(self, project_name: str, object_name: str, store_name: str = None) -> Union[None, Dict]:
        return self._manager.get_object(store_name=store_name, project_name=project_name, object_name=object_name)

    def set_object(self, project_name: str, object_name: str, object_data: Dict, store_name: str = None, update: bool = False) -> None:
        if not update and self._manager.has_object(store_name=store_name, project_name=project_name, object_name=object_name):
            raise ObjectExistsError(store_name=store_name, project_name=project_name, object_name=object_name)

        return self._manager.set_object(store_name=store_name, project_name=project_name, object_name=object_name, object_data=object_data)
