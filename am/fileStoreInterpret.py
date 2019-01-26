# Module to allow connection to interpret connection to different store types
# Additonally acts as a transformer for multiple s3 APIs including Minio and AWS implementations
from typing import Dict, Union

import logging

from am.consts import DEFAULT_CONFIG
from am.entities import OveMeta
from am.errors import AssetExistsError, ObjectExistsError
from am.s3minio import S3Manager


class FileController:
    def __init__(self, store_type: str = "s3", config_file: str = DEFAULT_CONFIG):
        if store_type == "s3":
            self._manager = S3Manager()
            self._manager.load(config_file=config_file)
        else:
            raise ValueError("Invalid store type provided")

    # List the projects in an storage (returning the names)
    def list_projects(self, store_name: str = None, with_object: str = None) -> Dict:
        return self._manager.list_projects(store_name=store_name, with_object=with_object)

    def list_assets(self, project_name: str, store_name: str = None, include_empty: bool = False) -> Dict:
        return self._manager.list_assets(project_name, store_name=store_name, include_empty=include_empty)

    def create_project(self, project_name: str, store_name: str = None) -> None:
        if self._manager.check_exists(project_name, store_name=store_name):
            raise AssetExistsError(store_name=store_name, project_name=project_name)

        self._manager.create_project(project_name, store_name=store_name)

    def create_asset(self, project_name: str, meta: OveMeta, store_name: str = None) -> OveMeta:
        if self._manager.has_asset_meta(store_name=store_name, project_name=project_name, asset_name=meta.name):
            raise AssetExistsError(store_name=store_name, project_name=project_name, asset_name=meta.name)

        return self._manager.create_asset(project_name, meta, store_name=store_name)

    def upload_asset(self, project_name: str, asset_name: str, filename: str, meta: OveMeta, file,
                     store_name: str = None) -> None:
        self._manager.upload_asset(project_name, asset_name, filename, file, store_name=store_name)
        logging.debug("Setting uploaded flag to True")
        meta.uploaded = True
        self._manager.set_asset_meta(project_name, asset_name, meta, store_name=store_name)

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
