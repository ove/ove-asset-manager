import logging
import signal

import falcon

from common.errors import handle_exceptions
from common.middleware import RequireJSON, CORSComponent
from common.util import parse_logging_lvl
from workers.fileStoreInterpret import FileController
from workers.register import register_callback
from workers.routes import WorkerRoute


def setup_worker(logging_level: str = "debug", hostname: str = "localhost", port: int = 9080,
                 service_url: str = "http://localhost:8080/api/workers") -> falcon.API:
    logging.basicConfig(level=parse_logging_lvl(logging_level), format='[%(asctime)s] [%(levelname)s] %(message)s')
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    controller = FileController()
    app = falcon.API(middleware=[RequireJSON(), CORSComponent()])
    app.add_route('/api/worker', WorkerRoute(controller=controller))
    app.add_error_handler(Exception, handle_exceptions)

    register_callback(service_url=service_url, callback="http://{}:{}/api/worker".format(hostname, port))

    return app
