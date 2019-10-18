import atexit
import logging
import signal

import falcon

from common.consts import DEFAULT_WORKER_CONFIG
from common.errors import handle_exceptions
from common.middleware import RequireJSON, CORSComponent
from common.util import parse_logging_lvl, dynamic_import
from workers.base.controller import FileController
from workers.base.routes import WorkerStatusRoute
from workers.base.worker import BaseWorker, register_worker, unregister_worker


def setup_worker(**kwargs) -> falcon.API:
    logging_level = parse_logging_lvl(kwargs.get("logging_level", "debug"))
    worker_name = kwargs.get("worker_name", "test")
    worker_class = kwargs.get("worker_class", None)
    config_file = kwargs.get("config_file", DEFAULT_WORKER_CONFIG)

    logging.basicConfig(level=logging_level, format='[%(asctime)s] [%(levelname)s] %(message)s')
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    _worker = dynamic_import(worker_class)(name=worker_name, config_file=config_file, file_controller=FileController())

    app = falcon.API(middleware=[RequireJSON(), CORSComponent()])
    app.add_route('/api/worker/status', WorkerStatusRoute(worker=_worker))
    app.add_error_handler(Exception, handle_exceptions)

    atexit.register(unregister_worker, worker=_worker)
    register_worker(worker=_worker)

    return app
