import logging
import pyvips
import os
from tempfile import TemporaryDirectory, NamedTemporaryFile
from typing import Dict, List


from common.entities import OveMeta, WorkerType
from workers.base import BaseWorker


class ImageWorker(BaseWorker):
    def worker_type(self) -> str:
        return WorkerType.DZ_IMAGE.value

    def extensions(self) -> List:
        return [".jpg", ".png", ".tiff", ".bmp"]

    def description(self) -> str:
        return "Converts large images into DZI tiled gigaimages"

    def process(self, project_name: str, meta: OveMeta, options: Dict):
        logging.info("Copying %s/%s into the temp place ...", project_name, meta.name)

        with TemporaryDirectory() as folder:
            with NamedTemporaryFile() as image_file:
                self._file_controller.download_asset(project_name=project_name, asset_name=meta.name, filename=meta.file_location, down_filename=image_file.name)
                pyvips.Image.new_from_file(image_file.name).dzsave(folder + "/image")
                self._file_controller.upload_asset_folder(project_name=project_name, meta=meta, upload_folder=folder, worker_name=self.name)
        meta.index_file = meta.worker_root + self.name + "/" + os.path.splitext(os.path.basename(meta.filename))[0] + "/" + "image.dzi"
        self._file_controller.set_asset_meta(project_name, meta.name, meta)
        logging.info("Finished generating %s/%s into the storage ...", project_name, meta.name)
