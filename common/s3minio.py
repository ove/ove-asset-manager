import io
import json
import logging
import sys
from typing import Union, Dict, Callable, List, Any, Tuple

from minio import Minio
from minio.error import ResponseError, NoSuchKey
from urllib3 import HTTPResponse

from common.consts import CONFIG_STORE_DEFAULT, CONFIG_STORE_NAME, CONFIG_STORES, CONFIG_ENDPOINT, CONFIG_ACCESS_KEY, CONFIG_SECRET_KEY, CONFIG_PROXY_URL, PROJECT_SECTIONS
from common.consts import DEFAULT_CREDENTIALS_CONFIG, S3_SEPARATOR, OVE_META, PROJECT_FILE, S3_OBJECT_EXTENSION, MAX_LIST_ITEMS
from common.consts import PROJECT_BASIC_TEMPLATE, PROJECT_METADATA_SECTION
from common.entities import OveAssetMeta, OveProjectMeta, OveProjectAccessMeta, UserAccessMeta
from common.errors import ValidationError, InvalidStoreError, InvalidAssetError, InvalidObjectError, StreamNotFoundError, InvalidProjectError
from common.filters import DEFAULT_FILTER
from common.util import append_slash

_DEFAULT_LABEL = "*"
_DEFAULT_OBJECT_ENCODING = "utf-8"
_DEFAULT_STORE_LOCATION = "us-east-1"


class S3Manager:
    def __init__(self):
        self._clients = {}
        self._store_config = {}

    def load(self, config_file: str = DEFAULT_CREDENTIALS_CONFIG):
        try:
            with open(config_file, mode="r") as fin:
                config = json.load(fin)
                default_store = config.get(CONFIG_STORE_DEFAULT, None)

                for client_config in config.get(CONFIG_STORES, []):
                    store_id = client_config.get(CONFIG_STORE_NAME, "")
                    client = Minio(endpoint=client_config.get(CONFIG_ENDPOINT, ""),
                                   access_key=client_config.get(CONFIG_ACCESS_KEY, ""),
                                   secret_key=client_config.get(CONFIG_SECRET_KEY, ""),
                                   secure=False)
                    self._clients[store_id] = client
                    self._store_config[store_id] = client_config
                    if default_store == store_id:
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
    def _get_connection(self, store_id: str = None) -> Union[Minio, None]:
        store_id = store_id if store_id else _DEFAULT_LABEL
        connection = self._clients.get(store_id, None)
        if connection:
            return connection
        else:
            raise InvalidStoreError(store_id)

    def _get_proxy_url(self, store_id: str = None) -> str:
        client_config = self.get_store_config(store_id)
        return client_config.get(CONFIG_PROXY_URL, "") if client_config is not None else ""

    def get_store_config(self, store_id: str = None) -> Dict:
        store_id = store_id if store_id else _DEFAULT_LABEL
        return self._store_config.get(store_id, None)

    def list_stores(self) -> List[str]:
        return [store for store in self._clients.keys() if store != _DEFAULT_LABEL]

    # List the projects in an s3 storage (returning the names)
    def list_projects(self, access: UserAccessMeta, store_id: str = None, metadata: bool = False, result_filter: Callable = None) -> List[Dict]:
        def _last_modified(project_id) -> str:
            ts = [a.last_modified for a in client.list_objects(project_id, prefix=None, recursive=False)]
            ts = [a for a in ts if a is not None]
            if len(ts) > 0:
                return '{0:%Y-%m-%d %H:%M:%S}'.format(max(ts))
            else:
                return ''

        client = self._get_connection(store_id)
        try:
            if metadata:
                result_filter = result_filter if result_filter is not None else DEFAULT_FILTER
                # has_object is an expensive metadata to compute
                result = []
                for bucket in client.list_buckets():
                    meta = self.get_project_meta(store_id=store_id, project_id=bucket.name, ignore_errors=True)
                    if result_filter(meta) and self.has_access(store_id=store_id, project_id=bucket.name, groups=access.read_groups, is_admin=access.admin_access):
                        item = meta.to_public_json()
                        item["id"] = bucket.name
                        item["creationDate"] = '{0:%Y-%m-%d %H:%M:%S}'.format(bucket.creation_date)
                        item["updateDate"] = _last_modified(bucket.name)
                        item["hasProject"] = self.has_object(store_id=store_id, project_id=bucket.name, object_id="project")
                        item["projectType"] = self.project_type(store_id=store_id, project_id=bucket.name)
                        item["access"] = self.get_project_access_meta(store_id=store_id, project_id=bucket.name).groups
                        item["read_access"] = True
                        item["write_access"] = self.has_access(store_id=store_id, project_id=bucket.name, groups=access.write_groups, is_admin=access.admin_access)

                        result.append(item)

                return result
            else:
                return [{
                    "id": bucket.name,
                    "creationDate": '{0:%Y-%m-%d %H:%M:%S}'.format(bucket.creation_date),
                } for bucket in client.list_buckets() if self.has_access(store_id=store_id, project_id=bucket.name, groups=access.read_groups, is_admin=access.admin_access)]
        except:
            logging.error("Error while trying to list store. Error: %s", sys.exc_info()[1])
            return []

    # List the assets in an s3 bucket
    def list_assets(self, project_id: str, store_id: str = None, result_filter: Callable = None) -> List[Dict]:
        def _format(name: str, meta: OveAssetMeta) -> Union[str, Dict]:
            return meta.to_public_json() if meta else {"name": name, "project": project_id}

        result_filter = result_filter if result_filter is not None else DEFAULT_FILTER
        client = self._get_connection(store_id)
        try:
            assets = [a.object_name[0:-1] for a in client.list_objects(project_id, prefix=None, recursive=False) if a.is_dir]
            # For the asset list, we switch to a public meta object
            metas = {asset_id: self.get_asset_meta(project_id, asset_id, store_id, ignore_errors=True) for asset_id in assets}
            return [_format(name, meta) for name, meta in metas.items() if result_filter(meta)]
        except:
            logging.error("Error while trying to list assets. Error: %s", sys.exc_info()[1])
            return []

        # List the assets in an s3 bucket

    def list_files(self, project_id: str, asset_id: str, store_id: str = None) -> List[Dict]:
        client = self._get_connection(store_id)
        try:
            meta = self.get_asset_meta(store_id=store_id, project_id=project_id, asset_id=asset_id)
            prefix = asset_id + "/" + str(meta.version) + "/"

            result = []
            for a in client.list_objects(project_id, prefix=prefix, recursive=True):
                if len(result) > MAX_LIST_ITEMS:
                    break

                if not a.is_dir:
                    result.append({
                        "name": a.object_name[len(prefix):],
                        "url": meta.proxy_url + project_id + "/" + a.object_name,
                        "default": meta.filename == a.object_name[len(prefix):]
                    })

            return result
        except:
            logging.error("Error while trying to list assets. Error: %s", sys.exc_info()[1])
            return []

    def check_exists(self, project_id: str, store_id: str = None) -> bool:
        client = self._get_connection(store_id)
        try:
            return client.bucket_exists(project_id)
        except ResponseError:
            logging.error("Error while trying to check exists. Error: %s", sys.exc_info()[1])
            return False

    def create_project(self, project_id: str, store_id: str = None) -> None:
        client = self._get_connection(store_id)
        try:
            client.make_bucket(project_id, location=_DEFAULT_STORE_LOCATION)
        except ResponseError:
            logging.error("Error while trying to create project. Error: %s", sys.exc_info()[1])
            raise ValidationError("Unable to create project on remote storage. Please check the project name.")

    def create_asset(self, project_id: str, meta: OveAssetMeta, store_id: str = None) -> OveAssetMeta:
        client = self._get_connection(store_id)
        meta.proxy_url = self._get_proxy_url(store_id)
        try:
            # minio interprets the slash as a directory
            meta_name = meta.id + S3_SEPARATOR + OVE_META
            data, size = _encode_json(meta.to_json())
            client.put_object(project_id, meta_name, data, size)
            meta.created()
            self.set_asset_meta(store_id=store_id, project_id=project_id, asset_id=meta.id, meta=meta)
            return meta
        except ResponseError:
            logging.error("Error while trying to create asset. Error: %s", sys.exc_info()[1])
            raise ValidationError("Unable to create asset on remote storage. Please check the asset name.")

    def upload_asset(self, project_id: str, asset_id: str, filename: str, upload_filename: str, store_id: str = None) -> None:
        client = self._get_connection(store_id)
        try:
            # filesize=os.stat(upfile.name).st_size
            filepath = asset_id + S3_SEPARATOR + filename
            client.fput_object(project_id, filepath, upload_filename)
        except ResponseError:
            logging.error("Error while trying to upload. Error: %s", sys.exc_info()[1])
            raise ValidationError("Unable to upload asset to remote storage.")

    def download_asset(self, project_id: str, asset_id: str, filename: str, down_filename: str, store_id: str = None) -> None:
        client = self._get_connection(store_id)
        try:
            # filesize=os.stat(upfile.name).st_size
            filepath = asset_id + S3_SEPARATOR + filename
            client.fget_object(project_id, filepath, down_filename)
        except ResponseError:
            logging.error("Error while trying to download. Error: %s", sys.exc_info()[1])
            raise ValidationError("Unable to download asset from remote storage.")

    def has_project_meta(self, project_id: str, store_id: str = None) -> bool:
        client = self._get_connection(store_id)
        try:
            logging.debug('Checking if project meta exists...')
            response = client.get_object(project_id, OVE_META)
            return 200 <= response.status < 300
        except:
            return False

    def get_project_meta(self, project_id: str, store_id: str = None, ignore_errors: bool = False) -> Union[None, OveProjectMeta]:
        client = self._get_connection(store_id)
        try:
            obj = _decode_json(client.get_object(project_id, PROJECT_FILE))['Metadata']
            result = OveProjectMeta(**obj)
            result.id = project_id

            project_info = self.get_object_info(store_id=store_id, project_id=project_id, object_id="project")
            result.url = project_info.get("index_file", "") if project_info else ""
            return result
        except:
            if ignore_errors:
                return OveProjectMeta(id=project_id, name=project_id)
            else:
                logging.error("Error while trying to get project meta. Error: %s", sys.exc_info()[1])
                raise InvalidProjectError(store_id=store_id, project_id=project_id)

    def set_project_meta(self, project_id: str, meta: OveProjectMeta, store_id: str = None, ignore_errors: bool = False) -> None:
        client = self._get_connection(store_id)
        try:
            try:
                project = _decode_json(client.get_object(project_id, PROJECT_FILE))
            except NoSuchKey:
                project = PROJECT_BASIC_TEMPLATE

            if PROJECT_METADATA_SECTION not in project.keys():
                project[PROJECT_METADATA_SECTION] = {}

            for field in OveProjectMeta.EDITABLE_FIELDS:
                project[PROJECT_METADATA_SECTION][field] = getattr(meta, field, '')

            data, size = _encode_json(project)
            client.put_object(project_id, PROJECT_FILE, data, size)
        except:
            if not ignore_errors:
                logging.error("Error while trying to set project meta. Error: %s", sys.exc_info()[1])
                raise InvalidProjectError(store_id=store_id, project_id=project_id)

    def get_project_access_meta(self, store_id: str, project_id: str) -> Union[None, OveProjectAccessMeta]:
        client = self._get_connection(store_id)
        try:
            params = _decode_json(client.get_object(project_id, OVE_META))
            return OveProjectAccessMeta(**params)
        except:
            return OveProjectAccessMeta()

    def set_project_access_meta(self, store_id: str, project_id: str, meta: OveProjectAccessMeta) -> None:
        client = self._get_connection(store_id)
        try:
            data, size = _encode_json(meta.to_json())
            client.put_object(project_id, OVE_META, data, size)
        except:
            logging.error("Error while trying to set project meta. Error: %s", sys.exc_info()[1])

    def has_access(self, store_id: str, project_id: str, groups: List[str], is_admin: bool) -> bool:
        if is_admin:
            return True

        if groups is None or len(groups) == 0:
            return False

        meta = self.get_project_access_meta(store_id=store_id, project_id=project_id)
        return any(group in groups for group in meta.groups)

    def has_asset_meta(self, project_id: str, asset_id: str, store_id: str = None) -> bool:
        client = self._get_connection(store_id)
        try:
            meta_name = asset_id + S3_SEPARATOR + OVE_META
            logging.debug('Checking if asset exists...')
            response = client.get_object(project_id, meta_name)
            return 200 <= response.status < 300
        except:
            return False

    def get_asset_meta(self, project_id: str, asset_id: str, store_id: str = None, ignore_errors: bool = False) -> Union[None, OveAssetMeta]:
        client = self._get_connection(store_id)
        try:
            meta_name = asset_id + S3_SEPARATOR + OVE_META
            logging.debug('Checking if asset exists')
            obj = _decode_json(client.get_object(project_id, meta_name))
            meta = OveAssetMeta(**obj)
            meta.id = asset_id
            return meta
        except:
            if ignore_errors:
                return None
            else:
                logging.error("Error while trying to get asset meta. Error: %s", sys.exc_info()[1])
                raise InvalidAssetError(store_id=store_id, project_id=project_id, asset_id=asset_id)

    def set_asset_meta(self, project_id: str, asset_id: str, meta: OveAssetMeta, store_id: str = None, ignore_errors: bool = False) -> None:
        client = self._get_connection(store_id)
        try:
            meta_name = asset_id + S3_SEPARATOR + OVE_META
            data, size = _encode_json(meta.to_json())
            client.put_object(project_id, meta_name, data, size)
        except:
            if not ignore_errors:
                logging.error("Error while trying to set asset meta. Error: %s", sys.exc_info()[1])
                raise InvalidAssetError(store_id=store_id, project_id=project_id, asset_id=asset_id)

    def project_type(self, store_id: str, project_id: str) -> str:
        project = self.get_object(store_id=store_id, project_id=project_id, object_id="project", ignore_errors=True)
        if project:
            meta = project.get(PROJECT_METADATA_SECTION, None)
            if meta:
                controller = meta.get("controller", None)
                if controller:
                    return "controller"

            sections = project.get(PROJECT_SECTIONS, [])
            if len(sections) > 0:
                return "launcher"

        return "none"

    def has_object(self, project_id: str, object_id: str, store_id: str = None) -> bool:
        _validate_object_id(store_id=store_id, project_id=project_id, object_id=object_id)

        client = self._get_connection(store_id)
        try:
            logging.debug('Checking if object exists ...')
            response = client.get_object(project_id, object_id + S3_OBJECT_EXTENSION)
            return 200 <= response.status < 300
        except:
            return False

    def get_object(self, project_id: str, object_id: str, store_id: str = None, ignore_errors: bool = False) -> Union[None, Dict]:
        _validate_object_id(store_id=store_id, project_id=project_id, object_id=object_id)

        client = self._get_connection(store_id)
        try:
            return _decode_json(client.get_object(project_id, object_id + S3_OBJECT_EXTENSION))
        except Exception:
            if ignore_errors:
                return None
            else:
                logging.error("Error while trying to get object. Error: %s", sys.exc_info()[1])
                raise InvalidObjectError(store_id=store_id, project_id=project_id, object_id=object_id)

    def get_object_info(self, project_id: str, object_id: str, store_id: str = None) -> Union[None, Dict]:
        if self.has_object(store_id=store_id, project_id=project_id, object_id=object_id):
            return {
                "name": object_id,
                "index_file": append_slash(self._get_proxy_url(store_id=store_id)) + project_id + "/" + object_id + S3_OBJECT_EXTENSION
            }
        else:
            return None

    def set_object(self, project_id: str, object_id: str, object_data: Dict, store_id: str = None) -> None:
        _validate_object_id(store_id=store_id, project_id=project_id, object_id=object_id)

        client = self._get_connection(store_id)
        try:
            data, size = _encode_json(object_data)
            client.put_object(project_id, object_id + S3_OBJECT_EXTENSION, data, size)
        except Exception:
            logging.error("Error while trying to set object. Error: %s", sys.exc_info()[1])
            raise InvalidObjectError(store_id=store_id, project_id=project_id, object_id=object_id)

    def get_stream(self, store_id: str, project_id: str, path_name: str) -> io.FileIO:
        client = self._get_connection(store_id)
        try:
            return client.get_object(project_id, path_name)
        except Exception:
            logging.error("Error while trying to get stream. Error: %s", sys.exc_info()[1])
            raise StreamNotFoundError(store_id=store_id, project_id=project_id, filename=path_name)

    def get_stream_meta(self, store_id: str, project_id: str, path_name: str) -> Dict:
        client = self._get_connection(store_id)
        try:
            obj = client.stat_object(project_id, path_name)
            return {"size": obj.size, "last_modified": obj.last_modified}
        except Exception:
            logging.error("Error while trying to get stream metadata. Error: %s", sys.exc_info()[1])
            raise StreamNotFoundError(store_id=store_id, project_id=project_id, filename=path_name)


# Helpers
def _validate_object_id(store_id: str, project_id: str, object_id: str) -> None:
    if not object_id or not object_id.isalnum():
        raise InvalidObjectError(store_id=store_id, project_id=project_id, object_id=object_id)


def _encode_json(data: Any) -> Tuple[io.BytesIO, int]:
    encoded = io.BytesIO(json.dumps(data).encode(encoding=_DEFAULT_OBJECT_ENCODING))
    size = encoded.getbuffer().nbytes
    return encoded, size


def _decode_json(response: HTTPResponse) -> Dict:
    return json.load(io.TextIOWrapper(response, encoding=_DEFAULT_OBJECT_ENCODING))
