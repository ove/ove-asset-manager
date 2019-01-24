# Module to allow connection to interpret connection to different store types
# Additonally acts as a transformer for multiple s3 APIs including Minio and AWS implementations
from typing import Dict

import logging
import sys

import falcon

from am.entities import OveMeta, ApiResult
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
        return self._manager.list_all_assets(project_name, store_name=store_name)

    # todo; figure out what this config does
    def show_meta(self, projectId: str, assetId: str, store_name: str = None) -> bool:
        return True

    def create_project(self, project_name: str, store_name: str = None) -> ApiResult:
        try:
            if self._manager.check_exists(project_name, store_name=store_name):
                return ApiResult(success=False, message="This project name already exists")
            else:
                self._manager.create_project(project_name, store_name=store_name)
                return ApiResult(success=True, message="Successfully created new project")
        except Exception as error:
            logging.error("Error while trying to create project. Error: %s", sys.exc_info()[1])
            return ApiResult(success=False, message=str(error))

    def create_asset(self, project_name: str, meta: OveMeta, store_name: str = None) -> ApiResult:
        try:
            return self._manager.create_asset(project_name, meta, store_name=store_name)
        except Exception as error:
            logging.error("Error while trying to create asset. Error: %s", sys.exc_info()[1])
            return ApiResult(success=False, message=str(error), status=falcon.HTTP_400)

    def upload_asset(self, project_name: str, asset_name: str, filename: str, meta: OveMeta, file,
                     store_name: str = None) -> ApiResult:
        try:
            result = self._manager.upload_asset(project_name, asset_name, filename, file, store_name=store_name)
            logging.debug("Setting uploaded flag to True")
            meta.uploaded = True
            self._manager.set_asset_meta(project_name, asset_name, meta, store_name=store_name)
            return result
        except Exception as error:
            logging.error("Error while trying to upload asset. Error: %s", sys.exc_info()[1])
            return ApiResult(success=False, message=str(error))

    def get_asset_meta(self, project_name: str, asset_name: str, store_name: str = None) -> ApiResult:
        try:
            result = self._manager.get_asset_meta(project_name, asset_name, store_name=store_name)
            if not result.success:
                logging.debug(result.message)
            return result
        except Exception as error:
            logging.error("Error while trying to get asset meta. Error: %s", sys.exc_info()[1])
            return ApiResult(success=False, message=str(error))

    def edit_asset_meta(self, project_name: str, asset_name: str, meta: OveMeta, store_name: str = None) -> ApiResult:
        try:
            result = self._manager.set_asset_meta(project_name, asset_name, meta, store_name=store_name)
            if not result.success:
                logging.debug(result.message)
            return result
        except Exception as error:
            logging.error("Error while trying to edit asset meta. Error: %s", sys.exc_info()[1])
            return ApiResult(success=False, message=str(error))
