import logging
import sys

import falcon

from common.errors import ValidationError
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
    def on_get(self, _req: falcon.Request, _resp: falcon.Response):
        raise falcon.HTTPPermanentRedirect("/*/")


class ProjectView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('project-list.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response, store_name: str = "*"):
        resp.context = {"projects": self._controller.list_projects(store_name), "store_name": store_name}
        report_success(resp=resp, description="Project list loaded")

    @falcon_template.render('project-list.html')
    def on_post(self, req: falcon.Request, resp: falcon.Response, store_name: str = "*"):
        try:
            self._controller.create_project(store_name=store_name, project_name=req.params.get("project", None))
            resp.context = {"projects": self._controller.list_projects(store_name), "store_name": store_name}
            report_success(resp=resp, description="Project created")
        except:
            resp.context = {"projects": self._controller.list_projects(store_name), "store_name": store_name}
            raise
