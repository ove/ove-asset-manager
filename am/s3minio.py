# s3miniomodule for accessing object stores that are compatible with the minio sdk
# requires pip install minio
from typing import Union, Dict, Tuple

import logging
import sys
import io
import json

from minio import Minio
from minio.error import ResponseError

_DEFAULT_CONFIG = "config/credentials.json"


# Open a connection to the S3 storage
# todo; refactor this into a storage manager and reuse connections
def open_connection(store_name: str = None) -> Union[Minio, None]:
    try:
        with open(_DEFAULT_CONFIG, mode="r") as fin:
            config = json.loads(fin.read())

            default_store = config.get("default", None)
            store_name = store_name if store_name else default_store

            for client_config in config.get("stores", []):
                if store_name == client_config.get("name", ""):
                    return Minio(endpoint=client_config.get("store", ""),
                                 access_key=client_config.get("accessKey", ""),
                                 secret_key=client_config.get("secretKey", ""),
                                 secure=False)
            return None
    except:
        logging.error("Error while trying to open store connection. Error: %s", sys.exc_info()[1])


# List the projects in an s3 storage (returning the names)
def list_projects() -> Dict:
    try:
        client = open_connection()
        buckets = client.list_buckets()
        return {'Projects': [bucket.name for bucket in buckets]}
    except:
        logging.error("Error while trying to list store. Error: %s", sys.exc_info()[1])


# List the assets in an s3 bucket
def list_assets(project_name: str) -> Dict:
    try:
        client = open_connection()
        assets = client.list_objects(project_name, prefix=None, recursive=False)
        return {'Assets': [asset.object_name[0:-1] for asset in assets if asset.is_dir]}
    except:
        logging.error("Error while trying to list assets. Error: %s", sys.exc_info()[1])


def check_exists(project_name: str) -> bool:
    try:
        client = open_connection()
        return client.bucket_exists(project_name)
    except ResponseError:
        logging.error("Error while trying to check exists. Error: %s", sys.exc_info()[1])
        return False


def create_project(name: str) -> bool:
    try:
        client = open_connection()
        client.make_bucket(name, location='us-east-1')
        return True
    except ResponseError:
        logging.error("Error while trying to create project. Error: %s", sys.exc_info()[1])
        return False


def create_asset(project_name: str, defmeta) -> Tuple[bool, str]:
    try:
        client = open_connection()
        # minio interprets the slash as a directory
        meta_name = defmeta.name + '/' + '.ovemeta'
        # We create the meta file at the same time
        if get_asset_meta(project_name, defmeta.name, defmeta)[0] is True:
            return False, "This asset already exists"
        # We make a file stream and write it to the s3 storage
        print("Meta class working", defmeta.name)
        temp_meta = io.BytesIO(json.dumps(defmeta.__dict__).encode())
        file_size = temp_meta.getbuffer().nbytes
        print(client.put_object(project_name, meta_name, temp_meta, file_size))
        return True, "Asset created"
    except ResponseError as err:
        return False, str(err)


def upload_asset(project_name: str, asset_name: str, filename: str, upfile) -> Tuple[bool, str]:
    try:
        client = open_connection()
        # filesize=os.stat(upfile.name).st_size
        filepath = asset_name + '/' + filename
        print(client.fput_object(project_name, filepath, upfile.name))
        return True, "Asset uploaded"
    except ResponseError as err:
        return False, str(err)


def get_asset_meta(project_name: str, asset_name: str, meta) -> Tuple[bool, str]:
    try:
        client = open_connection()
        meta_name = asset_name + '/' + '.ovemeta'
        print('Checking if asset exists')
        getmeta = client.get_object(project_name, meta_name)
        temp1 = io.BytesIO(getmeta.read())
        tempmeta = json.loads(temp1.read())
        meta.setName(tempmeta['name'])
        meta.setDescription(tempmeta['description'])
        meta.isUploaded(tempmeta['uploaded'])
        meta.setPermissions(tempmeta['permissions'])
        return True, meta
    except Exception as err:
        print("Check asset error is", err)
        return False, str(err)


def set_asset_meta(project_name: str, asset_name: str, meta) -> Tuple[bool, str]:
    try:
        client = open_connection()
        meta_name = asset_name + '/' + '.ovemeta'
        temp_meta = io.BytesIO(json.dumps(meta.__dict__).encode())
        filesize = temp_meta.getbuffer().nbytes
        print(client.put_object(project_name, meta_name, temp_meta, filesize))
        return True, temp_meta
    except Exception as err:
        print("Check asset error is", err)
        return False, err
