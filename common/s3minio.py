import io
import json
import logging
import sys
from typing import Union, Dict, Callable, List, Any, Tuple

from minio import Minio
from minio.error import ResponseError
from urllib3 import HTTPResponse

from common.consts import CONFIG_STORE_DEFAULT, CONFIG_STORE_NAME, CONFIG_STORES, CONFIG_ENDPOINT, CONFIG_ACCESS_KEY, CONFIG_SECRET_KEY, CONFIG_PROXY_URL
from common.consts import DEFAULT_CONFIG, S3_SEPARATOR, OVE_META, S3_OBJECT_EXTENSION
from common.entities import OveMeta
from common.errors import ValidationError, InvalidStoreError, InvalidAssetError, InvalidObjectError, StreamNotFoundError
from common.filters import DEFAULT_FILTER
from common.util import append_slash

_DEFAULT_LABEL = "*"
_DEFAULT_OBJECT_ENCODING = "utf-8"
_DEFAULT_STORE_LOCATION = "us-east-1"


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
        except:
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
    def list_projects(self, store_name: str = None, metadata: bool = False) -> List[Dict]:
        def _last_modified(project_name) -> str:
            ts = [a.last_modified for a in client.list_objects(project_name, prefix=None, recursive=False)]
            ts = [a for a in ts if a is not None]
            if len(ts) > 0:
                return '{0:%Y-%m-%d %H:%M:%S}'.format(max(ts))
            else:
                return ''

        client = self._get_connection(store_name)
        try:
            if metadata:
                # has_object is an expensive metadata to compute
                return [{
                    "name": bucket.name,
                    "creationDate": '{0:%Y-%m-%d %H:%M:%S}'.format(bucket.creation_date),
                    "updateDate": _last_modified(bucket.name),
                    "hasProject": self.has_object(store_name=store_name, project_name=bucket.name, object_name="project")
                } for bucket in client.list_buckets()]
            else:
                return [{
                    "name": bucket.name,
                    "creationDate": '{0:%Y-%m-%d %H:%M:%S}'.format(bucket.creation_date),
                } for bucket in client.list_buckets()]
        except:
            logging.error("Error while trying to list store. Error: %s", sys.exc_info()[1])
            return []

    # List the assets in an s3 bucket
    def list_assets(self, project_name: str, store_name: str = None, result_filter: Callable = None) -> List[Dict]:
        def _format(name: str, meta: OveMeta) -> Union[str, Dict]:
            return meta.to_public_json() if meta else {"name": name, "project": project_name}

        result_filter = result_filter if result_filter is not None else DEFAULT_FILTER
        client = self._get_connection(store_name)
        try:
            assets = [a.object_name[0:-1] for a in client.list_objects(project_name, prefix=None, recursive=False) if a.is_dir]
            # For the asset list, we switch to a public meta object
            metas = {asset_name: self.get_asset_meta(project_name, asset_name, store_name, ignore_errors=True) for asset_name in assets}
            return [_format(name, meta) for name, meta in metas.items() if result_filter(meta)]
        except:
            logging.error("Error while trying to list assets. Error: %s", sys.exc_info()[1])
            return []

        # List the assets in an s3 bucket

    def list_files(self, project_name: str, asset_name: str, store_name: str = None) -> List[Dict]:
        client = self._get_connection(store_name)
        try:
            meta = self.get_asset_meta(store_name=store_name, project_name=project_name, asset_name=asset_name)
            prefix = asset_name + "/" + str(meta.version) + "/"
            return [{
                "name": a.object_name[len(prefix):],
                "url": meta.proxy_url + project_name + "/" + a.object_name,
                "default": meta.filename == a.object_name[len(prefix):]
            } for a in client.list_objects(project_name, prefix=prefix, recursive=True) if not a.is_dir]
        except:
            logging.error("Error while trying to list assets. Error: %s", sys.exc_info()[1])
            return []

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
            client.make_bucket(project_name, location=_DEFAULT_STORE_LOCATION)
        except ResponseError:
            logging.error("Error while trying to create project. Error: %s", sys.exc_info()[1])
            raise ValidationError("Unable to create project on remote storage. Please check the project name.")

    def create_asset(self, project_name: str, meta: OveMeta, store_name: str = None) -> OveMeta:
        client = self._get_connection(store_name)
        meta.proxy_url = self._get_proxy_url(store_name)
        try:
            # minio interprets the slash as a directory
            meta_name = meta.name + S3_SEPARATOR + OVE_META
            data, size = _encode_json(meta.to_json())
            client.put_object(project_name, meta_name, data, size)
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
            logging.debug('Checking if asset exists...')
            response = client.get_object(project_name, meta_name)
            return 200 <= response.status < 300
        except:
            return False

    def get_asset_meta(self, project_name: str, asset_name: str, store_name: str = None, ignore_errors: bool = False) -> Union[None, OveMeta]:
        client = self._get_connection(store_name)
        try:
            meta_name = asset_name + S3_SEPARATOR + OVE_META
            logging.debug('Checking if asset exists')
            obj = _decode_json(client.get_object(project_name, meta_name))
            return OveMeta(**obj)
        except:
            if ignore_errors:
                return None
            else:
                logging.error("Error while trying to get asset meta. Error: %s", sys.exc_info()[1])
                raise InvalidAssetError(store_name=store_name, project_name=project_name, asset_name=asset_name)

    def set_asset_meta(self, project_name: str, asset_name: str, meta: OveMeta, store_name: str = None, ignore_errors: bool = False) -> None:
        client = self._get_connection(store_name)
        try:
            meta_name = asset_name + S3_SEPARATOR + OVE_META
            data, size = _encode_json(meta.to_json())
            client.put_object(project_name, meta_name, data, size)
        except:
            if not ignore_errors:
                logging.error("Error while trying to set asset meta. Error: %s", sys.exc_info()[1])
                raise InvalidAssetError(store_name=store_name, project_name=project_name, asset_name=asset_name)

    def has_object(self, project_name: str, object_name: str, store_name: str = None) -> bool:
        _validate_object_name(store_name=store_name, project_name=project_name, object_name=object_name)

        client = self._get_connection(store_name)
        try:
            logging.debug('Checking if object exists ...')
            response = client.get_object(project_name, object_name + S3_OBJECT_EXTENSION)
            return 200 <= response.status < 300
        except:
            return False

    def get_object(self, project_name: str, object_name: str, store_name: str = None, ignore_errors: bool = False) -> Union[None, Dict]:
        _validate_object_name(store_name=store_name, project_name=project_name, object_name=object_name)

        client = self._get_connection(store_name)
        try:
            return _decode_json(client.get_object(project_name, object_name + S3_OBJECT_EXTENSION))
        except Exception:
            if ignore_errors:
                return None
            else:
                logging.error("Error while trying to get object. Error: %s", sys.exc_info()[1])
                raise InvalidObjectError(store_name=store_name, project_name=project_name, object_name=object_name)

    def get_object_info(self, project_name: str, object_name: str, store_name: str = None) -> Union[None, Dict]:
        if self.has_object(store_name=store_name, project_name=project_name, object_name=object_name):
            return {
                "name": object_name,
                "index_file": append_slash(self._get_proxy_url(store_name=store_name)) + project_name + "/" + object_name + S3_OBJECT_EXTENSION
            }
        else:
            return None

    def set_object(self, project_name: str, object_name: str, object_data: Dict, store_name: str = None) -> None:
        _validate_object_name(store_name=store_name, project_name=project_name, object_name=object_name)

        client = self._get_connection(store_name)
        try:
            data, size = _encode_json(object_data)
            client.put_object(project_name, object_name + S3_OBJECT_EXTENSION, data, size)
        except Exception:
            logging.error("Error while trying to set object. Error: %s", sys.exc_info()[1])
            raise InvalidObjectError(store_name=store_name, project_name=project_name, object_name=object_name)

    def get_stream(self, store_name: str, project_name: str, path_name: str) -> io.FileIO:
        client = self._get_connection(store_name)
        try:
            return client.get_object(project_name, path_name)
        except Exception:
            logging.error("Error while trying to get stream. Error: %s", sys.exc_info()[1])
            raise StreamNotFoundError(store_name=store_name, project_name=project_name, filename=path_name)

    def get_stream_meta(self, store_name: str, project_name: str, path_name: str) -> Dict:
        client = self._get_connection(store_name)
        try:
            obj = client.stat_object(project_name, path_name)
            return {"size": obj.size, "last_modified": obj.last_modified}
        except Exception:
            logging.error("Error while trying to get stream metadata. Error: %s", sys.exc_info()[1])
            raise StreamNotFoundError(store_name=store_name, project_name=project_name, filename=path_name)


# Helpers
def _validate_object_name(store_name: str, project_name: str, object_name: str) -> None:
    if not object_name or not object_name.isalnum():
        raise InvalidObjectError(store_name=store_name, project_name=project_name, object_name=object_name)


def _encode_json(data: Any) -> Tuple[io.BytesIO, int]:
    encoded = io.BytesIO(json.dumps(data).encode(encoding=_DEFAULT_OBJECT_ENCODING))
    size = encoded.getbuffer().nbytes
    return encoded, size


def _decode_json(response: HTTPResponse) -> Dict:
    return json.load(io.TextIOWrapper(response, encoding=_DEFAULT_OBJECT_ENCODING))
