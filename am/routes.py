# RESTful API providing asset management capability
# Written using Falcon
# Author: David Akroyd
# Contributor: Ovidiu Serban
from functools import partial
from typing import Callable

import falcon
import tempfile
import re

from am.entities import OveMeta
from am.errors import InvalidAssetError
from am.fileStoreInterpret import FileController
from am.util import is_empty
from am.validation import validate_not_null


class StoreList:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response):
        resp.body = 'Listing of available file stores is not yet implemented'
        resp.status = falcon.HTTP_200


class WorkersList:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response):
        resp.body = 'Listing of available file workers is not yet implemented'
        resp.status = falcon.HTTP_200


class ProjectList:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response, store_id: str):
        resp.media = self._controller.list_projects(store_id)
        resp.status = falcon.HTTP_200


class ProjectCreate:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str):
        validate_not_null(req, 'name')
        project_name = req.media.get('name')

        self._controller.create_project(store_name=store_id, project_name=project_name)

        resp.media = {'Project': project_name}
        resp.status = falcon.HTTP_200


class AssetList:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        include_empty = req.params.get("includeEmpty", False)
        resp.media = self._controller.list_assets(project_name=project_id, store_name=store_id, include_empty=include_empty)
        resp.status = falcon.HTTP_200


class AssetCreate:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        validate_not_null(req, 'name')
        asset_name = req.media.get('name')

        self._controller.create_asset(store_name=store_id, project_name=project_id, meta=OveMeta(name=asset_name))

        resp.media = {'Asset': asset_name}
        resp.status = falcon.HTTP_200


class AssetUpload:
    # this will be validated by the RequireJSON middleware as a custom content-type, otherwise is json
    content_type = 'application/octet-stream'

    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        # retrieve the existing meta data
        try:
            meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
            if meta.uploaded:
                raise falcon.HTTPConflict("This asset already has a file. If you wish to change this file, use update")
        except InvalidAssetError:
            raise falcon.HTTPBadRequest("You have not created this asset yet")

        filename = _parse_filename(req)
        _save_filename(partial(self._controller.upload_asset, store_name=store_id, project_name=project_id,
                               asset_name=asset_id, filename=filename, meta=meta), req)

        resp.media = {'Asset': filename}
        resp.status = falcon.HTTP_200


class AssetCreateUpload:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        try:
            meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
            if meta.uploaded:
                raise falcon.HTTPConflict("This asset already has a file. If you wish to change this file, use update")
        except InvalidAssetError:
            meta = self._controller.create_asset(store_name=store_id, project_name=project_id,
                                                 meta=OveMeta(name=asset_id))

        filename = _parse_filename(req)
        _save_filename(partial(self._controller.upload_asset, store_name=store_id, project_name=project_id,
                               asset_name=asset_id, filename=filename, meta=meta), req)

        resp.media = {'Asset': filename}
        resp.status = falcon.HTTP_200


class MetaEdit:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
        resp.media = meta.__dict__
        resp.status = falcon.HTTP_200

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
        if is_empty(req.media.get('name')) is False:
            meta.name = req.media.get('name')
        if is_empty(req.media.get('description')) is False:
            meta.description = req.media.get('description')
        # There are issues checking whether a boolean is empty, since a False entry is the same as empty
        # if is_empty(bool(req.media.get('uploaded'))) is True:
        #     meta.isUploaded(bool(req.media.get('uploaded')))
        #     print(bool(req.media.get('uploaded')))
        self._controller.edit_asset_meta(store_name=store_id, project_name=project_id,
                                         asset_name=asset_id, meta=meta)
        resp.media = meta.__dict__
        resp.status = falcon.HTTP_200


class ObjectEdit:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, object_id: str):
        resp.media = self._controller.get_object(store_name=store_id, project_name=project_id, object_name=object_id)
        resp.status = falcon.HTTP_200

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, object_id: str):
        self._controller.set_object(store_name=store_id, project_name=project_id, object_name=object_id, object_data=req.media, update=False)
        resp.media = {'Status': 'OK'}
        resp.status = falcon.HTTP_200

    def on_put(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, object_id: str):
        self._controller.set_object(store_name=store_id, project_name=project_id, object_name=object_id, object_data=req.media, update=True)
        resp.media = {'Status': 'OK'}
        resp.status = falcon.HTTP_200


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
