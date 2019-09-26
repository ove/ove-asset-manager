import json
import logging
import os
from tempfile import TemporaryDirectory
from typing import Dict, List

from tulip import tlp

from common.entities import OveAssetMeta, WorkerType
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
        options = {'fields': {}}

        for algorithm in algorithms:
            default_params = tlp.getDefaultPluginParameters(algorithm)

            for field in default_params:
                if field != 'result':
                    field_name = algorithm + "_" + field

                    default = str(default_params[field])
                    if default == 'True' or default == 'False':
                        input_type = 'checkbox'
                        data_type = 'boolean'
                    else:
                        input_type = 'text'
                        data_type = 'string'

                    properties[field_name] = {
                        'type': data_type,
                        'title': field_name,
                        'default': default_params[field]
                    }

                    dependencies[field_name] = ['algorithm']
                    options['fields'][field_name] = {'type': input_type}
                    options[field_name] = {'type': input_type, 'dependencies': {'algorithm': algorithm}}
                    if default == 'True' or default == 'False':
                        options[field_name]['rightLabel'] = 'Enabled'

        options['result_name'] = {
            'helper': "Supported formats: TLP (.tlp, .tlp.gz, .tlpz), TLP Binary (.tlpb, .tlpb.gz, .tlpbz), TLP JSON (.json), GML (.gml), CSV (.csv)"
        }

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

    def process(self, project_id: str, filename: str, meta: OveAssetMeta, options: Dict):
        logging.info("Copying %s/%s/%s into the temp place ...", project_id, meta.id, filename)

        with TemporaryDirectory() as input_folder:
            with TemporaryDirectory() as output_folder:
                os.mkdir(os.path.join(input_folder, os.path.split(filename)[0]))  # make subdirectory for asset version number

                network_file = os.path.join(input_folder, filename)
                open(network_file, 'a').close()

                self._file_controller.download_asset(project_id=project_id, asset_id=meta.id, filename=filename, down_filename=network_file)

                algorithm = options.get('algorithm', "FM^3 (OGDF)")

                params = tlp.getDefaultPluginParameters(algorithm)
                for param in params:
                    params[param] = self.convert_param(options.get(algorithm + '_' + param, params[param]))

                logging.info("Received options %s ...", options)
                logging.info("Performing layout using algorithm %s and options %s ...", algorithm, params)

                graph = tlp.loadGraph(network_file)
                graph.applyLayoutAlgorithm(algorithm, params)

                result_name = options.get('result_name')
                if not result_name:
                    result_name = meta.id.split('.')[0] + '.gml'
                tlp.saveGraph(graph, os.path.join(output_folder, result_name))

                with open(os.path.join(output_folder, result_name + ".options"), 'w') as fp:
                    json.dump(options, fp)

                self._file_controller.upload_asset_folder(project_id=project_id, meta=meta, upload_folder=output_folder,
                                                          worker_name=self.name)

        base_name = os.path.splitext(os.path.basename(filename))[0]
        meta.index_file = os.path.join(meta.worker_root + self.name, base_name, result_name)

        self._file_controller.set_asset_meta(project_id=project_id, asset_id=meta.id, meta=meta)
        logging.info("Finished generating %s/%s into the storage ...", project_id, meta.id)

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
