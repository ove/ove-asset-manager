import logging
import os

import falcon

from common.middleware import CORSComponent
from common.util import parse_logging_lvl
from ui.controller import BackendController
from ui.routes import ProjectView


def setup_ui(logging_level: str = "debug", backend_url: str = "http://localhost:8080") -> falcon.API:
    logging.basicConfig(level=parse_logging_lvl(logging_level), format='[%(asctime)s] [%(levelname)s] %(message)s')

    _controller = BackendController(backend_url=backend_url)
    app = falcon.API(middleware=[CORSComponent()])

    app.add_route('/', ProjectView(controller=_controller))

    app.add_static_route("/", os.getcwd() + "/ui/static/", downloadable=True)
    app.add_static_route("/css", os.getcwd() + "/ui/static/css/", downloadable=True)
    app.add_static_route("/js", os.getcwd() + "/ui/static/js/", downloadable=True)

    return app
