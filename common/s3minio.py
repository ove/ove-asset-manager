# s3miniomodule for accessing object stores that are compatible with the minio sdk
# requires pip install minio
import io
import json
import logging
import sys
from typing import Union, Dict, Callable, List

from minio import Minio
from minio.error import ResponseError

from common.consts import CONFIG_STORE_DEFAULT, CONFIG_STORE_NAME, CONFIG_STORES, CONFIG_ENDPOINT, CONFIG_ACCESS_KEY, CONFIG_SECRET_KEY, CONFIG_PROXY_URL
from common.consts import DEFAULT_CONFIG, S3_SEPARATOR, OVE_META, S3_OBJECT_EXTENSION
from common.entities import OveMeta
from common.errors import ValidationError, InvalidStoreError, InvalidAssetError, InvalidObjectError
from common.filters import DEFAULT_FILTER

_DEFAULT_LABEL = "*"


class S3Manager:
    def __init__(self):
        self._clients = {}
        self._store_config = {}

    def load(self, config_file: str = DEFAULT_CONFIG):
        try:
            with open(config_file, mode="r") as fin:
                config = json.load(fin)
                default_store = config.get(CONFIG_STORE_DEFAULT, None)

                for client_config in config.get(CONFIG_STORES, []):
                    store_name = client_config.get(CONFIG_STORE_NAME, "")
                    client = Minio(endpoint=client_config.get(CONFIG_ENDPOINT, ""),
                                   access_key=client_config.get(CONFIG_ACCESS_KEY, ""),
                                   secret_key=client_config.get(CONFIG_SECRET_KEY, ""),
                                   secure=False)
                    self._clients[store_name] = client
                    self._store_config[store_name] = client_config
                    if default_store == store_name:
                        self._clients[_DEFAULT_LABEL] = client
                        self._store_config[_DEFAULT_LABEL] = client_config
                logging.info("Loaded %s connection configs from s3 client config file", len(self._clients))
        except Exception:
            logging.error("Error while trying to load store config. Error: %s", sys.exc_info()[1])

    def setup(self, store_config: Dict):
        client = Minio(endpoint=store_config.get(CONFIG_ENDPOINT, ""),
                       access_key=store_config.get(CONFIG_ACCESS_KEY, ""),
                       secret_key=store_config.get(CONFIG_SECRET_KEY, ""),
                       secure=False)
        self._clients[_DEFAULT_LABEL] = client
        self._store_config[_DEFAULT_LABEL] = store_config

    def clear(self):
        self._clients.clear()
        self._store_config.clear()

    # Open a connection to the S3 storage
    def _get_connection(self, store_name: str = None) -> Union[Minio, None]:
        store_name = store_name if store_name else _DEFAULT_LABEL
        connection = self._clients.get(store_name, None)
        if connection:
            return connection
        else:
            raise InvalidStoreError(store_name)

    def _get_proxy_url(self, store_name: str = None) -> str:
        client_config = self.get_store_config(store_name)
        return client_config.get(CONFIG_PROXY_URL, "") if client_config is not None else ""

    def get_store_config(self, store_name: str = None) -> Dict:
        store_name = store_name if store_name else _DEFAULT_LABEL
        return self._store_config.get(store_name, None)

    def list_stores(self) -> List[str]:
        return [store for store in self._clients.keys() if store != _DEFAULT_LABEL]

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
        meta.proxy_url = self._get_proxy_url(store_name)
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

    def upload_asset(self, project_name: str, asset_name: str, filename: str, upload_filename: str, store_name: str = None) -> None:
        client = self._get_connection(store_name)
        try:
            # filesize=os.stat(upfile.name).st_size
            filepath = asset_name + S3_SEPARATOR + filename
            client.fput_object(project_name, filepath, upload_filename)
        except ResponseError:
            logging.error("Error while trying to upload. Error: %s", sys.exc_info()[1])
            raise ValidationError("Unable to upload asset to remote storage.")

    def download_asset(self, project_name: str, asset_name: str, filename: str, down_filename: str, store_name: str = None) -> None:
        client = self._get_connection(store_name)
        try:
            # filesize=os.stat(upfile.name).st_size
            filepath = asset_name + S3_SEPARATOR + filename
            client.fget_object(project_name, filepath, down_filename)
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
