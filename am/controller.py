# Module to allow connection to interpret connection to different store types
# Additonally acts as a transformer for multiple s3 APIs including Minio and AWS implementations
from typing import Dict, Union, Callable, List

from common.consts import DEFAULT_CONFIG
from common.entities import OveAssetMeta, OveProjectMeta
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

    def get_store_config(self, store_id: str):
        return self._manager.get_store_config(store_id=store_id)

    def list_stores(self):
        return self._manager.list_stores()

    # List the projects in an storage (returning the names)
    def list_projects(self, store_id: str = None, metadata: bool = False, result_filter: Callable = None) -> List[Dict]:
        return self._manager.list_projects(store_id=store_id, metadata=metadata, result_filter=result_filter)

    def list_assets(self, project_id: str, store_id: str = None, result_filter: Callable = None) -> List[Dict]:
        return self._manager.list_assets(store_id=store_id, project_id=project_id, result_filter=result_filter)

    def list_files(self, project_id: str, asset_id: str, store_id: str = None) -> List[Dict]:
        return self._manager.list_files(store_id=store_id, project_id=project_id, asset_id=asset_id)

    def create_project(self, project_id: str, store_id: str = None) -> None:
        # To avoid confusion, we reserve certain names for projects
        if project_id in _RESERVED_NAMES:
            raise ProjectExistsError(store_id=store_id, project_id=project_id)
        if self._manager.check_exists(store_id=store_id, project_id=project_id):
            raise ProjectExistsError(store_id=store_id, project_id=project_id)

        self._manager.create_project(store_id=store_id, project_id=project_id)

    def check_exists_project(self, project_id: str, store_id: str = None) -> bool:
        return self._manager.check_exists(store_id=store_id, project_id=project_id)

    def create_asset(self, project_id: str, meta: OveAssetMeta, store_id: str = None) -> OveAssetMeta:
        if meta.name in _RESERVED_NAMES:
            raise AssetExistsError(store_id=store_id, project_id=project_id, asset_id=meta.name)
        if self._manager.has_asset_meta(store_id=store_id, project_id=project_id, asset_id=meta.name):
            raise AssetExistsError(store_id=store_id, project_id=project_id, asset_id=meta.name)
        return self._manager.create_asset(store_id=store_id, project_id=project_id, meta=meta)

    def upload_asset(self, project_id: str, asset_id: str, filename: str, meta: OveAssetMeta, upload_filename: str, store_id: str = None,
                     update: bool = False) -> None:
        meta.filename = filename
        if update:
            meta.update()
        else:
            meta.uploaded = True
            meta.upload()

        self._manager.upload_asset(store_id=store_id, project_id=project_id, asset_id=asset_id, filename=meta.file_location,
                                   upload_filename=upload_filename)
        self._manager.set_asset_meta(store_id=store_id, project_id=project_id, asset_id=asset_id, meta=meta)

    def get_project_meta(self, project_id: str, store_id: str = None) -> OveProjectMeta:
        return self._manager.get_project_meta(store_id=store_id, project_id=project_id, ignore_errors=True)

    def edit_project_meta(self, project_id: str, meta: OveProjectMeta, store_id: str = None) -> None:
        self._manager.set_project_meta(project_id=project_id, meta=meta, store_id=store_id, ignore_errors=False)

    def get_asset_meta(self, project_id: str, asset_id: str, store_id: str = None) -> OveAssetMeta:
        return self._manager.get_asset_meta(store_id=store_id, project_id=project_id, asset_id=asset_id)

    def edit_asset_meta(self, project_id: str, asset_id: str, meta: OveAssetMeta, store_id: str = None) -> None:
        self._manager.set_asset_meta(project_id=project_id, asset_id=asset_id, meta=meta, store_id=store_id)

    def has_object(self, project_id: str, object_id: str, store_id: str = None) -> bool:
        return self._manager.has_object(store_id=store_id, project_id=project_id, object_id=object_id)

    def get_object(self, project_id: str, object_id: str, store_id: str = None) -> Union[None, Dict]:
        return self._manager.get_object(store_id=store_id, project_id=project_id, object_id=object_id)

    def get_object_info(self, project_id: str, object_id: str, store_id: str = None) -> Union[None, Dict]:
        return self._manager.get_object_info(store_id=store_id, project_id=project_id, object_id=object_id)

    def set_object(self, project_id: str, object_id: str, object_data: Dict, store_id: str = None, update: bool = False) -> None:
        if not update and self._manager.has_object(store_id=store_id, project_id=project_id, object_id=object_id):
            raise ObjectExistsError(store_id=store_id, project_id=project_id, object_id=object_id)

        return self._manager.set_object(store_id=store_id, project_id=project_id, object_id=object_id, object_data=object_data)
