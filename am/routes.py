# RESTful API providing asset management capability
# Written using Falcon
# Author: David Akroyd
# Contributor: Ovidiu Serban
import datetime
from functools import partial
from typing import List

import falcon

from am.controller import FileController
from am.managers import WorkerManager
from common.auth import AuthManager
from common.entities import OveAssetMeta, OveProjectMeta, UserAccessMeta, OveProjectAccessMeta
from common.errors import InvalidAssetError, ValidationError, MissingParameterError
from common.falcon_utils import unquote_filename, save_filename
from common.filters import build_meta_filter, DEFAULT_FILTER
from common.util import to_bool
from common.validation import validate_not_null, validate_no_slashes, validate_list


class AuthRoute:
    internal_group_validation = True

    def __init__(self, auth: AuthManager):
        self._auth = auth

    def on_post(self, req: falcon.Request, resp: falcon.Response):
        validate_not_null(req.media, 'user')
        validate_not_null(req.media, 'password')

        token = self._auth.auth_token(user=req.media.get("user"), password=req.media.get("password"))
        resp.media = {"token": token}
        resp.status = falcon.HTTP_200 if token else falcon.HTTP_401


class UserEdit:
    internal_group_validation = True

    def __init__(self, auth: AuthManager):
        self._auth = auth

    def on_get(self, req: falcon.Request, resp: falcon.Response):
        _validate_is_admin(req)

        user = req.params.get("user", None)
        resp.media = self._auth.get_user(user).public_json() if user else [user.public_json() for user in self._auth.get_users()]
        resp.status = falcon.HTTP_200

    def on_post(self, req: falcon.Request, resp: falcon.Response):
        _validate_is_admin(req)

        validate_not_null(req.media, 'user')
        validate_not_null(req.media, 'password')

        data = UserAccessMeta(**req.media)

        self._auth.edit_user(access=data, password=req.media.get("password"), add=True)
        resp.media = {"result": "OK"}
        resp.status = falcon.HTTP_200

    def on_patch(self, req: falcon.Request, resp: falcon.Response):
        _validate_is_admin(req)

        validate_not_null(req.media, 'user')

        data = self._auth.get_user(user=req.media.get("user"))
        if not data:
            raise ValidationError(title="Invalid user", description="User not found")

        for field in UserAccessMeta.EDITABLE_FIELDS:
            if req.media.get(field, None):
                setattr(data, field, req.media.get(field))

        self._auth.edit_user(access=data)
        resp.media = {"result": "OK"}
        resp.status = falcon.HTTP_200

    def on_delete(self, req: falcon.Request, resp: falcon.Response):
        _validate_is_admin(req)

        validate_not_null(req.media, 'user')

        self._auth.remove_user(user=req.media.get("user"))
        resp.media = {"result": "OK"}
        resp.status = falcon.HTTP_200


def _validate_is_admin(req: falcon.Request):
    if not getattr(req, "user_access", UserAccessMeta()).admin_access:
        raise falcon.HTTPUnauthorized(title='Access token required for ADMIN operation',
                                      description='Please provide a valid access token as part of the request.')


class GroupsInfo:
    internal_group_validation = True

    def __init__(self, auth: AuthManager):
        self._auth = auth

    def on_get(self, _req: falcon.Request, resp: falcon.Response):
        resp.media = self._auth.get_groups()
        resp.status = falcon.HTTP_200


class UserInfo:
    internal_group_validation = True

    def __init__(self, auth: AuthManager):
        self._auth = auth

    def on_get(self, req: falcon.Request, resp: falcon.Response):
        access = getattr(req, "user_access", None)
        if not access:
            raise MissingParameterError(name="user")

        resp.media = self._auth.get_user(access.user).public_json()
        resp.status = falcon.HTTP_200


class StoreList:
    internal_group_validation = True

    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response):
        resp.media = self._controller.list_stores()
        resp.status = falcon.HTTP_200


class WorkersEdit:
    internal_group_validation = True

    def __init__(self, worker_manager: WorkerManager):
        self._worker_manager = worker_manager

    def on_get(self, req: falcon.Request, resp: falcon.Response):
        resp.media = self._worker_manager.worker_info(name=req.params.get("name", None))
        resp.status = falcon.HTTP_200

    def on_delete(self, req: falcon.Request, resp: falcon.Response):
        _validate_is_admin(req)

        validate_not_null(req.media, 'name')
        self._worker_manager.remove_worker(name=req.media.get('name'))

        resp.media = {"status": "OK"}
        resp.status = falcon.HTTP_200


class WorkersStatusRoute:
    internal_group_validation = True

    def __init__(self, worker_manager: WorkerManager):
        self._worker_manager = worker_manager

    def on_get(self, req: falcon.Request, resp: falcon.Response):
        resp.media = self._worker_manager.worker_status(name=req.params.get("name", None))
        resp.status = falcon.HTTP_200


class WorkerQueue:
    internal_group_validation = True

    def __init__(self, controller: FileController, worker_manager: WorkerManager):
        self._controller = controller
        self._worker_manager = worker_manager

    def on_get(self, req: falcon.Request, resp: falcon.Response):
        resp.media = self._worker_manager.worker_queue(user=getattr(req, "user_access", UserAccessMeta()))
        resp.status = falcon.HTTP_200

    def on_post(self, req: falcon.Request, resp: falcon.Response):
        validate_not_null(req.media, 'store_id')
        validate_not_null(req.media, 'project_id')
        validate_not_null(req.media, 'asset_id')
        validate_not_null(req.media, 'worker_type')

        user = getattr(req, "user_access", UserAccessMeta())
        store_id = req.media.get("store_id")
        project_id = req.media.get("project_id")
        asset_id = req.media.get("asset_id")
        worker_type = req.media.get("worker_type")

        if not self._controller.has_access(store_id=store_id, project_id=project_id, groups=user.write_groups, is_admin=user.admin_access):
            raise falcon.HTTPUnauthorized(title="Unable to process asset", description="Insufficient write access to process asset")

        store_config = self._controller.get_store_config(store_id=store_id)
        task_options = req.media.get("parameters", dict())
        priority = req.media.get("priority", 1)

        meta = self._controller.get_asset_meta(store_id=store_id, project_id=project_id, asset_id=asset_id)
        user = getattr(req, "user_access", UserAccessMeta())
        self._worker_manager.schedule_task(store_id=store_id, project_id=project_id, meta=meta, worker_type=worker_type,
                                           username=user.user, store_config=store_config, task_options=task_options, priority=priority)

        resp.media = {'Status': 'OK'}
        resp.status = falcon.HTTP_200

    def on_delete(self, req: falcon.Request, resp: falcon.Response):
        validate_not_null(req.media, 'task_id')
        self._worker_manager.cancel_task(task_id=req.media.get('task_id'), user=getattr(req, "user_access", UserAccessMeta()))

        resp.media = {"status": "OK"}
        resp.status = falcon.HTTP_200

    def on_patch(self, req: falcon.Request, resp: falcon.Response):
        validate_not_null(req.media, 'task_id')
        self._worker_manager.reset_task(task_id=req.media.get('task_id'), user=getattr(req, "user_access", UserAccessMeta()))

        resp.media = {"status": "OK"}
        resp.status = falcon.HTTP_200


class ProjectList:
    internal_group_validation = True

    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, req: falcon.Request, resp: falcon.Response, store_id: str):
        results_filter = build_meta_filter(req.params, default_filter=None)
        metadata = True if results_filter else to_bool(req.params.get("metadata", False))

        resp.media = self._controller.list_projects(store_id=store_id, metadata=metadata, result_filter=results_filter,
                                                    access=getattr(req, "user_access", UserAccessMeta()))
        resp.status = falcon.HTTP_200


def _has_create_access(is_admin: bool, access_groups: List[str], project_groups: List[str]) -> bool:
    if is_admin:
        return True

    if access_groups is None or len(access_groups) == 0:
        return False

    return any(group in access_groups for group in project_groups)


class ProjectCreate:
    internal_group_validation = True

    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str):
        validate_not_null(req.media, 'id')
        validate_not_null(req.media, 'name')
        validate_not_null(req.media, 'groups')

        project_id = req.media.get('id')
        project_name = req.media.get('name')
        project_groups = req.media.get('groups')

        access = getattr(req, "user_access", UserAccessMeta())
        _has_create_access(is_admin=access.admin_access, access_groups=access.write_groups, project_groups=project_groups)

        self._controller.create_project(store_id=store_id, project_id=project_id)
        self._controller.edit_project_access_meta(store_id=store_id, project_id=project_id, meta=OveProjectAccessMeta(groups=project_groups))

        meta = self._controller.get_project_meta(store_id=store_id, project_id=project_id)
        meta.name = project_name
        self._controller.edit_project_meta(store_id=store_id, project_id=project_id, meta=meta)

        resp.media = {'Project': project_id}
        resp.status = falcon.HTTP_200


class ProjectMetaEdit:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        access = getattr(req, "user_access", None)

        meta = self._controller.get_project_meta(store_id=store_id, project_id=project_id)
        item = meta.to_public_json()
        item["hasProject"] = self._controller.has_object(store_id=store_id, project_id=project_id, object_id="project")
        item["projectType"] = self._controller.project_type(store_id=store_id, project_id=project_id)
        item["access"] = self._controller.get_project_access_meta(store_id=store_id, project_id=project_id).groups
        item["read_access"] = True
        item["write_access"] = self._controller.has_access(store_id=store_id, project_id=project_id, groups=access.write_groups, is_admin=access.admin_access)

        resp.media = item
        resp.status = falcon.HTTP_200

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        validate_not_null(req.media, 'name')

        meta = self._controller.get_project_meta(store_id=store_id, project_id=project_id)

        for field in OveProjectMeta.EDITABLE_FIELDS:
            if field in req.media:
                setattr(meta, field, req.media.get(field))

        self._controller.edit_project_meta(store_id=store_id, project_id=project_id, meta=meta)

        resp.media = meta.to_public_json()
        resp.status = falcon.HTTP_200


class ProjectAccessMetaEdit:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        resp.media = self._controller.get_project_access_meta(store_id=store_id, project_id=project_id).to_public_json()
        resp.status = falcon.HTTP_200

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        _validate_is_admin(req)

        validate_not_null(req.media, 'groups')

        meta = OveProjectAccessMeta(groups=req.media.get("groups", []))
        self._controller.edit_project_access_meta(store_id=store_id, project_id=project_id, meta=meta)

        resp.media = meta.to_public_json()
        resp.status = falcon.HTTP_200


class ProjectVersion:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        meta = self._controller.get_project_meta(store_id=store_id, project_id=project_id)

        new_version = {
            'name': req.media['version_name'],
            'description': req.media['version_description'],
            'date_added': str(datetime.datetime.now()),
            'versions': {}
        }

        for asset in self._controller.list_assets(project_id=project_id, store_id=store_id):
            new_version['versions'][asset['id']] = asset['version']

        versions = getattr(meta, 'versions', {})
        if not versions:
            versions = []
        versions.insert(0, new_version)
        setattr(meta, 'versions', versions)

        self._controller.edit_project_meta(store_id=store_id, project_id=project_id, meta=meta)

        resp.media = meta.to_public_json()
        resp.status = falcon.HTTP_200


class AssetList:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        results_filter = build_meta_filter(req.params, default_filter=DEFAULT_FILTER)
        resp.media = self._controller.list_assets(project_id=project_id, store_id=store_id, result_filter=results_filter)
        resp.status = falcon.HTTP_200


class FileList:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        resp.media = self._controller.list_files(project_id=project_id, store_id=store_id, asset_id=asset_id)
        resp.status = falcon.HTTP_200


class AssetCreate:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        validate_not_null(req.media, 'id')
        validate_not_null(req.media, 'name')
        validate_no_slashes(req.media, 'id')

        asset_id = req.media.get('id')
        asset_name = req.media.get('name')

        meta = OveAssetMeta(id=asset_id, name=asset_name, project=project_id)
        self._controller.create_asset(store_id=store_id, project_id=project_id, meta=meta)

        resp.media = {'Asset': asset_id}
        resp.status = falcon.HTTP_200


class AssetUpload:
    # this will be validated by the RequireJSON middleware as a custom content-type, otherwise is json
    content_type = 'application/octet-stream'

    def __init__(self, controller: FileController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        filename = unquote_filename(req.params.get("filename", None))
        create_asset = to_bool(req.params.get("create", "False"))
        update_asset = to_bool(req.params.get("update", "False"))

        try:
            meta = self._controller.get_asset_meta(store_id=store_id, project_id=project_id, asset_id=asset_id)
            if meta.uploaded and not update_asset:
                raise falcon.HTTPBadRequest(title="Asset exists",
                                            description="This asset already has a file. If you wish to change this file, please update the asset.")
        except InvalidAssetError:
            if create_asset:
                meta = self._controller.create_asset(store_id=store_id, project_id=project_id, meta=OveAssetMeta(id=asset_id, name=asset_id, project=project_id))
            else:
                raise falcon.HTTPBadRequest(title="Asset not found", description="You have not created this asset yet.")

        up_fn = partial(self._controller.upload_asset, store_id=store_id, project_id=project_id, asset_id=asset_id, filename=filename, meta=meta,
                        update=update_asset)
        save_filename(up_fn, req)

        resp.media = {'Asset': asset_id, 'Filename': filename}
        resp.status = falcon.HTTP_200


class AssetMetaEdit:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        meta = self._controller.get_asset_meta(store_id=store_id, project_id=project_id, asset_id=asset_id)
        resp.media = meta.to_public_json()
        resp.status = falcon.HTTP_200

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        validate_not_null(req.media, 'name')

        meta = self._controller.get_asset_meta(store_id=store_id, project_id=project_id, asset_id=asset_id)

        for field in OveAssetMeta.EDITABLE_FIELDS:
            if field in req.media:
                setattr(meta, field, req.media.get(field))

        self._controller.edit_asset_meta(store_id=store_id, project_id=project_id, asset_id=asset_id, meta=meta)

        resp.media = meta.to_public_json()
        resp.status = falcon.HTTP_200


class TagEdit:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        meta = self._controller.get_asset_meta(store_id=store_id, project_id=project_id, asset_id=asset_id)
        resp.media = meta.tags
        resp.status = falcon.HTTP_200

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        validate_list(req.media)

        meta = self._controller.get_asset_meta(store_id=store_id, project_id=project_id, asset_id=asset_id)
        meta.tags = req.media
        self._controller.edit_asset_meta(store_id=store_id, project_id=project_id, asset_id=asset_id, meta=meta)

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

        meta = self._controller.get_asset_meta(store_id=store_id, project_id=project_id, asset_id=asset_id)

        new_tags = set(meta.tags)
        if action == 'add':
            new_tags.update(data)
        elif action == 'remove':
            new_tags.difference_update(data)
        meta.tags = list(new_tags)

        self._controller.edit_asset_meta(store_id=store_id, project_id=project_id, asset_id=asset_id, meta=meta)

        resp.media = meta.tags
        resp.status = falcon.HTTP_200

    def on_delete(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        meta = self._controller.get_asset_meta(store_id=store_id, project_id=project_id, asset_id=asset_id)
        meta.tags = []
        self._controller.edit_asset_meta(store_id=store_id, project_id=project_id, asset_id=asset_id, meta=meta)

        resp.media = meta.tags
        resp.status = falcon.HTTP_200


class ObjectEdit:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_head(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, object_id: str):
        has_object = self._controller.has_object(store_id=store_id, project_id=project_id, object_id=object_id)
        resp.status = falcon.HTTP_200 if has_object else falcon.HTTP_NOT_FOUND

    def on_get(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, object_id: str):
        resp.media = self._controller.get_object(store_id=store_id, project_id=project_id, object_id=object_id)
        resp.status = falcon.HTTP_200

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, object_id: str):
        self._controller.set_object(store_id=store_id, project_id=project_id, object_id=object_id, object_data=req.media, update=False)
        resp.media = {'Status': 'OK'}
        resp.status = falcon.HTTP_200

    def on_put(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, object_id: str):
        self._controller.set_object(store_id=store_id, project_id=project_id, object_id=object_id, object_data=req.media, update=True)
        resp.media = {'Status': 'OK'}
        resp.status = falcon.HTTP_200


class ObjectInfo:
    def __init__(self, controller: FileController):
        self._controller = controller

    def on_get(self, _: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, object_id: str):
        resp.media = self._controller.get_object_info(store_id=store_id, project_id=project_id, object_id=object_id) or {}
        resp.status = falcon.HTTP_200
