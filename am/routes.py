# RESTful API providing asset management capability
# Written using Falcon
# Author: David Akroyd

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
            create_project = self._controller.create_project(store_name=store_id, project_name=project_name)
            if create_project[0] is False and create_project[1] == "This project name already exists":
                raise falcon.HTTPConflict('This project name is already in use')
            elif create_project[0] is False:
                print(create_project[1])
                raise falcon.HTTPBadRequest("400 Bad Request",
                                            "There was an error creating your project, please check your name")
        except KeyError:
            raise falcon.HTTPBadRequest('This went really badly wrong')

        resp.media = {'Project': project_name}
        resp.status = falcon.HTTP_200


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
            if result[0] is False and result[1] == "This asset already exists":
                raise falcon.HTTPConflict("This asset already exists")
            elif result[0] is False:
                print(result[1])
                raise falcon.HTTPBadRequest("There was an error creating your asset")
        except KeyError:
            raise falcon.HTTPBadRequest('This went very wrong')

        resp.media = {'Asset': asset_name}
        resp.status = falcon.HTTP_200


class AssetUpload:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req, resp, store_id, project_id, asset_id):
        try:
            # retrieve the existing meta data
            meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id,
                                                   meta=OveMeta())
            if meta[0] is False:
                raise falcon.HTTPBadRequest("You have not created this asset yet")
            if meta[1].uploaded is True:
                raise falcon.HTTPConflict("This asset already has a file - if you wish to change this file, use update")
            if req.get_header('content-disposition') is not None:
                fname = re.findall("filename=(.+)", req.get_header('content-disposition'))
                if is_empty(fname) is True:
                    raise falcon.HTTPInvalidHeader("No filename specified in header", 'content-disposition')
                fname = fname[0]
                fname = (fname.encode('ascii', errors='ignore').decode()).strip('\"')
                if fname == '.ovemeta':
                    raise falcon.HTTPForbidden("403 Forbidden",
                                               "This is a reserved filename and is not allowed as an asset name")
            else:
                raise falcon.HTTPBadRequest("No filename specified -"
                                            " this should be in the content-disposition header")
            with tempfile.NamedTemporaryFile() as cache:
                cache.write(req.stream.read())
                cache.flush()
                meta = meta[1]
                self._controller.upload_asset(store_name=store_id, project_name=project_id, asset_name=asset_id,
                                              filename=fname, meta=meta, file=cache)
        except KeyError:
            raise falcon.HTTPBadRequest('This went very wrong')
        resp.media = {'Asset': fname}
        resp.status = falcon.HTTP_200


class MetaEdit:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, req, resp, store_id, project_id, asset_id):
        try:
            meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id,
                                                   meta=OveMeta())
            if meta[0] is False:
                raise falcon.HTTPBadRequest("Could not access asset - please check your filename")
        except KeyError:
            raise falcon.HTTPBadRequest('This went very wrong')
        resp.media = meta[1].__dict__
        resp.status = falcon.HTTP_200

    def on_post(self, req, resp, store_id, project_id, asset_id):
        try:
            meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id,
                                                   meta=OveMeta())
            if meta[0] is False:
                raise falcon.HTTPBadRequest("Could not access asset - please check your filename")
            # We input the old meta file, change the options, then re-write it to avoid deleting previous meta
            meta = meta[1]
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
            if setmeta[0] is False:
                raise falcon.HTTPBadRequest("Could not access asset - please check your filename")
        except KeyError:
            raise falcon.HTTPBadRequest('This went very wrong - please check your meta is correct')
        resp.media = meta[1].__dict__
        resp.status = falcon.HTTP_200
