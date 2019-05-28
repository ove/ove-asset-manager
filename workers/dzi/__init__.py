import logging
import os
from tempfile import TemporaryDirectory, NamedTemporaryFile
from typing import Dict, List

import pyvips

from common.entities import OveAssetMeta, WorkerType
from workers.base import BaseWorker


class DeepZoomImageWorker(BaseWorker):
    def worker_type(self) -> str:
        return WorkerType.DZ_IMAGE.value

    def extensions(self) -> List:
        return [".jpg", ".jpeg", ".png", ".tiff", ".tif", ".gif"]

    def description(self) -> str:
        return "Converts large images into a Deep Zoom Tiled Image (DZI)"

    def docs(self) -> str:
        return "DeepZoomImageWorker.md"

    def parameters(self) -> Dict:
        return {}

    def process(self, project_name: str, filename: str, meta: OveAssetMeta, options: Dict):
        logging.info("Copying %s/%s/%s into the temp place ...", project_name, meta.name, filename)

        with TemporaryDirectory() as folder:
            with NamedTemporaryFile() as image_file:
                self._file_controller.download_asset(project_name=project_name, asset_name=meta.name, filename=filename, down_filename=image_file.name)
                pyvips.Image.new_from_file(image_file.name).dzsave(folder + "/image", suffix=".png")
                self._file_controller.upload_asset_folder(project_name=project_name, meta=meta, upload_folder=folder, worker_name=self.name)
        meta.index_file = meta.worker_root + self.name + "/" + os.path.splitext(os.path.basename(filename))[0] + "/" + "image.dzi"
        self._file_controller.set_asset_meta(project_name, meta.name, meta)
        logging.info("Finished generating %s/%s into the storage ...", project_name, meta.name)
