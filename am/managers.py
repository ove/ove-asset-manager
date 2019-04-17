import logging
import random
import sys
from typing import List, Dict

import requests

from common.entities import WorkerData, OveAssetMeta, WorkerStatus
from common.errors import MissingParameterError, WorkerCallbackError, WorkerUnavailableError, WorkerExistsError, WorkerNotFoundError
from common.util import is_empty_str


class WorkerManager:
    def __init__(self):
        self._workers = []

    def add_worker(self, worker: WorkerData):
        _validate_field(worker, "name")
        _validate_field(worker, "callback")
        _validate_field(worker, "status_callback")

        if worker.name in self._workers:
            raise WorkerExistsError()

        if not _validate_callback(worker.callback):
            raise WorkerCallbackError(url=worker.callback)

        if not _validate_callback(worker.status_callback):
            raise WorkerCallbackError(url=worker.status_callback)

        self._workers.append(worker)

    def remove_worker(self, name: str):
        if name in self._workers:
            self._workers = [w for w in self._workers if w.name != name]
        else:
            raise WorkerNotFoundError()

    def worker_info(self, name: str = None):
        return [w.to_public_json() for w in self._workers if name is None or name == w.name]

    def worker_status(self, name: str = None):
        return {w.name: str(w.status) for w in self._workers if name is None or name == w.name}

    def update(self, name: str, status: WorkerStatus, error_msg: str = ""):
        for w in self._workers:
            if w.name == name:
                w.status = status
                w.error_msg = error_msg

    def schedule_process(self, project_name: str, meta: OveAssetMeta, worker_type: str, store_config: Dict, task_options: Dict):
        filename = task_options.get("filename", meta.filename)
        if filename is None or len(filename) == 0:
            filename = meta.filename

        available = _find_workers(filename=filename, worker_type=worker_type, workers=self._workers)
        if len(available) > 0:
            # load balancing ^_^
            random.shuffle(available)
            data = {"store_config": store_config, "project_name": project_name, "asset_name": meta.name, "task_options": task_options}

            success = False
            for w in available:
                if _schedule_callback(w.callback, data=data):
                    w.status = WorkerStatus.PROCESSING
                    success = True
                    break

            if not success:
                raise WorkerUnavailableError(filename=filename)
        else:
            raise WorkerUnavailableError(filename=filename)

    def reset_worker_status(self, name: str = None):
        for worker in self._workers:
            if name is None or worker.name == name:
                _schedule_callback(worker.status_callback, {})


def _find_workers(filename: str, worker_type: str, workers: List[WorkerData]) -> List[WorkerData]:
    def is_valid(w: WorkerData) -> bool:
        if w.type == worker_type and any([filename.lower().endswith(ext) for ext in w.extensions]):
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
