import logging
import sys
import time
from abc import ABC, abstractmethod
from multiprocessing import Process
from typing import Dict, List

import requests

from common.entities import OveMeta, WorkerStatus, WorkerData
from workers.base.controller import FileController


class BaseWorker(ABC):
    def __init__(self, name: str, callback: str, status_callback: str, service_url: str, file_controller: FileController):
        self._name = name
        self._callback = callback
        self._status_callback = status_callback
        self._service_url = service_url
        self._file_controller = file_controller
        self._status = WorkerStatus.READY

    @property
    def name(self) -> str:
        return self._name

    @property
    def status(self) -> WorkerStatus:
        return self._status

    def reset_status(self) -> WorkerStatus:
        if self.status is WorkerStatus.ERROR:
            self.update_status(WorkerStatus.READY)
        return self.status

    def update_status(self, status: WorkerStatus):
        r = requests.patch(self._service_url, json={"name": self.name, "status": str(status)})
        if 200 <= r.status_code < 300:
            logging.info("%s status updated on server '%s'", status, self._service_url)
            self._status = status
        else:
            logging.error("Failed to update status on server '%s'. Requested status: %s. Server error: %s", self._service_url, status, r.text)

    def report_error(self, error: str):
        r = requests.patch(self._service_url, json={"name": self.name, "status": str(WorkerStatus.ERROR), "error": error})
        if 200 <= r.status_code < 300:
            logging.error("Error status updated on server '%s'. Error: %s", self._service_url, error)
            self._status = WorkerStatus.ERROR
        else:
            logging.error("Failed to update status on server '%s'. Reported error: %s. Server error: %s", self._service_url, error, r.text)

    def register_callback(self, attempts: int, timeout: int):
        data = WorkerData(name=self.name, callback=self._callback, status_callback=self._status_callback,
                          type=self.worker_type(), description=self.description(), status=self.status, extensions=self.extensions())

        for i in range(attempts):
            logging.info("Register callback timeout %s ms", timeout)
            time.sleep(timeout / 1000)
            try:
                r = requests.post(self._service_url, json=data.to_json())
                if 200 <= r.status_code < 300:
                    logging.info("Registered callback '%s' on server '%s'", self._callback, self._service_url)
                    return
                else:
                    logging.error("Failed to register callback '%s' on server '%s'. Error: %s. %s attempts left ...",
                                  self._callback, self._service_url, r.text, attempts - i - 1)
            except:
                logging.error("Failed to register callback '%s' on server '%s'. Error: %s. %s attempts left ...",
                              self._callback, self._service_url, sys.exc_info()[1], attempts - i - 1)

        logging.error("Failed to register callback '%s' on server '%s'", self._callback, self._service_url)

    def safe_process(self, store_config: Dict, project_name: str, asset_name: str, task_options: Dict):
        try:
            self._file_controller.setup(store_config)

            meta = self._file_controller.get_asset_meta(project_name=project_name, asset_name=asset_name)
            self.update_status(WorkerStatus.PROCESSING)
            self._file_controller.lock_asset(project_name=project_name, meta=meta, worker_name=self._name)

            self.process(project_name=project_name, meta=meta, options=task_options)

            self._file_controller.unlock_asset(project_name=project_name, meta=meta)
            self.update_status(WorkerStatus.READY)
            self._file_controller.clean()
        except:
            logging.error("Error while trying to process (%s, %s). Error: %s", project_name, asset_name, sys.exc_info()[1])
            self.report_error("Error while trying to process ({}, {}). Check worker logs for details.".format(project_name, asset_name))

    @abstractmethod
    def worker_type(self) -> str:
        """
        :return: the worker type as a string. This value can be a valid WorkerType or anything else
        """
        return ""

    @abstractmethod
    def extensions(self) -> List:
        """
        :return: the extensions handled by this worker
        """
        return []

    @abstractmethod
    def description(self) -> str:
        """
        :return: description in human-readable format
        """
        return ""

    @abstractmethod
    def process(self, project_name: str, meta: OveMeta, options: Dict):
        """
        Override this to start processing
        :param project_name: name of the project to process
        :param meta: the object to process
        :param options: task options, passed by the asset manager. Can be empty
        :return: None
        :raises: Any exception is treated properly and logged by the safe_process method
        """
        pass


def register_callback(worker: BaseWorker, attempts: int = 5, timeout: int = 1000):
    p = Process(target=worker.register_callback, name="register_callback", args=(attempts, timeout), daemon=True)
    p.start()


def process_request(worker: BaseWorker, store_config: Dict, project_name: str, asset_name: str, task_options: Dict, ):
    p = Process(target=worker.safe_process, name="worker_process", args=(store_config, project_name, asset_name, task_options), daemon=True)
    p.start()
