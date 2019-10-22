import datetime
import json
import logging
import os
import sys
from typing import Dict, Tuple

from bson import ObjectId
from pymongo import MongoClient, ASCENDING
from pymongo.collection import Collection
from pymongo.errors import CollectionInvalid

from am import FileController
from common.consts import *
from common.entities import OveAssetMeta, TaskStatus, UserAccessMeta
from common.errors import MissingParameterError, WorkerNotFoundError
from common.util import is_empty_str

VALIDATION_WORKER = {"$jsonSchema": {
    "bsonType": "object",
    "required": ["name", "type", "description", "extensions", "status", "docs"],
    "properties": {
        "name": {
            "bsonType": "string",
            "description": "name, required"
        },
        "type": {
            "bsonType": "string",
            "description": "worker type, required"
        },
        "description": {
            "bsonType": "string",
            "description": "worker type, required"
        },
        "extensions": {
            "bsonType": "array",
            "items": {
                "bsonType": "string",
            },
            "description": "accepted extensions, required"
        },
        "status": {
            "bsonType": "string",
            "description": "worker status, required"
        },
        "docs": {
            "bsonType": "string",
            "description": "worker docs, required"
        },
        "parameters": {
            "bsonType": "object"
        }
    }
}}

VALIDATION_QUEUE = {"$jsonSchema": {
    "bsonType": "object",
    "required": ["storeID", "projectID", "assetID", "workerType", "username"],
    "properties": {
        "startTime": {
            "bsonType": "date",
            "description": "Start time optional"
        },
        "endTime": {
            "bsonType": "date",
            "description": "End time optional"
        },
        "createdOn": {
            "bsonType": "date",
            "description": "Created date optional"
        },
        "priority": {
            "bsonType": "int",
            "description": "Priority optional"
        },
        "storeID": {
            "bsonType": "string",
            "description": "Store ID, required"
        },
        "projectID": {
            "bsonType": "string",
            "description": "Project ID, required"
        },
        "assetID": {
            "bsonType": "string",
            "description": "Asset ID, required"
        },
        "workerType": {
            "bsonType": "string",
            "description": "worker type, required"
        },
        "workerName": {
            "bsonType": "string",
            "description": "worker type, required"
        },
        "username": {
            "bsonType": "string",
            "description": "username, required"
        },
        "filename": {
            "bsonType": "string",
            "description": "filename"
        },
        "extension": {
            "bsonType": "string",
            "description": "extension"
        },
        "taskOptions": {
            "bsonType": "object"
        },
        "credentials": {
            "bsonType": "object"
        },
        "status": {
            "bsonType": "string",
            "description": "Status message"
        },
        "error": {
            "bsonType": "string",
            "description": "Error message, if any"
        },
    }
}}


class WorkerManager:
    def __init__(self, controller: FileController, config_file: str = DEFAULT_WORKER_CONFIG):
        self._client = None
        self._worker_collection = None
        self._worker_queue = None

        self._controller = controller

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
                self._worker_collection = self.setup(db_name=mongo_config.get(CONFIG_MONGO_DB),
                                                     collection_name=mongo_config.get(CONFIG_MONGO_WORKER_COLLECTION),
                                                     validator=VALIDATION_WORKER, index=("name", ASCENDING))
                self._worker_queue = self.setup(db_name=mongo_config.get(CONFIG_MONGO_DB),
                                                collection_name=mongo_config.get(CONFIG_MONGO_QUEUE_COLLECTION),
                                                validator=VALIDATION_QUEUE)
                logging.info("Loaded worker config...")
        except:
            logging.error("Error while trying to load worker config. Error: %s", sys.exc_info()[1])

    def remove_worker(self, name: str) -> bool:
        result = self._worker_collection.delete_many({"name": name})
        if result.deleted_count > 0:
            return True
        else:
            raise WorkerNotFoundError()

    def worker_info(self, name: str = None):
        return [w for w in self._worker_collection.find({"name": name} if name else {}, {"_id": 0})]

    def worker_status(self, name: str = None):
        return {w.get("name", ""): w.get("status", "") for w in self._worker_collection.find({"name": name} if name else {})}

    def worker_queue(self, user: UserAccessMeta):
        def has_access(d: Dict) -> bool:
            return self._controller.has_access(store_id=d.get("storeID", ""), project_id=d.get("projectID", ""), groups=user.write_groups, is_admin=user.admin_access)

        return [_format(w) for w in self._worker_queue.find({}, {"credentials": 0}) if has_access(w)]

    def schedule_task(self, store_id: str, project_id: str, meta: OveAssetMeta, worker_type: str, username: str, store_config: Dict, task_options: Dict, priority: int):
        filename = task_options.get("filename", meta.filename)
        if filename is None or len(filename) == 0:
            filename = meta.filename

        extension = os.path.splitext(filename)[1] if filename else ""

        self._worker_queue.insert_one({"createdOn": datetime.datetime.utcnow(), "priority": priority, "status": str(TaskStatus.NEW), "username": username,
                                       "storeID": store_id, "projectID": project_id, "assetID": meta.id, "filename": filename, "extension": extension,
                                       "workerType": worker_type, "taskOptions": task_options, "credentials": store_config})

    def cancel_task(self, task_id: str, user: UserAccessMeta) -> bool:
        task = self._worker_queue.find_one({"_id": ObjectId(task_id)})
        if task and self._controller.has_access(store_id=task.get("storeID", ""), project_id=task.get("projectID", ""), groups=user.write_groups, is_admin=user.admin_access):
            task_diff = {"status": str(TaskStatus.CANCELED), "startTime": datetime.datetime.utcnow(), "endTime": datetime.datetime.utcnow()}
            self._worker_queue.find_one_and_update({"_id": ObjectId(task_id)}, {"$set": task_diff})
            return True
        else:
            return False

    def reset_task(self, task_id: str, user: UserAccessMeta):
        task = self._worker_queue.find_one({"_id": ObjectId(task_id)})
        if task and self._controller.has_access(store_id=task.get("storeID", ""), project_id=task.get("projectID", ""), groups=user.write_groups, is_admin=user.admin_access):
            self._worker_queue.find_one_and_update({"_id": ObjectId(task_id)}, {"$set": {"status": str(TaskStatus.NEW)}, "$unset": {"startTime": "", "endTime": ""}})
            return True
        else:
            return False

    def setup(self, db_name: str, collection_name: str, validator: Dict, index: Tuple = None) -> Collection:
        db = self._client[db_name]
        try:
            collection = db.create_collection(collection_name, validator=validator)
            if index:
                collection.create_index([index], unique=True)
            return collection
        except CollectionInvalid:
            return db[collection_name]

    def close(self):
        if self._client:
            self._client.close()


def _validate_field(data, field: str):
    if is_empty_str(getattr(data, field, None)):
        raise MissingParameterError(field)


_DATE_FIELDS = ["startTime", "endTime", "createdOn"]


def _format(d: Dict) -> Dict:
    if "_id" in d:
        d["_id"] = str(d["_id"])

    for field in _DATE_FIELDS:
        if field in d:
            d[field] = '{0:%Y-%m-%d %H:%M:%S}'.format(d[field])

    return d
