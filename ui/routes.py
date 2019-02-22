import logging
import sys

import falcon

from common.errors import ValidationError
from common.validation import validate_not_null
from ui.alert_utils import report_error, report_success
from ui.controller import BackendController
from ui.jinja2_utils import FalconTemplate


def _handle_exceptions(ex: Exception, resp: falcon.Response):
    logging.debug("Handling exception: %s", repr(ex))

    if not hasattr(resp, "alerts"):
        resp.alerts = []

    if isinstance(ex, (falcon.HTTPError, ValidationError)):
        report_error(resp=resp, title=ex.title, description=ex.description)
    else:
        report_error(resp=resp, description=sys.exc_info()[1])


falcon_template = FalconTemplate(path="ui/templates/", error_handler=_handle_exceptions)


class IndexView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('index.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response):
        resp.context = {"stores": self._controller.list_stores()}


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
            report_success(resp=resp, description="Project list loaded")
        except:
            raise

    @falcon_template.render('project-list.html')
    def on_post(self, req: falcon.Request, resp: falcon.Response, store_name: str):
        resp.context = {"store_name": store_name, "projects": []}

        validate_not_null(req.params, "project")
        try:
            self._controller.create_project(store_name=store_name, project_name=req.params.get("project", None))
            report_success(resp=resp, description="Project created")
        except:
            raise
        finally:
            resp.context["projects"] = self._controller.list_projects(store_name)


class AssetView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('asset-list.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response, store_name: str, project_name: str):
        resp.context = {"store_name": store_name, "project_name": project_name, "assets": []}
        try:
            resp.context["assets"] = self._controller.list_assets(store_name=store_name, project_name=project_name)
            report_success(resp=resp, description="Asset list loaded")
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
            resp.context["asset"] = self._controller.create_asset(store_name=store_name, project_name=project_name, asset=asset)
            raise falcon.HTTPPermanentRedirect(location="/view/store/{}/project/{}/asset/{}".format(store_name, project_name, asset.get("name")))
        else:
            resp.context["asset"] = self._controller.edit_asset(store_name=store_name, project_name=project_name, asset=asset)
