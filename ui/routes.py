import json
import logging
import re
import sys
from typing import List, Tuple

import falcon
import markdown2
import urllib3

from common.consts import OBJECT_TEMPLATE, FIELD_AUTH_TOKEN
from common.entities import OveProjectMeta, OveAssetMeta
from common.errors import ValidationError
from common.falcon_utils import unquote_filename, auth_token
from common.util import to_bool, append_slash
from common.validation import validate_not_null
from ui.alert_utils import report_error, report_success
from ui.controller import BackendController
from ui.jinja2_utils import FalconTemplate


def handle_api_exceptions(ex: Exception, req: falcon.Request, _resp: falcon.Response, _params):
    logging.debug("Handling api exception: %s", repr(ex))

    if isinstance(ex, falcon.HTTPNotFound):
        logging.debug("%s. %s", ex.title, req.url)
        raise ex

    if isinstance(ex, (falcon.HTTPNotFound, falcon.HTTPNotImplemented)):
        raise falcon.HTTPPermanentRedirect(location="/404")

    if isinstance(ex, (falcon.HTTPPermanentRedirect, falcon.HTTPTemporaryRedirect, falcon.HTTPSeeOther)):
        raise ex

    if isinstance(ex, falcon.HTTPError):
        raise ex

    if isinstance(ex, ValidationError):
        raise falcon.HTTPBadRequest(title=ex.title, description=ex.description)

    raise falcon.HTTPBadRequest(title="Internal Server error", description=str(ex))


def _handle_exceptions(ex: Exception, resp: falcon.Response):
    logging.debug("Handling exception: %s", repr(ex))

    if not hasattr(resp, "alerts"):
        resp.alerts = []

    if isinstance(ex, (falcon.HTTPPermanentRedirect, falcon.HTTPSeeOther)):
        raise ex

    if isinstance(ex, (falcon.HTTPError, ValidationError)):
        report_error(resp=resp, title=ex.title, description=ex.description)
    elif isinstance(ex, urllib3.exceptions.RequestError):
        report_error(resp=resp, title="Server unavailable", description="The data server seems to be unavailable at the moment")
    else:
        report_error(resp=resp, description=sys.exc_info()[1])


falcon_template = FalconTemplate(path="ui/templates/", error_handler=_handle_exceptions)


class LoginView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('login.html')
    def on_get(self, _req: falcon.Request, _resp: falcon.Response):
        pass

    @falcon_template.render('login.html')
    def on_post(self, req: falcon.Request, resp: falcon.Response):
        validate_not_null(req.params, 'user')
        validate_not_null(req.params, 'password')

        token = self._controller.login(user=req.params.get("user", None), password=req.params.get("password", None))
        if token:
            resp.set_cookie(FIELD_AUTH_TOKEN, token)
            raise falcon.HTTPSeeOther("/")
        else:
            raise ValidationError(title="Invalid login", description="Invalid username or password")


class LogoutView:
    @falcon_template.render('login.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response):
        resp.unset_cookie(FIELD_AUTH_TOKEN)
        raise falcon.HTTPSeeOther("/")

    @falcon_template.render('login.html')
    def on_post(self, _: falcon.Request, resp: falcon.Response):
        resp.unset_cookie(FIELD_AUTH_TOKEN)
        raise falcon.HTTPSeeOther("/")


class IndexView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('index.html')
    def on_get(self, req: falcon.Request, resp: falcon.Response):
        if req.params.get("store-name", None):
            raise falcon.HTTPPermanentRedirect("/view/store/" + req.params.get("store-name", None))
        else:
            resp.context = {"stores": self._controller.list_stores(auth_token=auth_token(req))}


class NotFoundView:
    @falcon_template.render('404.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response):
        pass


class WorkerView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('worker-list.html')
    def on_get(self, req: falcon.Request, resp: falcon.Response):
        resp.context = {"workers": []}
        try:
            resp.context["workers"] = self._controller.list_workers(auth_token=auth_token(req))
        except:
            raise

    @falcon_template.render('worker-list.html')
    def on_post(self, req: falcon.Request, resp: falcon.Response):
        resp.context = {"workers": []}

        validate_not_null(req.params, "name")
        validate_not_null(req.params, "action")
        action = req.params.get("action")
        name = req.params.get("name")
        try:
            resp.context["workers"] = self._controller.list_workers(auth_token=auth_token(req))
            self._controller.edit_worker(action=action, name=name, auth_token=auth_token(req))

            if action == "reset":
                report_success(resp=resp, description="Worker status refreshed")
            elif action == "delete":
                report_success(resp=resp, description="Worker deleted")
            else:
                report_error(resp=resp, description="Invalid worker action")

            resp.context["workers"] = self._controller.list_workers(auth_token=auth_token(req))
        except:
            raise


class WorkerQueueView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('worker-queue.html')
    def on_get(self, req: falcon.Request, resp: falcon.Response):
        resp.context = {"tasks": []}
        try:
            resp.context["tasks"] = self._controller.list_tasks(auth_token=auth_token(req))
        except:
            raise

    @falcon_template.render('worker-queue.html')
    def on_post(self, req: falcon.Request, resp: falcon.Response):
        resp.context = {"tasks": []}

        validate_not_null(req.params, "task_id")
        validate_not_null(req.params, "action")
        action = req.params.get("action")
        task_id = req.params.get("task_id")
        try:
            resp.context["tasks"] = self._controller.list_tasks(auth_token=auth_token(req))
            self._controller.edit_task(action=action, task_id=task_id, auth_token=auth_token(req))

            if action == "reset":
                report_success(resp=resp, description="Task status reset")
            elif action == "cancel":
                report_success(resp=resp, description="Task cancelled")
            else:
                report_error(resp=resp, description="Invalid task action")

            resp.context["tasks"] = self._controller.list_tasks(auth_token=auth_token(req))
        except:
            raise


class ProjectView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('project-list.html')
    def on_get(self, req: falcon.Request, resp: falcon.Response, store_id: str):
        resp.context = {"store_id": store_id, "projects": []}
        try:
            resp.context["projects"] = self._controller.list_projects(store_id, auth_token=auth_token(req))
        except:
            raise

    @falcon_template.render('project-list.html')
    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str):
        validate_not_null(req.params, "project_id")
        validate_not_null(req.params, "project_name")

        project_id = req.params.get("project_id", None)
        project_name = req.params.get("project_name", None)

        resp.context = {"store_id": store_id, "project_id": project_id, "project_name": project_name, "assets": [], "workers": {}}

        try:
            access = getattr(resp, "auth_user", {})
            self._controller.create_project(store_id=store_id, project_id=project_id, project_name=project_name,
                                            groups=access.get("write_groups", []), auth_token=auth_token(req))
            report_success(resp=resp, description="Project created")
        except:
            raise
        finally:
            resp.context["projects"] = self._controller.list_projects(store_id, auth_token=auth_token(req))

        raise falcon.HTTPSeeOther('./%s/project/%s' % (store_id, project_id))


class ProjectIndexView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('project-index.html')
    def on_get(self, req: falcon.Request, resp: falcon.Response, store_id: str):
        resp.context = {"store_id": store_id, "projects": []}
        try:
            resp.context["projects"] = self._controller.list_projects(store_id, auth_token=auth_token(req))
        except:
            raise


class AssetView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('asset-list.html')
    def on_get(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        resp.context = {"store_id": store_id, "project_id": project_id, "assets": [], "workers": [], "project": {}}
        try:
            resp.context["project"] = self._controller.get_project(store_id=store_id, project_id=project_id, auth_token=auth_token(req))
            resp.context["assets"] = self._controller.list_assets(store_id=store_id, project_id=project_id, auth_token=auth_token(req))
            resp.context["workers"] = self._controller.get_worker_types(auth_token=auth_token(req))
            resp.context["objects"] = self._controller.check_objects(store_id=store_id, project_id=project_id, object_ids=["project"], auth_token=auth_token(req))
            resp.context["launcher_url"] = self._controller.launcher_url
        except:
            raise


class ProjectEdit:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('project-edit.html')
    def on_get(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        resp.context = {"store_id": store_id, "project_id": project_id, "project": {"name": project_id}}
        try:
            resp.context["project"] = self._controller.get_project(store_id=store_id, project_id=project_id, auth_token=auth_token(req))
        except:
            raise

    @falcon_template.render('project-edit.html')
    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        def _get_tags():
            result = req.params.get("tags[]", None)
            if isinstance(result, str):
                result = [result]
            return result

        project = {}
        for field in OveProjectMeta.EDITABLE_FIELDS:
            project[field] = req.params.get(field, "")
        project["tags"] = _get_tags()
        project["video_controller"] = to_bool(req.params.get("video_controller", False))
        project["html_controller"] = to_bool(req.params.get("html_controller", False))

        resp.context = {"store_id": store_id, "project_id": project_id, "project": project}
        try:
            resp.context["project"] = self._controller.edit_project(store_id=store_id, project_id=project_id, project_data=project, auth_token=auth_token(req))
        except:
            raise


def _groups(auth_groups: List[str], project_groups: List[str]) -> List[Tuple[str, bool]]:
    return list({group: group in project_groups for group in auth_groups}.items())


class ProjectAccessEdit:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('project-access-edit.html')
    def on_get(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        resp.context = {"store_id": store_id, "project_id": project_id, "groups": []}
        try:
            meta = self._controller.get_access_meta(store_id=store_id, project_id=project_id, auth_token=auth_token(req)) or {}
            resp.context["groups"] = _groups(auth_groups=self._controller.get_auth_groups(auth_token=auth_token(req)), project_groups=meta.get("groups", []))
        except:
            raise

    @falcon_template.render('project-access-edit.html')
    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        def _get_groups():
            result = req.params.get("groups[]", None)
            if isinstance(result, str):
                result = [result]
            return result

        resp.context = {"store_id": store_id, "project_id": project_id, "groups": []}
        try:
            meta = {"groups": _get_groups()}
            meta = self._controller.edit_access_meta(store_id=store_id, project_id=project_id, meta=meta, auth_token=auth_token(req))
            resp.context["groups"] = _groups(auth_groups=self._controller.get_auth_groups(auth_token=auth_token(req)), project_groups=meta.get("groups", []))
        except:
            raise


class AssetEdit:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('asset-edit.html')
    def on_get(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        resp.context = {"store_id": store_id, "project_id": project_id, "asset_id": asset_id, "create": asset_id == "new",
                        "asset": {"id": asset_id, "name": asset_id, "project": project_id}}
        if asset_id != "new":
            try:
                resp.context["asset"] = self._controller.get_asset(store_id=store_id, project_id=project_id, asset_id=asset_id, auth_token=auth_token(req))
            except:
                resp.context["create"] = True
                raise

    @falcon_template.render('asset-edit.html')
    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        def _get_tags():
            result = req.params.get("tags[]", None)
            if isinstance(result, str):
                result = [result]
            return result

        asset = {"id": req.params.get("id", ""), "name": req.params.get("name", ""), "project": req.params.get("project", "")}
        for field in OveAssetMeta.EDITABLE_FIELDS:
            asset[field] = req.params.get(field, "")
        asset["tags"] = _get_tags()

        resp.context = {"store_id": store_id, "project_id": project_id, "asset_id": asset_id, "create": False, "asset": asset}

        if asset_id == "new":
            resp.context["create"] = True
            resp.context["asset"] = self._controller.create_asset(store_id=store_id, project_id=project_id, asset=asset, auth_token=auth_token(req))
            raise falcon.HTTPPermanentRedirect(location="/view/store/{}/project/{}/asset/{}".format(store_id, project_id, asset.get("id")))
        else:
            resp.context["asset"] = self._controller.edit_asset(store_id=store_id, project_id=project_id, asset=asset, auth_token=auth_token(req))


class ObjectEdit:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('object-edit.html')
    def on_get(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, object_id: str):
        default_object = OBJECT_TEMPLATE.get(object_id, {})

        resp.context = {"store_id": store_id, "project_id": project_id, "object_id": object_id, "object": default_object, "create": False}
        objects = self._controller.check_objects(store_id=store_id, project_id=project_id, object_ids=[object_id], auth_token=auth_token(req))
        if len(objects) > 0:
            resp.context['file_url'] = objects[0]['index_file']

        try:
            resp.context["object"] = self._controller.get_object(store_id=store_id, project_id=project_id, object_id=object_id, auth_token=auth_token(req))
            resp.context["create"] = False
        except:
            resp.context["create"] = True
            resp.context["object"] = default_object
            raise ValidationError(title="Not found", description="This project does not have a '{}.json' object".format(object_id))

    @falcon_template.render('object-edit.html')
    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, object_id: str):
        resp.context = {"store_id": store_id, "project_id": project_id, "object_id": object_id, "create": False,
                        "object": json.loads(req.params.get("object", ""))}

        self._controller.set_object(store_id=store_id, project_id=project_id, object_id=object_id,
                                    object_data=json.loads(req.params.get("object", "")), auth_token=auth_token(req))

        objects = self._controller.check_objects(store_id=store_id, project_id=project_id, object_ids=[object_id], auth_token=auth_token(req))
        if len(objects) > 0:
            resp.context['file_url'] = objects[0]['index_file']


class WorkerDocsView:
    def __init__(self, docs_folder: str):
        self.docs_folder = append_slash(docs_folder)

    @falcon_template.render('worker-docs.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response, worker_doc: str):
        resp.context = {"worker_doc": worker_doc, "content": ""}
        try:
            with open(self.docs_folder + worker_doc) as fin:
                resp.context["content"] = markdown2.markdown(fin.read())
        except:
            raise falcon.HTTPNotFound(title="Docs not found", description="'{}' is not available".format(worker_doc))


class BackendDetailsView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('backend-details.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response):
        resp.context = {"backend_url": self._controller.backend_url}


class UploadApi:
    content_type = 'application/octet-stream'

    def __init__(self, controller: BackendController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str = None):
        filename = unquote_filename(req.params.get("filename", None))
        create = False
        if asset_id is None:
            asset_id = re.sub("\\W+", '_', filename)
            create = True

        self._controller.upload_asset(store_id=store_id, project_id=project_id, asset_id=asset_id, filename=filename, stream=req.bounded_stream,
                                      update=to_bool(req.params.get("update", "True")), create=create, auth_token=auth_token(req))
        resp.media = {'Status': 'OK'}
        resp.status = falcon.HTTP_200


class VersionApi:
    content_type = 'application/x-www-form-urlencoded'

    def __init__(self, controller: BackendController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str):
        self._controller.create_project_version(store_id=store_id, project_id=project_id,
                                                version_name=req.params.get("version_name", ""),
                                                version_description=req.params.get("version_description", ""))

        resp.media = {'Status': 'OK'}
        resp.status = falcon.HTTP_200

        raise falcon.HTTPSeeOther(location="/view/store/{}/project/{}".format(store_id, project_id))


class ObjectEditApi:
    content_type = 'application/json'

    def __init__(self, controller: BackendController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, object_id: str):
        self._controller.set_object(store_id=store_id, project_id=project_id, object_id=object_id, object_data=req.media, auth_token=auth_token(req))
        resp.media = {'Status': 'OK'}
        resp.status = falcon.HTTP_200


class WorkerApi:
    content_type = 'application/json'

    def __init__(self, controller: BackendController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str, worker_type: str):
        self._controller.schedule_worker(store_id=store_id, project_id=project_id, asset_id=asset_id, worker_type=worker_type, parameters=req.media, auth_token=auth_token(req))
        resp.media = {'Status': 'OK'}
        resp.status = falcon.HTTP_200


class FilesApi:
    content_type = 'application/json'

    def __init__(self, controller: BackendController):
        self._controller = controller

    def on_get(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        resp.media = self._controller.list_files(store_id=store_id, project_id=project_id, asset_id=asset_id, version=req.params.get("version", None),
                                                 hierarchical=to_bool(req.params.get("hierarchical", False)), auth_token=auth_token(req))
        resp.status = falcon.HTTP_200


class MetaApi:
    content_type = 'application/json'

    def __init__(self, controller: BackendController):
        self._controller = controller

    def on_get(self, req: falcon.Request, resp: falcon.Response, store_id: str, project_id: str, asset_id: str):
        resp.media = self._controller.get_asset(store_id=store_id, project_id=project_id, asset_id=asset_id, auth_token=auth_token(req))
        resp.status = falcon.HTTP_200
