import logging

import falcon

from am.apiAM import WorkersList, StoreList, AssetCreate, AssetList, AssetUpload, MetaEdit, ProjectCreate, ProjectList
from am.util import parse_logging_lvl


def setup_app(logging_level: str = "debug") -> falcon.API:
    logging.basicConfig(level=parse_logging_lvl(logging_level), format='[%(asctime)s] [%(levelname)s] %(message)s')

    app = falcon.API()

    app.add_route('/api/listworkers', WorkersList())
    app.add_route('/api/liststore', StoreList())
    app.add_route('/api/{store_id}/list', ProjectList())
    app.add_route('/api/{store_id}/{project_id}/listall', AssetList())
    app.add_route('/api/{store_id}/create', ProjectCreate())
    app.add_route('/api/{store_id}/{project_id}/create', AssetCreate())
    app.add_route('/api/{store_id}/{project_id}/{asset_id}/meta', MetaEdit())
    app.add_route('/api/{store_id}/{project_id}/{asset_id}/upload', AssetUpload())

    return app
