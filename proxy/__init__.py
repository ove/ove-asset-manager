import logging

import falcon

from common.consts import DEFAULT_CONFIG
from common.errors import handle_exceptions
from common.middleware import CORSComponent
from common.util import parse_logging_lvl
from proxy.controller import FileController
from proxy.routes import ResourceStream


def setup_app(logging_level: str = "debug", config_file: str = DEFAULT_CONFIG) -> falcon.API:
    logging.basicConfig(level=parse_logging_lvl(logging_level), format='[%(asctime)s] [%(levelname)s] %(message)s')

    app = falcon.API(middleware=[CORSComponent()])
    app.add_sink(prefix='/', sink=ResourceStream(controller=FileController(config_file=config_file)))
    app.add_error_handler(Exception, handle_exceptions)

    return app
