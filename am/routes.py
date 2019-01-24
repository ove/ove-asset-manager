# RESTful API providing asset management capability
# Written using Falcon
# Author: David Akroyd
import logging
from functools import partial
from typing import Callable

import falcon
import tempfile
import re

from am.entities import OveMeta
from am.fileStoreInterpret import FileController
from am.util import is_empty


class StoreList:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, req, resp):
        resp.body = 'Listing of available file stores is not yet implemented'
        resp.status = falcon.HTTP_200


class WorkersList:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, req, resp):
        resp.body = 'Listing of available file workers is not yet implemented'
        resp.status = falcon.HTTP_200


class ProjectList:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, req, resp, store_id):
        resp.media = self._controller.list_projects(store_id)
        resp.status = falcon.HTTP_200


class ProjectCreate:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req, resp, store_id):
        try:
            project_name = req.media.get('name')
        except KeyError:
            raise falcon.HTTPBadRequest('Missing Name', 'A Project name is required')

        try:
            result = self._controller.create_project(store_name=store_id, project_name=project_name)
            # todo; refactor this into an error code/state
            if not result.success and result.message == "This project name already exists":
                raise falcon.HTTPConflict('This project name is already in use')
            elif not result.success:
                logging.debug(result.message)
                raise falcon.HTTPBadRequest("400 Bad Request",
                                            "There was an error creating your project, please check your name")

            resp.media = {'Project': project_name}
            resp.status = falcon.HTTP_200
        except KeyError:
            raise falcon.HTTPBadRequest('This went really badly wrong')


class AssetListAll:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, req, resp, store_id, project_id):
        resp.media = self._controller.list_all_assets(store_name=store_id, project_name=project_id)
        resp.status = falcon.HTTP_200


class AssetList:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, req, resp, store_id, project_id):
        resp.media = self._controller.list_assets(project_name=project_id, store_name=store_id)
        resp.status = falcon.HTTP_200


class AssetCreate:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req, resp, store_id, project_id):
        try:
            asset_name = req.media.get('name')
        except KeyError:
            raise falcon.HTTPBadRequest('Missing Name', 'A valid asset name is required')
        try:
            meta = OveMeta()
            meta.name = asset_name
            result = self._controller.create_asset(store_name=store_id, project_name=project_id, meta=meta)
            # todo; refactor this into an error code/state
            if not result.status and result.message == "This asset already exists":
                raise falcon.HTTPConflict("This asset already exists")
            elif not result.status:
                logging.debug(result.message)
                raise falcon.HTTPBadRequest("There was an error creating your asset")

            resp.media = {'Asset': asset_name}
            resp.status = falcon.HTTP_200
        except KeyError:
            raise falcon.HTTPBadRequest('This went very wrong')


class AssetUpload:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req, resp, store_id, project_id, asset_id):
        try:
            # retrieve the existing meta data
            result = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
            if not result.success:
                raise falcon.HTTPBadRequest("You have not created this asset yet")
            if result.data.uploaded:
                raise falcon.HTTPConflict("This asset already has a file - if you wish to change this file, use update")

            if req.get_header('content-disposition') is not None:
                fname = re.findall("filename=(.+)", req.get_header('content-disposition'))
                if is_empty(fname) is True:
                    raise falcon.HTTPInvalidHeader("No filename specified in header", 'content-disposition')

                fname = fname[0]
                fname = (fname.encode('ascii', errors='ignore').decode()).strip('\"')
                if is_empty(fname):
                    raise falcon.HTTPInvalidHeader("No valid filename specified in header", 'content-disposition')

                if fname == '.ovemeta':
                    raise falcon.HTTPForbidden("403 Forbidden",
                                               "This is a reserved filename and is not allowed as an asset name")
            else:
                raise falcon.HTTPBadRequest("No filename specified -"
                                            " this should be in the content-disposition header")
            with tempfile.NamedTemporaryFile() as cache:
                cache.write(req.stream.read())
                cache.flush()
                result = result.data
                self._controller.upload_asset(store_name=store_id, project_name=project_id, asset_name=asset_id,
                                              filename=fname, meta=result, file=cache)

            resp.media = {'Asset': fname}
            resp.status = falcon.HTTP_200
        except KeyError:
            raise falcon.HTTPBadRequest('This went very wrong')


class AssetCreateUpload:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        try:
            # retrieve the existing meta data
            result = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
            if not result.success:
                result = self._controller.create_asset(store_name=store_id, project_name=project_id,
                                                       meta=OveMeta(name=asset_id))
                if not result.success:
                    raise falcon.HTTPError(result.status, result.message)

            elif result.data.uploaded:
                raise falcon.HTTPConflict("This asset already has a file - if you wish to change this file, use update")

            filename = _parse_filename(req)
            _save_filename(partial(self._controller.upload_asset, store_name=store_id, project_name=project_id,
                                   asset_name=asset_id, filename=filename, meta=result.data), req)

            resp.media = {'Asset': filename}
            resp.status = falcon.HTTP_200
        except KeyError:
            raise falcon.HTTPBadRequest('This went very wrong')


class MetaEdit:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, req, resp, store_id, project_id, asset_id):
        try:
            result = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
            if not result.success:
                raise falcon.HTTPBadRequest("Could not access asset - please check your filename")

            resp.media = result.data.__dict__
            resp.status = falcon.HTTP_200
        except KeyError:
            raise falcon.HTTPBadRequest('This went very wrong')

    def on_post(self, req, resp, store_id, project_id, asset_id):
        try:
            result = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
            if not result.success:
                raise falcon.HTTPBadRequest("Could not access asset - please check your filename")
            # We input the old meta file, change the options, then re-write it to avoid deleting previous meta
            meta = result.data
            if is_empty(req.media.get('name')) is False:
                meta.setName(req.media.get('name'))
            if is_empty(req.media.get('description')) is False:
                meta.setDescription(req.media.get('description'))
            # There are issues checking whether a boolean is empty, since a False entry is the same as empty
            # if is_empty(bool(req.media.get('uploaded'))) is True:
            #     meta.isUploaded(bool(req.media.get('uploaded')))
            #     print(bool(req.media.get('uploaded')))
            setmeta = self._controller.edit_asset_meta(store_name=store_id, project_name=project_id,
                                                       asset_name=asset_id, meta=meta)
            if not setmeta.status:
                raise falcon.HTTPBadRequest("Could not access asset - please check your filename")

            resp.media = meta.__dict__
            resp.status = falcon.HTTP_200
        except KeyError:
            raise falcon.HTTPBadRequest('This went very wrong - please check your meta is correct')


def _parse_filename(req: falcon.Request) -> str:
    if req.get_header('content-disposition'):
        filename = re.findall("filename=(.+)", req.get_header('content-disposition'))
        if is_empty(filename):
            raise falcon.HTTPInvalidHeader("No filename specified in header", 'content-disposition')

        filename = filename[0]
        filename = (filename.encode('ascii', errors='ignore').decode()).strip('\"')
        if is_empty(filename):
            raise falcon.HTTPInvalidHeader("No valid filename specified in header", 'content-disposition')

        if filename == '.ovemeta':
            raise falcon.HTTPForbidden("403 Forbidden",
                                       "This is a reserved filename and is not allowed as an asset name")

        return filename
    else:
        raise falcon.HTTPBadRequest("No filename specified -"
                                    " this should be in the content-disposition header")


def _save_filename(save_fn: Callable, req: falcon.Request):
    with tempfile.NamedTemporaryFile() as cache:
        cache.write(req.stream.read())
        cache.flush()
        save_fn(file=cache)
