# s3miniomodule for accessing object stores that are compatible with the minio sdk
# requires pip install minio
from typing import Union, Dict, Tuple

import logging
import sys
import io
import json

import falcon
from minio import Minio
from minio.error import ResponseError

from am.entities import OveMeta, ApiResult

_DEFAULT_CONFIG = "config/credentials.json"
_DEFAULT_LABEL = "*"


class S3Manager:
    def __init__(self):
        self._clients = {}

    def load(self, config_file: str = _DEFAULT_CONFIG):
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
                logging.info("Loaded %s from s3 client config", len(self._clients))
        except Exception as error:
            logging.error("Error while trying to load store config. Error: %s", sys.exc_info()[1])

    # Open a connection to the S3 storage
    def _get_connection(self, store_name: str = None) -> Union[Minio, None]:
        store_name = store_name if store_name else _DEFAULT_LABEL
        return self._clients.get(store_name, None)

    # List the projects in an s3 storage (returning the names)
    def list_projects(self, store_name: str = None) -> Dict:
        try:
            client = self._get_connection(store_name)
            buckets = client.list_buckets()
            return {'Projects': [bucket.name for bucket in buckets]}
        except:
            logging.error("Error while trying to list store. Error: %s", sys.exc_info()[1])

    # List the assets in an s3 bucket
    def list_assets(self, project_name: str, store_name: str = None) -> Dict:
        try:
            client = self._get_connection(store_name)
            assets = client.list_objects(project_name, prefix=None, recursive=False)
            return {'Assets': [asset.object_name[0:-1] for asset in assets if asset.is_dir]}
        except:
            logging.error("Error while trying to list assets. Error: %s", sys.exc_info()[1])

    def check_exists(self, project_name: str, store_name: str = None) -> bool:
        try:
            client = self._get_connection(store_name)
            return client.bucket_exists(project_name)
        except ResponseError:
            logging.error("Error while trying to check exists. Error: %s", sys.exc_info()[1])
            return False

    def create_project(self, name: str, store_name: str = None) -> bool:
        try:
            client = self._get_connection(store_name)
            client.make_bucket(name, location='us-east-1')
            return True
        except ResponseError:
            logging.error("Error while trying to create project. Error: %s", sys.exc_info()[1])
            return False

    def create_asset(self, project_name: str, meta, store_name: str = None) -> ApiResult:
        try:
            client = self._get_connection(store_name)
            # minio interprets the slash as a directory
            meta_name = meta.name + '/' + '.ovemeta'
            # We create the meta file at the same time
            if self.get_asset_meta(project_name, meta.name, store_name=store_name).success:
                return ApiResult(success=False, message="This asset already exists", status=falcon.HTTP_409)
            # We make a file stream and write it to the s3 storage
            print("Meta class working", meta.name)
            temp_meta = io.BytesIO(json.dumps(meta.__dict__).encode())
            file_size = temp_meta.getbuffer().nbytes
            print(client.put_object(project_name, meta_name, temp_meta, file_size))
            return ApiResult(success=True, data=meta, message="Asset created")
        except ResponseError as err:
            return ApiResult(success=False, message=str(err), status=falcon.HTTP_400)

    def upload_asset(self, project_name: str, asset_name: str, filename: str, upfile,
                     store_name: str = None) -> ApiResult:
        try:
            client = self._get_connection(store_name)
            # filesize=os.stat(upfile.name).st_size
            filepath = asset_name + '/' + filename
            print(client.fput_object(project_name, filepath, upfile.name))
            return ApiResult(success=True, message="Asset uploaded")
        except ResponseError as err:
            return ApiResult(success=False, message=str(err))

    def get_asset_meta(self, project_name: str, asset_name: str, store_name: str = None) -> ApiResult:
        try:
            client = self._get_connection(store_name)
            meta_name = asset_name + '/' + '.ovemeta'
            print('Checking if asset exists')
            obj = json.load(client.get_object(project_name, meta_name))

            meta = OveMeta(name=obj.get('name', ""), description=obj.get('description', ""),
                           uploaded=obj.get('uploaded', False), permissions=obj.get('permissions', ""))
            return ApiResult(success=True, data=meta)
        except Exception as err:
            logging.error("Error while trying to get asset meta. Error: %s", sys.exc_info()[1])
            return ApiResult(success=False, message=str(err))

    def set_asset_meta(self, project_name: str, asset_name: str, meta: OveMeta, store_name: str = None) -> ApiResult:
        try:
            client = self._get_connection(store_name)
            meta_name = asset_name + '/' + '.ovemeta'
            temp_meta = io.BytesIO(json.dumps(meta.__dict__).encode())
            filesize = temp_meta.getbuffer().nbytes
            print(client.put_object(project_name, meta_name, temp_meta, filesize))
            return ApiResult(success=True)
        except Exception as err:
            logging.error("Error while trying to set asset meta. Error: %s", sys.exc_info()[1])
            return ApiResult(success=False, message=str(err))
