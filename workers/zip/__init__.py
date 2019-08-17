import glob
import logging
import os
from tempfile import TemporaryDirectory, NamedTemporaryFile
from typing import Dict, List, Union, Set
from zipfile import ZipFile

from common.entities import OveAssetMeta, WorkerType
from common.util import append_slash
from workers.base import BaseWorker


class ZipWorker(BaseWorker):
    def worker_type(self) -> str:
        return WorkerType.EXTRACT.value

    def extensions(self) -> List:
        return [".zip"]

    def description(self) -> str:
        return "Extracts zip archives"

    def docs(self) -> str:
        return "ZipWorker.md"

    def parameters(self) -> Dict:
        return {
            "schema": {
                "type": "object",
                "properties": {
                    "index_file": {
                        "type": "string",
                        "title": "Index File",
                    }
                }
            }
        }

    def process(self, project_id: str, filename: str, meta: OveAssetMeta, options: Dict):
        logging.info("Copying %s/%s/%s into the temp place ...", project_id, meta.name, filename)

        index_files = set()
        if options.get("index_file", None):
            index_files.add(options.get("index_file").strip().lower())
        else:
            index_files.update({"index.html", "index.htm", "index.js"})

        with TemporaryDirectory() as folder:
            with NamedTemporaryFile() as zip_file:
                self._file_controller.download_asset(project_id=project_id, asset_id=meta.name, filename=filename, down_filename=zip_file.name)
                ZipFile(zip_file.name).extractall(path=folder)
                self._file_controller.upload_asset_folder(project_id=project_id, meta=meta, upload_folder=folder, worker_name=self.name)

            meta_filename_name = os.path.splitext(os.path.basename(meta.filename))[0]
            meta.index_file = meta.worker_root + self.name + "/" + meta_filename_name + "/" + _guess_index_file(folder, index_files=index_files)
            self._file_controller.set_asset_meta(project_id, meta.name, meta)

        logging.info("Finished unzipping %s/%s into the storage ...", project_id, meta.name)


def _guess_index_file(folder: str, index_files: Set[str]) -> Union[str, None]:
    result = None

    for filename in glob.iglob(append_slash(folder) + '**/*', recursive=True):
        if not os.path.islink(filename) and not os.path.ismount(filename) and os.path.isfile(filename):
            if not result:
                result = filename[len(folder) + 1:]
            elif any(filename.lower().endswith(suffix) for suffix in index_files):
                result = filename[len(folder) + 1:]

    return result or ""
