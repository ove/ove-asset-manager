# s3miniomodule for accessing object stores that are compatible with the minio sdk
# requires pip install minio
from typing import Union, Dict

import logging
import sys
import io
import json

from minio import Minio
from minio.error import ResponseError

from am.consts import DEFAULT_CONFIG, S3_SEPARATOR, OVE_META
from am.entities import OveMeta
from am.errors import ValidationError, InvalidStoreError, InvalidAssetError

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
    def list_projects(self, store_name: str = None) -> Dict:
        try:
            client = self._get_connection(store_name)
            buckets = client.list_buckets()
            return {'Projects': [bucket.name for bucket in buckets]}
        except Exception:
            logging.error("Error while trying to list store. Error: %s", sys.exc_info()[1])
            return {'Projects': []}

    # List all the folders in an s3 bucket
    def list_all_assets(self, project_name: str, store_name: str = None) -> Dict:
        try:
            client = self._get_connection(store_name)
            assets = client.list_objects(project_name, prefix=None, recursive=False)
            return {'Assets': [asset.object_name[0:-1] for asset in assets if asset.is_dir]}
        except Exception:
            logging.error("Error while trying to list assets. Error: %s", sys.exc_info()[1])
            return {'Assets': []}

    # List the assets in an s3 bucket
    def list_assets(self, project_name: str, store_name: str = None) -> Dict:
        try:
            client = self._get_connection(store_name)
            assets = client.list_objects(project_name, prefix=None, recursive=False)
            result = {}
            for asset in assets:
                if asset.is_dir:
                    asset_name = asset.object_name[0:-1]
                    meta = self.get_asset_meta(project_name, asset_name, store_name, ignore_errors=True)
                    if meta:
                        result[asset_name] = meta.__dict__
            return result
        except Exception:
            logging.error("Error while trying to list assets. Error: %s", sys.exc_info()[1])

    def check_exists(self, project_name: str, store_name: str = None) -> bool:
        try:
            client = self._get_connection(store_name)
            return client.bucket_exists(project_name)
        except ResponseError:
            logging.error("Error while trying to check exists. Error: %s", sys.exc_info()[1])
            return False

    def create_project(self, name: str, store_name: str = None) -> None:
        try:
            client = self._get_connection(store_name)
            client.make_bucket(name, location='us-east-1')
        except ResponseError:
            logging.error("Error while trying to create project. Error: %s", sys.exc_info()[1])
            raise ValidationError("Unable to create project on remote storage. Please check the project name.")

    def create_asset(self, project_name: str, meta: OveMeta, store_name: str = None) -> OveMeta:
        try:
            client = self._get_connection(store_name)
            # minio interprets the slash as a directory
            meta_name = meta.name + S3_SEPARATOR + OVE_META
            temp_meta = io.BytesIO(json.dumps(meta.__dict__).encode())
            file_size = temp_meta.getbuffer().nbytes
            client.put_object(project_name, meta_name, temp_meta, file_size)
            return meta
        except ResponseError:
            logging.error("Error while trying to create asset. Error: %s", sys.exc_info()[1])
            raise ValidationError("Unable to create asset on remote storage. Please check the asset name.")

    def upload_asset(self, project_name: str, asset_name: str, filename: str, upfile, store_name: str = None) -> None:
        try:
            client = self._get_connection(store_name)
            # filesize=os.stat(upfile.name).st_size
            filepath = asset_name + S3_SEPARATOR + filename
            client.fput_object(project_name, filepath, upfile.name)
        except ResponseError:
            logging.error("Error while trying to upload. Error: %s", sys.exc_info()[1])
            raise ValidationError("Unable to upload asset to remote storage.")

    def has_asset_meta(self, project_name: str, asset_name: str, store_name: str = None) -> bool:
        try:
            client = self._get_connection(store_name)
            meta_name = asset_name + S3_SEPARATOR + OVE_META
            logging.debug('Checking if asset exists. If we can parse it then it may be valid')
            json.load(client.get_object(project_name, meta_name))
            return True
        except Exception:
            logging.error("Error while trying to check if meta exists. Error: %s", sys.exc_info()[1])
            return False

    def get_asset_meta(self, project_name: str, asset_name: str, store_name: str = None,
                       ignore_errors: bool = False) -> Union[None, OveMeta]:
        try:
            client = self._get_connection(store_name)
            meta_name = asset_name + S3_SEPARATOR + OVE_META
            logging.debug('Checking if asset exists')
            obj = json.load(client.get_object(project_name, meta_name))

            return OveMeta(name=obj.get('name', ""), description=obj.get('description', ""),
                           uploaded=obj.get('uploaded', False), permissions=obj.get('permissions', ""))
        except Exception:
            if ignore_errors:
                return None
            else:
                logging.error("Error while trying to get asset meta. Error: %s", sys.exc_info()[1])
                raise InvalidAssetError(store_name=store_name, project_name=project_name, asset_name=asset_name)

    def set_asset_meta(self, project_name: str, asset_name: str, meta: OveMeta, store_name: str = None,
                       ignore_errors: bool = False) -> None:
        try:
            client = self._get_connection(store_name)
            meta_name = asset_name + S3_SEPARATOR + OVE_META
            temp_meta = io.BytesIO(json.dumps(meta.__dict__).encode())
            file_size = temp_meta.getbuffer().nbytes
            client.put_object(project_name, meta_name, temp_meta, file_size)
        except Exception:
            if not ignore_errors:
                logging.error("Error while trying to set asset meta. Error: %s", sys.exc_info()[1])
                raise InvalidAssetError(store_name=store_name, project_name=project_name, asset_name=asset_name)
