# RESTful API providing asset management capability
# Written using Falcon
# Author: David Akroyd
# Contributor: Ovidiu Serban
from functools import partial

import falcon

from am.controller import FileController
from am.managers import WorkerManager
from common.entities import OveMeta, WorkerStatus
from common.entities import WorkerData
from common.errors import InvalidAssetError, ValidationError
from common.falcon_utils import parse_filename, save_filename
from common.filters import build_meta_filter
from common.util import is_empty, to_bool
from common.validation import validate_not_null, validate_no_slashes, validate_list


class StoreList:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response):
        resp.media = self._controller.list_stores()
        resp.status = falcon.HTTP_200


class WorkersEdit:
    def __init__(self, worker_manager: WorkerManager):
        self._worker_manager = worker_manager

    def on_get(self, req: falcon.Request, resp: falcon.Response):
        resp.media = self._worker_manager.worker_info(name=req.params.get("name", None))
        resp.status = falcon.HTTP_200

    def on_post(self, req: falcon.Request, resp: falcon.Response):
        worker = WorkerData(**req.media)
        self._worker_manager.add_worker(worker)

        resp.media = worker.to_public_json()
        resp.status = falcon.HTTP_200

    def on_delete(self, req: falcon.Request, resp: falcon.Response):
        validate_not_null(req.media, 'name')
        self._worker_manager.remove_worker(name=req.media.get('name'))

        resp.media = {"status": "OK"}
        resp.status = falcon.HTTP_200

    def on_patch(self, req: falcon.Request, resp: falcon.Response):
        validate_not_null(req.media, 'name')
        validate_not_null(req.media, 'status')
        self._worker_manager.update(name=req.media.get("name"), status=WorkerStatus(req.media.get("status")), error_msg=req.media.get("error_msg", ""))

        resp.media = {'Status': 'OK'}
        resp.status = falcon.HTTP_200


class WorkersStatusRoute:
    def __init__(self, worker_manager: WorkerManager):
        self._worker_manager = worker_manager

    def on_get(self, req: falcon.Request, resp: falcon.Response):
        resp.media = self._worker_manager.worker_status(name=req.params.get("name", None))
        resp.status = falcon.HTTP_200

    def on_post(self, req: falcon.Request, resp: falcon.Response):
        self._worker_manager.reset_worker_status(name=req.params.get("name", None))

        resp.media = self._worker_manager.worker_status(name=req.params.get("name", None))
        resp.status = falcon.HTTP_200


class WorkerSchedule:
    def __init__(self, controller: FileController, worker_manager: WorkerManager):
        self._controller = controller
        self._worker_manager = worker_manager

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        validate_not_null(req.media, 'worker_type')

        meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
        self._worker_manager.schedule_process(project_name=project_id, meta=meta, worker_type=req.media.get("worker_type"),
                                              store_config=self._controller.get_store_config(store_name=store_id),
                                              task_options=req.media.get("parameters", dict()))

        resp.media = {'Status': 'OK'}
        resp.status = falcon.HTTP_200


class ProjectList:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, req: falcon.Request, resp: falcon.Response, store_id: str):
        metadata = to_bool(req.params.get("metadata", False))
        resp.media = self._controller.list_projects(store_name=store_id, metadata=metadata)
        resp.status = falcon.HTTP_200


class ProjectCreate:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str):
        validate_not_null(req.media, 'name')
        project_name = req.media.get('name')

        self._controller.create_project(store_name=store_id, project_name=project_name)

        resp.media = {'Project': project_name}
        resp.status = falcon.HTTP_200


class AssetList:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        results_filter = build_meta_filter(req.params)
        resp.media = self._controller.list_assets(project_name=project_id, store_name=store_id, result_filter=results_filter)
        resp.status = falcon.HTTP_200


class FileList:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        resp.media = self._controller.list_files(project_name=project_id, store_name=store_id, asset_name=asset_id)
        resp.status = falcon.HTTP_200


class AssetCreate:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        validate_not_null(req.media, 'name')
        validate_no_slashes(req.media, 'name')
        asset_name = req.media.get('name')
        self._controller.create_asset(store_name=store_id, project_name=project_id, meta=OveMeta(name=asset_name, project=project_id))

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
                raise falcon.HTTPConflict(title="Asset exists", description="This asset already has a file. If you wish to change this file, please update the asset.")
        except InvalidAssetError:
            raise falcon.HTTPBadRequest(title="Asset not found", description="You have not created this asset yet.")

        filename = parse_filename(req)
        save_filename(partial(self._controller.upload_asset, store_name=store_id, project_name=project_id,
                              asset_name=asset_id, filename=filename, meta=meta), req)

        resp.media = {'Asset': asset_id, 'Filename': filename}
        resp.status = falcon.HTTP_200


class AssetUpdate:
    # this will be validated by the RequireJSON middleware as a custom content-type, otherwise is json
    content_type = 'application/octet-stream'

    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        # retrieve the existing meta data
        try:
            meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
            if meta.uploaded is False:
                raise falcon.HTTPConflict(title="Asset not found", description="This asset has not been uploaded yet")

        except InvalidAssetError:
            raise falcon.HTTPBadRequest(title="Asset not found", description="You have not created this asset yet")
        filename = parse_filename(req)
        save_filename(partial(self._controller.update_asset, store_name=store_id, project_name=project_id,
                              asset_name=asset_id, filename=filename, meta=meta), req)

        resp.media = {'Asset': asset_id, 'Filename': filename}
        resp.status = falcon.HTTP_200


class AssetCreateUpload:
    # this will be validated by the RequireJSON middleware as a custom content-type, otherwise is json
    content_type = 'application/octet-stream'

    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        try:
            meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
            if meta.uploaded:
                raise falcon.HTTPConflict(title="Asset exists", description="This asset already has a file. If you wish to change this file, use update")
        except InvalidAssetError:
            meta = self._controller.create_asset(store_name=store_id, project_name=project_id, meta=OveMeta(name=asset_id, project=project_id))

        filename = parse_filename(req)
        save_filename(partial(self._controller.upload_asset, store_name=store_id, project_name=project_id,
                              asset_name=asset_id, filename=filename, meta=meta), req)

        resp.media = {'Asset': asset_id, 'Filename': filename}
        resp.status = falcon.HTTP_200


class MetaEdit:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
        resp.media = meta.to_public_json()
        resp.status = falcon.HTTP_200

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
        if is_empty(req.media.get('name')) is False:
            # todo; this needs to move the asset into a new path as well
            # todo; rebuild the path as well
            # meta.name = req.media.get('name')
            pass
        if is_empty(req.media.get('description')) is False:
            meta.description = req.media.get('description')
        if is_empty(req.media.get('tags')) is False:
            meta.tags = req.media.get('tags')

        self._controller.edit_asset_meta(store_name=store_id, project_name=project_id,
                                         asset_name=asset_id, meta=meta)

        resp.media = meta.to_public_json()
        resp.status = falcon.HTTP_200


class TagEdit:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
        resp.media = meta.tags
        resp.status = falcon.HTTP_200

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        validate_list(req.media)

        meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
        meta.tags = req.media
        self._controller.edit_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id, meta=meta)

        resp.media = meta.tags
        resp.status = falcon.HTTP_200

    def on_patch(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        validate_not_null(req.media, 'action')
        validate_not_null(req.media, 'data')
        validate_list(req.media.get('data'))

        action = req.media.get('action')
        data = req.media.get('data')

        if action not in ['add', 'remove']:
            raise ValidationError(title="Invalid action provided", description="The action should be either add or remove")

        meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)

        new_tags = set(meta.tags)
        if action == 'add':
            new_tags.update(data)
        elif action == 'remove':
            new_tags.difference_update(data)
        meta.tags = list(new_tags)

        self._controller.edit_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id, meta=meta)

        resp.media = meta.tags
        resp.status = falcon.HTTP_200

    def on_delete(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        meta = self._controller.get_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id)
        meta.tags = []
        self._controller.edit_asset_meta(store_name=store_id, project_name=project_id, asset_name=asset_id, meta=meta)

        resp.media = meta.tags
        resp.status = falcon.HTTP_200


class ObjectEdit:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_head(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, object_id: str):
        has_object = self._controller.has_object(store_name=store_id, project_name=project_id, object_name=object_id)
        resp.status = falcon.HTTP_200 if has_object else falcon.HTTP_NOT_FOUND

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


class ObjectInfo:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, object_id: str):
        resp.media = self._controller.get_object_info(store_name=store_id, project_name=project_id, object_name=object_id) or {}
        resp.status = falcon.HTTP_200
