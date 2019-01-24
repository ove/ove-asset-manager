# Module to allow connection to interpret connection to different store types
# Additonally acts as a transformer for multiple s3 APIs including Minio and AWS implementations
from typing import Dict, Tuple, Union

import logging
import sys

from am.entities import OveMeta
from am.s3minio import S3Manager


class FileController:
    def __init__(self, store_type: str = "s3"):
        if store_type == "s3":
            self._manager = S3Manager()
            self._manager.load()
        else:
            raise ValueError("Invalid store type provided")

    # List the projects in an storage (returning the names)
    def list_projects(self, store_name: str = None) -> Dict:
        return self._manager.list_projects(store_name=store_name)

    def list_assets(self, project_name: str, store_name: str = None) -> Dict:
        return self._manager.list_assets(project_name, store_name=store_name)

    # List the assets in an s3 bucket
    def list_all_assets(self, project_name: str, store_name: str = None) -> Dict:
        return self._manager.list_assets(project_name, store_name=store_name)

    # todo; figure out what this config does
    def show_meta(self, projectId: str, assetId: str, store_name: str = None) -> bool:
        return True

    def create_project(self, project_name: str, store_name: str = None) -> Tuple[bool, str]:
        try:
            if self._manager.check_exists(project_name, store_name=store_name):
                return False, "This project name already exists"
            else:
                self._manager.create_project(project_name, store_name=store_name)
                return True, "Successfully created new project"
        except Exception as error:
            logging.error("Error while trying to list store. Error: %s", sys.exc_info()[1])
            return False, str(error)

    def create_asset(self, project_name: str, meta: OveMeta, store_name: str = None) -> Tuple[bool, str]:
        try:
            return self._manager.create_asset(project_name, meta, store_name=store_name)
        except Exception as error:
            logging.error("Error while trying to list store. Error: %s", sys.exc_info()[1])
            return False, str(error)

    def upload_asset(self, project_name: str, asset_name: str, filename: str, meta: OveMeta, file,
                     store_name: str = None) -> Tuple[bool, str]:
        try:
            result = self._manager.upload_asset(project_name, asset_name, filename, file, store_name=store_name)
            logging.debug("Setting uploaded flag to True")
            meta.isUploaded(True)
            self._manager.set_asset_meta(project_name, asset_name, meta, store_name=store_name)
            return result
        except Exception as error:
            logging.error("Error while trying to list store. Error: %s", sys.exc_info()[1])
            return False, str(error)

    def get_asset_meta(self, project_name: str, asset_name: str, meta: OveMeta,
                       store_name: str = None) -> Tuple[bool, Union[str, OveMeta]]:
        try:
            result = self._manager.get_asset_meta(project_name, asset_name, meta, store_name=store_name)
            if not result[0]:
                logging.debug(result[1])
            return result
        except Exception as error:
            logging.error("Error while trying to list store. Error: %s", sys.exc_info()[1])
            return False, str(error)

    def edit_asset_meta(self, project_name: str, asset_name: str, meta: OveMeta,
                        store_name: str = None) -> Tuple[bool, str]:
        try:
            result = self._manager.set_asset_meta(project_name, asset_name, meta, store_name=store_name)
            if not result[0]:
                logging.debug(result[1])
            return result
        except Exception as error:
            logging.error("Error while trying to list store. Error: %s", sys.exc_info()[1])
            return False, str(error)
