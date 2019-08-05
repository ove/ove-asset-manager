import json
import logging
import re
import sys

import falcon
import markdown2
import urllib3

from common.errors import ValidationError
from common.falcon_utils import unquote_filename
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


class IndexView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('index.html')
    def on_get(self, req: falcon.Request, resp: falcon.Response):
        if req.params.get("store-name", None):
            raise falcon.HTTPPermanentRedirect("/view/store/" + req.params.get("store-name", None))
        else:
            resp.context = {"stores": self._controller.list_stores()}


class NotFoundView:
    @falcon_template.render('404.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response):
        pass


class WorkerView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('worker-list.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response):
        resp.context = {"workers": []}
        try:
            resp.context["workers"] = self._controller.list_workers()
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
            resp.context["workers"] = self._controller.list_workers()
            self._controller.edit_worker(action=action, name=name)

            if action == "reset":
                report_success(resp=resp, description="Worker status refreshed")
            elif action == "delete":
                report_success(resp=resp, description="Worker deleted")
            else:
                report_error(resp=resp, description="Invalid worker action")

            resp.context["workers"] = self._controller.list_workers()
        except:
            raise


class ProjectView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('project-list.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response, store_name: str):
        resp.context = {"store_name": store_name, "projects": []}
        try:
            resp.context["projects"] = self._controller.list_projects(store_name)
        except:
            raise

    @falcon_template.render('project-list.html')
    def on_post(self, req: falcon.Request, resp: falcon.Response, store_name: str):
        validate_not_null(req.params, "project")
        project_name = req.params.get("project", None)
        resp.context = {"store_name": store_name, "project_name": project_name, "assets": [], "workers": {}}

        try:
            self._controller.create_project(store_name=store_name, project_name=project_name)
            report_success(resp=resp, description="Project created")
        except:
            raise
        finally:
            resp.context["projects"] = self._controller.list_projects(store_name)

        raise falcon.HTTPSeeOther('./%s/project/%s' % (store_name, project_name))


class ProjectIndexView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('project-index.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response, store_name: str):
        resp.context = {"store_name": store_name, "projects": []}
        try:
            resp.context["projects"] = self._controller.list_projects(store_name)
        except:
            raise


class AssetView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('asset-list.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response, store_name: str, project_name: str):
        resp.context = {"store_name": store_name, "project_name": project_name, "assets": [], "workers": {}}
        try:
            resp.context["assets"] = self._controller.list_assets(store_name=store_name, project_name=project_name)
            resp.context["workers"] = self._controller.get_worker_types()
            resp.context["objects"] = self._controller.check_objects(store_name=store_name, project_name=project_name, object_names=["project"])
        except:
            raise


class ProjectEdit:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('project-edit.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response, store_name: str, project_name: str):
        resp.context = {"store_name": store_name, "project_name": project_name, "project": {"name": project_name}}
        try:
            resp.context["project"] = self._controller.get_project(store_name=store_name, project_name=project_name)
        except:
            raise

    @falcon_template.render('project-edit.html')
    def on_post(self, req: falcon.Request, resp: falcon.Response, store_name: str, project_name: str):
        def _get_tags():
            result = req.params.get("tags[]", None)
            if isinstance(result, str):
                result = [result]
            return result

        project = {
            "name": req.params.get("name", ""),
            "description": req.params.get("description", ""),
            "authors": req.params.get("authors", ""),
            "publications": req.params.get("publications", ""),
            "tags": _get_tags()
        }
        resp.context = {"store_name": store_name, "project_name": project_name, "project": project}
        try:
            resp.context["project"] = self._controller.edit_project(store_name=store_name, project_name=project_name, project_data=project)
        except:
            raise


class AssetEdit:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('asset-edit.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response, store_name: str, project_name: str, asset_name: str):
        resp.context = {"store_name": store_name, "project_name": project_name, "asset_name": asset_name, "create": asset_name == "new",
                        "asset": {"name": asset_name, "project": project_name}}
        if asset_name != "new":
            try:
                resp.context["asset"] = self._controller.get_asset(store_name=store_name, project_name=project_name, asset_name=asset_name)
            except:
                resp.context["create"] = True
                raise

    @falcon_template.render('asset-edit.html')
    def on_post(self, req: falcon.Request, resp: falcon.Response, store_name: str, project_name: str, asset_name: str):
        def _get_tags():
            result = req.params.get("tags[]", None)
            if isinstance(result, str):
                result = [result]
            return result

        asset = {
            "name": req.params.get("name", ""),
            "project": req.params.get("project", ""),
            "description": req.params.get("description", ""),
            "tags": _get_tags()
        }
        resp.context = {"store_name": store_name, "project_name": project_name, "asset_name": asset_name, "create": False, "asset": asset}

        if asset_name == "new":
            resp.context["create"] = True
            resp.context["asset"] = self._controller.create_asset(store_name=store_name, project_name=project_name, asset=asset)
            raise falcon.HTTPPermanentRedirect(location="/view/store/{}/project/{}/asset/{}".format(store_name, project_name, asset.get("name")))
        else:
            resp.context["asset"] = self._controller.edit_asset(store_name=store_name, project_name=project_name, asset=asset)


class ObjectEdit:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('object-edit.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response, store_name: str, project_name: str, object_name: str):

        default_object = {
            "Attribution": {
                "Title": project_name
            },
            "HasVideos": False,
            "Sections": [
                {
                    "app": {
                        "states": {
                            "load": {
                                "url": "http://google.com"
                            }
                        },
                        "url": "OVE_APP_HTML"
                    },
                    "h": 1080,
                    "space": "SPACE_NAME",
                    "w": 1920,
                    "x": 0,
                    "y": 0
                }
            ]
        }

        resp.context = {"store_name": store_name, "project_name": project_name, "object_name": object_name, "object": {}, "create": False}
        try:
            resp.context["object"] = self._controller.get_object(store_name=store_name, project_name=project_name, object_name=object_name)
            resp.context["create"] = False
        except:
            resp.context["create"] = True
            resp.context["object"] = default_object
            raise ValidationError(title="Not found", description="This project does not have a '{}.json' object".format(object_name))

    @falcon_template.render('object-edit.html')
    def on_post(self, req: falcon.Request, resp: falcon.Response, store_name: str, project_name: str, object_name: str):
        resp.context = {"store_name": store_name, "project_name": project_name, "object_name": object_name, "create": False,
                        "object": json.loads(req.params.get("object", ""))}

        self._controller.set_object(store_name=store_name, project_name=project_name, object_name=object_name,
                                    object_data=json.loads(req.params.get("object", "")))


class WorkerDocs:
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
        resp.context = {"backend_url": self. _controller._backend.backend_url}


class UploadApi:
    content_type = 'application/octet-stream'

    def __init__(self, controller: BackendController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_name: str, project_name: str, asset_name: str = None):
        filename = unquote_filename(req.params.get("filename", None))
        create = False
        if asset_name is None:
            asset_name = re.sub("\\W+", '_', filename)
            create = True

        self._controller.upload_asset(store_name=store_name, project_name=project_name, asset_name=asset_name, filename=filename, stream=req.bounded_stream,
                                      update=to_bool(req.params.get("update", "True")), create=create)
        resp.media = {'Status': 'OK'}
        resp.status = falcon.HTTP_200


class WorkerApi:
    content_type = 'application/json'

    def __init__(self, controller: BackendController):
        self._controller = controller

    def on_post(self, req: falcon.Request, resp: falcon.Response, store_name: str, project_name: str, asset_name: str, worker_type: str):
        self._controller.schedule_worker(store_name=store_name, project_name=project_name, asset_name=asset_name, worker_type=worker_type, parameters=req.media)
        resp.media = {'Status': 'OK'}
        resp.status = falcon.HTTP_200


class FilesApi:
    content_type = 'application/json'

    def __init__(self, controller: BackendController):
        self._controller = controller

    def on_get(self, req: falcon.Request, resp: falcon.Response, store_name: str, project_name: str, asset_name: str):
        resp.media = self._controller.list_files(store_name=store_name, project_name=project_name, asset_name=asset_name,
                                                 hierarchical=to_bool(req.params.get("hierarchical", False)))
        resp.status = falcon.HTTP_200
