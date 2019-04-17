import io
from typing import Dict

from common.consts import DEFAULT_CONFIG
from common.s3minio import S3Manager

_RESERVED_NAMES = {"list", "validate", "create", "new"}


class FileController:
    def __init__(self, store_type: str = "s3", config_file: str = DEFAULT_CONFIG):
        if store_type == "s3":
            self._manager = S3Manager()
            self._manager.load(config_file=config_file)
        else:
            raise ValueError("Invalid store type provided")

    def get_resource(self, store_name: str, project_name: str, path_name: str) -> io.FileIO:
        return self._manager.get_stream(store_name=store_name, project_name=project_name, path_name=path_name)

    def get_resource_meta(self, store_name: str, project_name: str, path_name: str) -> Dict:
        return self._manager.get_stream_meta(store_name=store_name, project_name=project_name, path_name=path_name)
