import json
import logging
import sys
import time
from abc import ABC, abstractmethod
from multiprocessing import Process
from typing import Dict, List

import urllib3

from common.entities import OveAssetMeta, WorkerStatus, WorkerData
from workers.base.controller import FileController


class BaseWorker(ABC):
    def __init__(self, name: str, callback: str, status_callback: str, service_url: str, file_controller: FileController):
        self._http = urllib3.PoolManager()
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
        payload = {"name": self.name, "status": str(status)}
        response = self._http.request(method="PATCH", url=self._service_url, body=json.dumps(payload).encode('utf-8'),
                                      headers={'Content-Type': 'application/json'})
        if 200 <= response.status < 300:
            logging.info("%s status updated on server '%s'", status, self._service_url)
            self._status = status
        else:
            logging.error("Failed to update status on server '%s'. Requested status: %s. Server error: %s", self._service_url, status, response.data)

    def report_error(self, error: str):
        payload = {"name": self.name, "status": str(WorkerStatus.ERROR), "error_msg": error}
        response = self._http.request(method="PATCH", url=self._service_url, body=json.dumps(payload).encode('utf-8'),
                                      headers={'Content-Type': 'application/json'})
        if 200 <= response.status < 300:
            logging.error("Error status updated on server '%s'. Error: %s", self._service_url, error)
            self._status = WorkerStatus.ERROR
        else:
            logging.error("Failed to update status on server '%s'. Reported error: %s. Server error: %s", self._service_url, error, response.data)

    def register_callback(self, attempts: int, timeout: int):
        data = WorkerData(name=self.name, callback=self._callback, status_callback=self._status_callback, type=self.worker_type(), docs=self.docs(),
                          description=self.description(), status=self.status, extensions=self.extensions(), parameters=self.parameters())

        for i in range(attempts):
            logging.info("Register callback timeout %s ms", timeout)
            time.sleep(timeout / 1000)
            try:
                response = self._http.request(method="POST", url=self._service_url, body=json.dumps(data.to_json()).encode('utf-8'),
                                              headers={'Content-Type': 'application/json'})
                if 200 <= response.status < 300:
                    logging.info("Registered callback '%s' on server '%s'", self._callback, self._service_url)
                    return
                else:
                    logging.error("Failed to register callback '%s' on server '%s'. Error: %s. %s attempts left ...",
                                  self._callback, self._service_url, response.data, attempts - i - 1)
            except:
                logging.error("Failed to register callback '%s' on server '%s'. Error: %s. %s attempts left ...",
                              self._callback, self._service_url, sys.exc_info()[1], attempts - i - 1)

        logging.error("Failed to register callback '%s' on server '%s'", self._callback, self._service_url)

    def unregister_callback(self):
        try:
            response = self._http.request(method="DELETE", url=self._service_url, body=json.dumps({"name": self.name}).encode('utf-8'),
                                          headers={'Content-Type': 'application/json'})
            if 200 <= response.status < 300:
                logging.info("Unregistered callback '%s' on server '%s'", self._callback, self._service_url)
                return
            else:
                logging.error("Failed to unregister callback '%s' on server '%s'. Error: %s", self._callback, self._service_url, response.data)
        except:
            logging.error("Failed to unregister callback '%s' on server '%s'. Error: %s", self._callback, self._service_url, sys.exc_info()[1])

    def safe_process(self, store_config: Dict, project_id: str, asset_id: str, task_options: Dict):
        meta = None
        try:
            self._file_controller.setup(store_config)

            meta = self._file_controller.get_asset_meta(project_id=project_id, asset_id=asset_id)
            self.update_status(WorkerStatus.PROCESSING)
            self._file_controller.lock_asset(project_id=project_id, meta=meta, worker_name=self._name)
            self._file_controller.update_asset_status(project_id=project_id, meta=meta, status=WorkerStatus.PROCESSING)

            filename = task_options.get("filename", meta.filename)
            if filename is None or len(filename) == 0:
                filename = meta.filename

            if filename is None:
                logging.error("Invalid filename provided ...")
                self.report_error("Invalid filename provided ...")
                self._file_controller.update_asset_status(project_id=project_id, meta=meta, status=WorkerStatus.ERROR,
                                                          error_msg="Invalid filename provided ...")
            else:
                filename = str(meta.version) + "/" + filename
                self.process(project_id=project_id, filename=filename, meta=meta, options=task_options)

                self._file_controller.update_asset_status(project_id=project_id, meta=meta, status=WorkerStatus.DONE)
                self.update_status(WorkerStatus.READY)
        except:
            logging.error("Error while trying to process (%s, %s). Error: %s", project_id, asset_id, sys.exc_info()[1])
            error_msg = "Error while trying to process ({}, {}). Check worker logs for details.".format(project_id, asset_id)
            self._file_controller.update_asset_status(project_id=project_id, meta=meta, status=WorkerStatus.ERROR, error_msg=error_msg)
            self.report_error(error_msg)
        finally:
            if meta is not None:
                self._file_controller.unlock_asset(project_id=project_id, meta=meta, worker_name=self._name)
            self._file_controller.clean()

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
    def docs(self) -> str:
        """
        :return: the worker documentation document url, in markdown format
        see https://github.com/trentm/python-markdown2 for more details
        """
        return ""

    @abstractmethod
    def parameters(self) -> Dict:
        """
        :return: the worker parameter description, in json-form format:
        see http://www.alpacajs.org/ for more details
        """
        return {}

    @abstractmethod
    def process(self, project_id: str, filename: str, meta: OveAssetMeta, options: Dict):
        """
        Override this to start processing
        :param project_id: name of the project to process
        :param filename: the filename to process
        :param meta: the object to process
        :param options: task options, passed by the asset manager. Can be empty
        :return: None
        :raises: Any exception is treated properly and logged by the safe_process method
        """
        pass


def register_callback(worker: BaseWorker, attempts: int = 5, timeout: int = 1000):
    p = Process(target=worker.register_callback, name="register_callback", args=(attempts, timeout), daemon=True)
    p.start()


def unregister_callback(worker: BaseWorker):
    worker.unregister_callback()


def process_request(worker: BaseWorker, store_config: Dict, project_id: str, asset_id: str, task_options: Dict, ):
    p = Process(target=worker.safe_process, name="worker_process", args=(store_config, project_id, asset_id, task_options), daemon=True)
    p.start()
