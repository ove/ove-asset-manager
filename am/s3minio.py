# s3miniomodule for accessing object stores that are compatible with the minio sdk
# requires pip install minio
import io
import json
import logging
import sys
from typing import Union, Dict, Callable

from minio import Minio
from minio.error import ResponseError

from am.consts import DEFAULT_CONFIG, S3_SEPARATOR, OVE_META, S3_OBJECT_EXTENSION
from am.entities import OveMeta
from am.errors import ValidationError, InvalidStoreError, InvalidAssetError, InvalidObjectError
from am.filters import DEFAULT_FILTER

_DEFAULT_LABEL = "*"


class S3Manager:
    def __init__(self):
        self._clients = {}

    def load(self, config_file: str = DEFAULT_CONFIG):
        try:
            with open(config_file, mode="r") as fin:
                config = json.load(fin)
                default_store = config.get("default", None)

                for client_config in config.get("stores", []):
                    store_name = client_config.get("name", "")
                    client = Minio(endpoint=client_config.get("endpoint", ""),
                                   access_key=client_config.get("accessKey", ""),
                                   secret_key=client_config.get("secretKey", ""),
                                   secure=False)
                    self._clients[store_name] = client
                    if default_store == store_name:
                        self._clients[_DEFAULT_LABEL] = client
                logging.info("Loaded %s connection configs from s3 client config file", len(self._clients))
        except Exception:
            logging.error("Error while trying to load store config. Error: %s", sys.exc_info()[1])

    # Open a connection to the S3 storage
    def _get_connection(self, store_name: str = None) -> Union[Minio, None]:
        store_name = store_name if store_name else _DEFAULT_LABEL
        connection = self._clients.get(store_name, None)
        if connection:
            return connection
        else:
            raise InvalidStoreError(store_name)

    # List the projects in an s3 storage (returning the names)
    def list_projects(self, store_name: str = None, with_object: str = None) -> Dict:
        def _filter(name: str) -> bool:
            return self.has_object(store_name=store_name, project_name=name, object_name=with_object) if with_object else True

        client = self._get_connection(store_name)
        try:
            return {'Projects': [bucket.name for bucket in client.list_buckets() if _filter(bucket.name)]}
        except Exception:
            logging.error("Error while trying to list store. Error: %s", sys.exc_info()[1])
            return {'Projects': []}

    # List the assets in an s3 bucket
    def list_assets(self, project_name: str, store_name: str = None, result_filter: Callable = None) -> Dict:
        def _format(name: str, meta: OveMeta) -> Union[str, Dict]:
            return meta.to_public_json() if meta else name

        result_filter = result_filter if result_filter is not None else DEFAULT_FILTER
        client = self._get_connection(store_name)
        try:
            assets = [a.object_name[0:-1] for a in client.list_objects(project_name, prefix=None, recursive=False) if a.is_dir]
            # For the asset list, we switch to a public meta object
            metas = {asset_name: self.get_asset_meta(project_name, asset_name, store_name, ignore_errors=True) for asset_name in assets}
            return {'Assets': {name: _format(name, meta) for name, meta in metas.items() if result_filter(meta)}}
        except Exception:
            logging.error("Error while trying to list assets. Error: %s", sys.exc_info()[1])
            return {'Assets': {}}

    def check_exists(self, project_name: str, store_name: str = None) -> bool:
        client = self._get_connection(store_name)
        try:
            return client.bucket_exists(project_name)
        except ResponseError:
            logging.error("Error while trying to check exists. Error: %s", sys.exc_info()[1])
            return False

    def create_project(self, project_name: str, store_name: str = None) -> None:
        client = self._get_connection(store_name)
        try:
            client.make_bucket(project_name, location='us-east-1')
        except ResponseError:
            logging.error("Error while trying to create project. Error: %s", sys.exc_info()[1])
            raise ValidationError("Unable to create project on remote storage. Please check the project name.")

    def create_asset(self, project_name: str, meta: OveMeta, store_name: str = None) -> OveMeta:
        client = self._get_connection(store_name)
        try:
            # minio interprets the slash as a directory
            meta_name = meta.name + S3_SEPARATOR + OVE_META
            temp_meta = io.BytesIO(json.dumps(meta.to_json()).encode())
            file_size = temp_meta.getbuffer().nbytes
            client.put_object(project_name, meta_name, temp_meta, file_size)
            meta.created()
            self.set_asset_meta(project_name, meta.name, meta, store_name)
            return meta
        except ResponseError:
            logging.error("Error while trying to create asset. Error: %s", sys.exc_info()[1])
            raise ValidationError("Unable to create asset on remote storage. Please check the asset name.")

    def upload_asset(self, project_name: str, asset_name: str, filename: str, upfile, store_name: str = None) -> None:
        client = self._get_connection(store_name)
        try:
            # filesize=os.stat(upfile.name).st_size
            filepath = asset_name + S3_SEPARATOR + filename
            print("s3 filepath", filepath)
            client.fput_object(project_name, filepath, upfile.name)
        except ResponseError:
            logging.error("Error while trying to upload. Error: %s", sys.exc_info()[1])
            raise ValidationError("Unable to upload asset to remote storage.")

    def has_asset_meta(self, project_name: str, asset_name: str, store_name: str = None) -> bool:
        client = self._get_connection(store_name)
        try:
            meta_name = asset_name + S3_SEPARATOR + OVE_META
            logging.debug('Checking if asset exists. If we can parse it then it may be valid')
            json.load(client.get_object(project_name, meta_name))
            return True
        except Exception:
            logging.error("Error while trying to check if meta exists. Error: %s", sys.exc_info()[1])
            return False

    def get_asset_meta(self, project_name: str, asset_name: str, store_name: str = None, ignore_errors: bool = False) -> Union[None, OveMeta]:
        client = self._get_connection(store_name)
        try:
            meta_name = asset_name + S3_SEPARATOR + OVE_META
            logging.debug('Checking if asset exists')
            obj = json.load(client.get_object(project_name, meta_name))
            return OveMeta(**obj)
        except Exception:
            if ignore_errors:
                return None
            else:
                logging.error("Error while trying to get asset meta. Error: %s", sys.exc_info()[1])
                raise InvalidAssetError(store_name=store_name, project_name=project_name, asset_name=asset_name)

    def set_asset_meta(self, project_name: str, asset_name: str, meta: OveMeta, store_name: str = None, ignore_errors: bool = False) -> None:
        client = self._get_connection(store_name)
        try:
            meta_name = asset_name + S3_SEPARATOR + OVE_META
            temp_meta = io.BytesIO(json.dumps(meta.to_json()).encode())
            file_size = temp_meta.getbuffer().nbytes
            client.put_object(project_name, meta_name, temp_meta, file_size)
        except Exception:
            if not ignore_errors:
                logging.error("Error while trying to set asset meta. Error: %s", sys.exc_info()[1])
                raise InvalidAssetError(store_name=store_name, project_name=project_name, asset_name=asset_name)

    def has_object(self, project_name: str, object_name: str, store_name: str = None) -> bool:
        _validate_object_name(store_name=store_name, project_name=project_name, object_name=object_name)

        client = self._get_connection(store_name)
        try:
            logging.debug('Checking if object exists. If we can parse it then it may be valid')
            json.load(client.get_object(project_name, object_name + S3_OBJECT_EXTENSION))
            return True
        except Exception:
            logging.error("Error while trying to check if object exists. Error: %s", sys.exc_info()[1])
            return False

    def get_object(self, project_name: str, object_name: str, store_name: str = None, ignore_errors: bool = False) -> Union[None, Dict]:
        _validate_object_name(store_name=store_name, project_name=project_name, object_name=object_name)

        client = self._get_connection(store_name)
        try:
            return json.load(client.get_object(project_name, object_name + S3_OBJECT_EXTENSION))
        except Exception:
            if ignore_errors:
                return None
            else:
                logging.error("Error while trying to get object. Error: %s", sys.exc_info()[1])
                raise InvalidObjectError(store_name=store_name, project_name=project_name, object_name=object_name)

    def set_object(self, project_name: str, object_name: str, object_data: Dict, store_name: str = None) -> None:
        _validate_object_name(store_name=store_name, project_name=project_name, object_name=object_name)

        client = self._get_connection(store_name)
        try:
            temp = io.BytesIO(json.dumps(object_data).encode())
            file_size = temp.getbuffer().nbytes
            client.put_object(project_name, object_name + S3_OBJECT_EXTENSION, temp, file_size)
        except Exception:
            logging.error("Error while trying to set object. Error: %s", sys.exc_info()[1])
            raise InvalidObjectError(store_name=store_name, project_name=project_name, object_name=object_name)


# Helpers
def _validate_object_name(store_name: str, project_name: str, object_name: str) -> None:
    if not object_name or not object_name.isalnum():
        raise InvalidObjectError(store_name=store_name, project_name=project_name, object_name=object_name)
