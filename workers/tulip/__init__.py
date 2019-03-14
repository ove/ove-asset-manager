import logging
from tulip import tlp
import os
from tempfile import TemporaryDirectory
from typing import Dict, List
import json

from common.entities import OveMeta, WorkerType
from workers.base import BaseWorker


class NetworkWorker(BaseWorker):
    def worker_type(self) -> str:
        return WorkerType.TULIP.value

    def extensions(self) -> List:
        return ['.tlp', '.tlp.gz', '.tlpz', '.tlpb', '.tlpb.gz', '.tlpbz', '.json', '.gexf', '.net', '.paj', '.gml',
                '.dot', '.txt']

    def description(self) -> str:
        return "Applies a layout algorithm to a network using the Tulip framework"

    def docs(self) -> str:
        return "Tulip.md"

    def parameters(self) -> Dict:

        algorithms = tlp.getLayoutAlgorithmPluginsList()

        properties = {
            "result_name": {
                "title": "Output filename:",
                "type": "string",
                "required": False
            },
            "algorithm": {
                "title": "Layout Algorithm",
                "type": "string",
                "enum": algorithms,
                "required": True
            }
        }
        dependencies = {}
        options = {}

        for algorithm in algorithms:
            default_params = tlp.getDefaultPluginParameters(algorithm)

            for field in default_params:
                if field != 'result':
                    field_name = algorithm + "_" + field

                    properties[field_name] = {
                        'type': 'string',
                        'title': field_name,
                        'default': str(default_params[field])
                    }

                    dependencies[field_name] = ['algorithm']

                    options[field_name] = {'dependencies': {'algorithm': algorithm}}

        return {
            'schema': {
                'type': 'object',
                'properties': properties,
                "dependencies": dependencies
            },
            "options": {
                "fields": options
            }
        }

    def process(self, project_name: str, meta: OveMeta, options: Dict):
        logging.info("Copying %s/%s into the temp place ...", project_name, meta.name)

        if not options:
            options = {}

        with TemporaryDirectory() as folder:

            with TemporaryDirectory() as folder2:
                network_file = os.path.join(folder2, meta.filename)
                open(network_file, 'a').close()

                self._file_controller.download_asset(project_name=project_name, asset_name=meta.name,
                                                     filename=meta.file_location, down_filename=network_file)

                algorithm = options.get('algorithm')
                if not algorithm:
                    algorithm = "FM^3 (OGDF)"

                params = tlp.getDefaultPluginParameters(algorithm)
                for param in params:
                    params[param] = self.convert_param(options.get(param, params[param]))

                logging.info("Performing layout using algorithm %s and options %s ...", algorithm, params)
                graph = tlp.loadGraph(network_file)
                graph.applyLayoutAlgorithm(algorithm, params)

                result_name = options.get('result_name')
                if not result_name:
                    result_name = meta.name.split('.')[0] + '.gml'
                tlp.saveGraph(graph, os.path.join(folder, result_name))

                with open(os.path.join(folder, result_name + ".options"), 'w') as fp:
                    json.dump(options, fp)

                self._file_controller.upload_asset_folder(project_name=project_name, meta=meta, upload_folder=folder,
                                                          worker_name=self.name)

        base_name = os.path.splitext(os.path.basename(meta.filename))[0]
        meta.index_file = os.path.join(meta.worker_root + self.name, base_name, result_name)

        self._file_controller.set_asset_meta(project_name, meta.name, meta)
        logging.info("Finished generating %s/%s into the storage ...", project_name, meta.name)

    @staticmethod
    def convert_param(param):
        if not isinstance(param, str):
            return param
        elif str.lower(param) == 'true':
            return True
        elif str.lower(param) == 'false':
            return False
        elif str.lower(param) == 'none':
            return None
        elif str.isdigit(param):
            return int(param)
        elif param.replace('.', '', 1).isdigit():
            return float(param)
        return param
