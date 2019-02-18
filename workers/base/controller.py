from typing import Dict

from common.entities import OveMeta
from common.s3minio import S3Manager


class FileController:
    def __init__(self, store_type: str = "s3"):
        if store_type == "s3":
            self._manager = S3Manager()
        else:
            raise ValueError("Invalid store type provided")

    def setup(self, store_config: Dict):
        return self._manager.setup(store_config)

    def clean(self):
        return self._manager.clear()

    def get_asset_meta(self, project_name: str, asset_name: str) -> OveMeta:
        return self._manager.get_asset_meta(project_name=project_name, asset_name=asset_name)

    def set_asset_meta(self, project_name: str, asset_name: str, meta: OveMeta) -> None:
        self._manager.set_asset_meta(project_name=project_name, asset_name=asset_name, meta=meta)

    def lock_asset(self, project_name: str, asset_name: str, meta: OveMeta, worker_name: str) -> None:
        meta.worker = worker_name
        return self._manager.set_asset_meta(project_name=project_name, asset_name=asset_name, meta=meta)

    def unlock_asset(self, project_name: str, asset_name: str, meta: OveMeta) -> None:
        meta.worker = ""
        return self._manager.set_asset_meta(project_name=project_name, asset_name=asset_name, meta=meta)
