import logging
from tempfile import TemporaryDirectory, NamedTemporaryFile
from typing import Dict, List
from zipfile import ZipFile

from common.entities import OveMeta, WorkerType
from workers.base import BaseWorker


class ZipWorker(BaseWorker):
    def worker_type(self) -> str:
        return WorkerType.EXTRACT.value

    def extensions(self) -> List:
        return [".zip"]

    def description(self) -> str:
        return "Extracts zip archives"

    def process(self, project_name: str, meta: OveMeta, options: Dict):
        logging.info("Unzipping %s/%s into the temp place ...", project_name, meta.name)

        with TemporaryDirectory() as folder:
            with NamedTemporaryFile() as zip_file:
                self._file_controller.download_asset(project_name=project_name, asset_name=meta.name, filename=meta.file_location, down_filename=zip_file.name)
                ZipFile(zip_file.name).extractall(path=folder)
                self._file_controller.upload_asset_folder(project_name=project_name, meta=meta, upload_folder=folder, worker_name=self.name)

        logging.info("Finished unzipping %s/%s into the storage ...", project_name, meta.name)
