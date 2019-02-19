import logging
import signal

import falcon

from common.entities import WorkerType
from common.errors import handle_exceptions
from common.middleware import RequireJSON, CORSComponent
from common.util import parse_logging_lvl
from workers import factory_worker
from workers.base.controller import FileController
from workers.base.routes import WorkerRoute
from workers.base.worker import BaseWorker, register_callback


def setup_worker(**kwargs) -> falcon.API:
    logging_level = parse_logging_lvl(kwargs.get("logging_level", "debug"))
    hostname = kwargs.get("hostname", "localhost")
    port = kwargs.get("port", 9080)
    worker_name = kwargs.get("worker_name", "test")
    worker_type = WorkerType(kwargs.get("worker_type", "extract"))
    service_url = kwargs.get("service_url", "http://localhost:8080/api/workers")
    registration_attempts = kwargs.get("registration_attempts", 5)
    registration_timeout = kwargs.get("registration_timeout", 5000)

    logging.basicConfig(level=logging_level, format='[%(asctime)s] [%(levelname)s] %(message)s')
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)

    _worker = factory_worker(worker_type)(name=worker_name, callback="http://{}:{}/api/worker".format(hostname, port),
                                          service_url=service_url, file_controller=FileController())

    app = falcon.API(middleware=[RequireJSON(), CORSComponent()])
    app.add_route('/api/worker', WorkerRoute(worker=_worker))
    app.add_error_handler(Exception, handle_exceptions)

    register_callback(worker=_worker, attempts=registration_attempts, timeout=registration_timeout)

    return app
