import logging
import os

import falcon

from common.middleware import CORSComponent
from common.util import parse_logging_lvl
from ui.controller import BackendController
from ui.routes import ProjectView, IndexView


def setup_ui(logging_level: str = "debug", backend_url: str = "http://localhost:8080") -> falcon.API:
    logging.basicConfig(level=parse_logging_lvl(logging_level), format='[%(asctime)s] [%(levelname)s] %(message)s')

    _controller = BackendController(backend_url=backend_url)
    app = falcon.API(middleware=[CORSComponent()])
    app.req_options.auto_parse_form_urlencoded = True

    app.add_static_route("/favicon.ico", os.getcwd() + "/ui/static/favicon.ico", downloadable=True)
    app.add_static_route("/css", os.getcwd() + "/ui/static/css/", downloadable=True)
    app.add_static_route("/js", os.getcwd() + "/ui/static/js/", downloadable=True)
    app.add_static_route("/images", os.getcwd() + "/ui/static/images/", downloadable=True)

    app.add_route('/', IndexView())
    app.add_route('/{store_name}/', ProjectView(controller=_controller))

    return app
