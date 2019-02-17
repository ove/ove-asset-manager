from common.entities import OveMeta
from common.s3minio import S3Manager


class FileController:
    def __init__(self, store_type: str = "s3"):
        if store_type == "s3":
            self._manager = S3Manager()
        else:
            raise ValueError("Invalid store type provided")

    def get_asset_meta(self, project_name: str, asset_name: str, store_name: str = None) -> OveMeta:
        return self._manager.get_asset_meta(store_name=store_name, project_name=project_name, asset_name=asset_name)

    def edit_asset_meta(self, project_name: str, asset_name: str, meta: OveMeta, store_name: str = None) -> None:
        self._manager.set_asset_meta(project_name=project_name, asset_name=asset_name, meta=meta, store_name=store_name)
