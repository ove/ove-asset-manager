import datetime
import json
import logging
import sys
import time
from abc import ABC, abstractmethod
from multiprocessing import Process
from typing import Dict, List

import pymongo
from bson import ObjectId
from pymongo import MongoClient
from pymongo.collection import Collection

from common.consts import *
from common.entities import OveAssetMeta, WorkerStatus, TaskStatus
from workers.base.controller import FileController


class BaseWorker(ABC):
    def __init__(self, name: str, file_controller: FileController, config_file: str = DEFAULT_WORKER_CONFIG):
        self._name = name
        self._status = WorkerStatus.READY

        self._file_controller = file_controller

        self._client = None
        self._worker_collection = None
        self._worker_queue = None

        self.running = True
        self.worker_process = Process(target=self.worker_loop, name="worker_process", args=(config_file,), daemon=True)
        self.worker_process.start()

        self.load(config_file=config_file)

    def load(self, config_file: str = DEFAULT_WORKER_CONFIG):
        try:
            with open(config_file, mode="r") as fin:
                config = json.load(fin)

                mongo_config = config.get(CONFIG_MONGO, {}) or {}
                self._client = MongoClient(host=mongo_config.get(CONFIG_MONGO_HOST),
                                           port=mongo_config.get(CONFIG_MONGO_PORT),
                                           username=mongo_config.get(CONFIG_MONGO_USER),
                                           password=mongo_config.get(CONFIG_MONGO_PASSWORD),
                                           authSource=mongo_config.get(CONFIG_MONGO_DB),
                                           authMechanism=mongo_config.get(CONFIG_MONGO_MECHANISM))
                self._worker_collection = self.setup(db_name=mongo_config.get(CONFIG_MONGO_DB), collection_name=mongo_config.get(CONFIG_MONGO_WORKER_COLLECTION))
                self._worker_queue = self.setup(db_name=mongo_config.get(CONFIG_MONGO_DB), collection_name=mongo_config.get(CONFIG_MONGO_QUEUE_COLLECTION))
                logging.info("Loaded worker config...")
        except:
            logging.error("Error while trying to load worker config. Error: %s", sys.exc_info()[1])

    def setup(self, db_name: str, collection_name: str) -> Collection:
        db = self._client[db_name]
        return db[collection_name]

    def close(self):
        self.running = False
        if self._client:
            self._client.close()

    @property
    def name(self) -> str:
        return self._name

    @property
    def status(self) -> WorkerStatus:
        return self._status

    def reset_status(self) -> WorkerStatus:
        if self.status is WorkerStatus.ERROR:
            self.update_worker_status(WorkerStatus.READY)
        return self.status

    def update_worker_status(self, status: WorkerStatus):
        self._worker_collection.find_one_and_update({"name": self.name}, {"$set": {"status": str(status)}})

    def report_task_error(self, task_id: ObjectId, error: str):
        self._worker_queue.find_one_and_update({"_id": task_id}, {"$set": {"status": str(TaskStatus.ERROR), "error": error}})

    def update_task_status(self, task_id: ObjectId, status: TaskStatus):
        self._worker_queue.find_one_and_update({"_id": task_id}, {"$set": {"status": str(status)}})

    def start_task(self, task_id: ObjectId):
        task_diff = {"workerName": self.name, "status": str(TaskStatus.PROCESSING), "startTime": datetime.datetime.utcnow()}
        self._worker_queue.find_one_and_update({"_id": task_id}, {"$set": task_diff})

    def end_task(self, task_id: ObjectId, status: TaskStatus):
        self._worker_queue.find_one_and_update({"_id": task_id}, {"$set": {"status": str(status), "endTime": datetime.datetime.utcnow()}})

    def register_worker(self):
        try:
            data = {"name": self.name, "type": self.worker_type(), "description": self.description(), "extensions": self.extensions(),
                    "status": str(self.status), "docs": self.docs(), "parameters": self.parameters()}
            self._worker_collection.insert_one(data)
            logging.info("Worker registered successfully ...")
        except:
            logging.error("Failed to unregister worker. %s", sys.exc_info()[1])

    def unregister_worker(self):
        try:
            result = self._worker_collection.delete_one({"name": self.name})
            if result.deleted_count > 0:
                logging.info("Worker unregistered successfully ...")
            else:
                logging.error("Failed to unregister worker ...")
        except:
            logging.error("Failed to unregister worker. %s", sys.exc_info()[1])

    def terminate_worker(self):
        self.worker_process.terminate()

    def worker_loop(self, config_file: str = DEFAULT_WORKER_CONFIG):
        self.load(config_file=config_file)

        if not self._client or not self._worker_queue:
            logging.error("Mongo connection not initialised. Worker queue is not running ...")
            return

        _filter = {"status": str(TaskStatus.NEW), "workerType": self.worker_type(), "extension": {"$in": self.extensions()}}
        _update = {"$set": {"status": str(TaskStatus.PROCESSING)}}
        _sort = [("priority", pymongo.DESCENDING), ("createdOn", pymongo.DESCENDING)]

        while self.running:
            try:
                job = self._worker_queue.find_one_and_update(filter=_filter, update=_update, sort=_sort)
                if job:
                    self.safe_process(task_id=job.get("_id"), project_id=job.get("projectID"), asset_id=job.get("assetID"),
                                      store_config=job.get("credentials", {}), task_options=job.get("taskOptions", {}))
                else:
                    time.sleep(5)
            except:
                logging.error("Error while trying to query collection. Error: %s", sys.exc_info()[1])

    def safe_process(self, task_id: ObjectId, store_config: Dict, project_id: str, asset_id: str, task_options: Dict):
        meta = None
        error_msg = None
        try:
            self.update_worker_status(WorkerStatus.PROCESSING)
            self.start_task(task_id)
            self._file_controller.setup(store_config)

            meta = self._file_controller.get_asset_meta(project_id=project_id, asset_id=asset_id)

            self._file_controller.lock_asset(project_id=project_id, meta=meta, worker_name=self._name)
            self._file_controller.update_asset_status(project_id=project_id, meta=meta, status=TaskStatus.PROCESSING)

            filename = task_options.get("filename", meta.filename)
            if filename is None or len(filename) == 0:
                filename = meta.filename

            if filename is None:
                logging.error("Invalid filename provided ...")
                self.report_task_error(task_id=task_id, error="Invalid filename provided ...")
                self._file_controller.update_asset_status(project_id=project_id, meta=meta, status=TaskStatus.ERROR,
                                                          error_msg="Invalid filename provided ...")
            else:
                filename = str(meta.version) + "/" + filename
                self.process(project_id=project_id, filename=filename, meta=meta, options=task_options)

                self._file_controller.update_asset_status(project_id=project_id, meta=meta, status=TaskStatus.DONE)
        except:
            error_msg = "Error: {}.".format(sys.exc_info()[1])
            logging.error("Error while trying to process ({}, {}). {}".format(project_id, asset_id, error_msg))
            self._file_controller.update_asset_status(project_id=project_id, meta=meta, status=TaskStatus.ERROR, error_msg=error_msg)
            self.report_task_error(task_id=task_id, error=error_msg)
        finally:
            if meta is not None:
                self._file_controller.unlock_asset(project_id=project_id, meta=meta, worker_name=self._name)
            self.end_task(task_id, TaskStatus.ERROR if error_msg else TaskStatus.DONE)
            self._file_controller.clean()
            self.update_worker_status(WorkerStatus.READY)

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


def register_worker(worker: BaseWorker):
    worker.register_worker()


def unregister_worker(worker: BaseWorker):
    worker.unregister_worker()
    worker.close()
