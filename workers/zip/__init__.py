import logging
from typing import Dict, Union

from common.entities import OveMeta, WorkerType
from workers.base import BaseWorker


class ZipWorker(BaseWorker):
    def worker_type(self) -> Union[WorkerType, None]:
        return WorkerType.ZIP

    def process(self, project_name: str, meta: OveMeta, options: Dict):
        logging.info("Unzipping")
