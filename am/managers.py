import logging
import random
import sys
from typing import List, Dict

import requests

from common.entities import WorkerData, OveMeta, WorkerStatus
from common.errors import MissingParameterError, WorkerCallbackError, WorkerUnavailableError, WorkerExistsError, WorkerNotFoundError
from common.util import is_empty_str


class WorkerManager:
    def __init__(self):
        self._workers = []

    def add_worker(self, worker: WorkerData):
        _validate_field(worker, "name")
        _validate_field(worker, "callback")

        if worker.name in self._workers:
            raise WorkerExistsError()

        if not _validate_callback(worker.callback):
            raise WorkerCallbackError(url=worker.callback)

        self._workers.append(worker)

    def remove_worker(self, name: str):
        if name in self._workers:
            self._workers = [w for w in self._workers if w.name != name]
        else:
            raise WorkerNotFoundError()

    def worker_info(self, name: str = None):
        return [w.to_public_json() for w in self._workers if name is None or name == w.name]

    def update(self, name: str, status: WorkerStatus):
        for w in self._workers:
            if w.name == name:
                w.status = status

    def schedule_process(self, meta: OveMeta, store_config: Dict):
        available = _find_workers(meta.filename, self._workers)
        if len(available) > 0:
            # load balancing ^_^
            random.shuffle(available)
            data = {"store": store_config, "meta": meta.name}

            success = False
            for w in available:
                if _schedule_callback(w.callback, data=data):
                    w.status = WorkerStatus.PROCESSING
                    success = True
                    break

            if not success:
                raise WorkerUnavailableError(filename=meta.filename)
        else:
            raise WorkerUnavailableError(filename=meta.filename)


def _find_workers(filename: str, workers: List[WorkerData]) -> List[WorkerData]:
    def is_valid(w: WorkerData) -> bool:
        if any([filename.endswith(ext) for ext in w.extensions]):
            return _validate_callback(w.callback)
        return False

    return [w for w in workers if is_valid(w)]


def _validate_field(data, field: str):
    if is_empty_str(getattr(data, field, None)):
        raise MissingParameterError(field)


def _validate_callback(callback: str) -> bool:
    try:
        requests.head(callback)
        return True
    except:
        logging.error("Callback not reachable. Url = '%s'. Error: %s", callback, sys.exc_info()[1])
        return False


def _schedule_callback(callback: str, data: Dict) -> bool:
    try:
        r = requests.post(callback, json=data)
        if 200 <= r.status_code < 300:
            return True
        else:
            logging.error("Callback error. Url = '%s'. Status Code: %s. Error: %s", callback, r.status_code, r.text)
    except:
        logging.error("Callback not reachable. Url = '%s'. Error: %s", callback, sys.exc_info()[1])
        return False
