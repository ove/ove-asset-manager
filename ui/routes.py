import logging

import falcon

from ui.controller import BackendController
from ui.jinja2_utils import FalconTemplate


def _handle_exceptions(ex: Exception, resp: falcon.Response):
    logging.debug("Handling exception: %s", repr(ex))

    # resp.alerts.append({
    #     "title": "Uh-ho",
    #     "type": "error",
    #     "description": "Something went wrong"
    # })

    # if isinstance(ex, falcon.HTTPError):
    #     raise ex
    #
    # if isinstance(ex, (AssetExistsError, ObjectExistsError)):
    #     raise falcon.HTTPConflict(title=ex.title, description=ex.description)
    #
    # if isinstance(ex, ValidationError):
    #     raise falcon.HTTPBadRequest(title=ex.title, description=ex.description)
    #
    # raise falcon.HTTPBadRequest(title="Internal Server error", description=str(ex))


falcon_template = FalconTemplate(path="ui/templates/", error_handler=_handle_exceptions)


class ProjectView:
    def __init__(self, controller: BackendController):
        self._controller = controller

    @falcon_template.render('project-list.html')
    def on_get(self, _: falcon.Request, resp: falcon.Response):
        resp.alerts.append({
            "title": "Uh-ho",
            "type": "error",
            "description": "Something went wrong"
        })

        resp.alerts.append({
            "title": "Uh-ho",
            "type": "info",
            "description": "Something went wrong"
        })

        resp.context = self._controller.list_projects()
