from typing import Dict

from common.entities import OveMeta
from common.errors import WorkerLockError
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

    def download_asset(self, project_name: str, asset_name: str, filename: str, down_filename: str):
        return self._manager.download_asset(project_name=project_name, asset_name=asset_name, filename=filename, down_filename=down_filename)

    def upload_asset(self, project_name: str, asset_name: str, filename: str, upload_filename: str) -> None:
        return self._manager.upload_asset(project_name=project_name, asset_name=asset_name, filename=filename, upload_filename=upload_filename)

    def lock_asset(self, project_name: str, asset_name: str, meta: OveMeta, worker_name: str) -> None:
        if meta.worker is None or len(meta.worker) == 0 or meta.worker == worker_name:
            meta.worker = worker_name
            return self._manager.set_asset_meta(project_name=project_name, asset_name=asset_name, meta=meta)
        else:
            raise WorkerLockError()

    def unlock_asset(self, project_name: str, asset_name: str, meta: OveMeta) -> None:
        meta.worker = ""
        return self._manager.set_asset_meta(project_name=project_name, asset_name=asset_name, meta=meta)
