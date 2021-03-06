import glob
import os
from typing import Dict

from common.entities import OveAssetMeta, TaskStatus
from common.errors import WorkerLockError
from common.s3minio import S3Manager
from common.util import append_slash


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

    def get_asset_meta(self, project_id: str, asset_id: str) -> OveAssetMeta:
        return self._manager.get_asset_meta(project_id=project_id, asset_id=asset_id)

    def set_asset_meta(self, project_id: str, asset_id: str, meta: OveAssetMeta) -> None:
        self._manager.set_asset_meta(project_id=project_id, asset_id=asset_id, meta=meta)

    def download_asset(self, project_id: str, asset_id: str, filename: str, down_filename: str):
        return self._manager.download_asset(project_id=project_id, asset_id=asset_id, filename=filename, down_filename=down_filename)

    def upload_asset(self, project_id: str, asset_id: str, filename: str, upload_filename: str) -> None:
        return self._manager.upload_asset(project_id=project_id, asset_id=asset_id, filename=filename, upload_filename=upload_filename)

    def upload_asset_folder(self, project_id: str, meta: OveAssetMeta, worker_name: str, upload_folder: str) -> None:
        meta_filename_name = os.path.splitext(os.path.basename(meta.filename))[0]
        prefix = str(meta.version) + "/" + worker_name + "/" + meta_filename_name
        for filename in glob.iglob(append_slash(upload_folder) + '**/*', recursive=True):
            if not os.path.islink(filename) and not os.path.ismount(filename) and os.path.isfile(filename):
                # note: filename[len(upload_folder):] always starts with /
                self._manager.upload_asset(project_id=project_id, asset_id=meta.id, upload_filename=filename,
                                           filename=prefix + filename[len(upload_folder):])

    def lock_asset(self, project_id: str, meta: OveAssetMeta, worker_name: str) -> None:
        if meta.worker is None or len(meta.worker) == 0 or meta.worker == worker_name:
            meta.worker = worker_name
            return self._manager.set_asset_meta(project_id=project_id, asset_id=meta.id, meta=meta)
        else:
            raise WorkerLockError()

    def unlock_asset(self, project_id: str, meta: OveAssetMeta, worker_name: str) -> None:
        # do not unlock other resources
        if meta.worker == worker_name:
            meta.worker = ""
            return self._manager.set_asset_meta(project_id=project_id, asset_id=meta.id, meta=meta)

    def update_asset_status(self, project_id: str, meta: OveAssetMeta, status: TaskStatus, error_msg: str = "") -> None:
        if meta:
            meta.processing_status = str(status)
            meta.processing_error = error_msg
            return self._manager.set_asset_meta(project_id=project_id, asset_id=meta.id, meta=meta)
