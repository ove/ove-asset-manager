import logging
import os

import falcon

from am.routes import WorkersList, StoreList, MetaEdit, ProjectCreate, ProjectList
from am.routes import AssetCreateUpload, AssetCreate, AssetList, AssetUpload
from am.routes import WorkersList, StoreList, AssetCreate, AssetList, AssetListAll, AssetUpload, MetaEdit, ProjectCreate, ProjectList
from am.fileStoreInterpret import FileController
from am.util import parse_logging_lvl


def setup_app(logging_level: str = "debug") -> falcon.API:
    logging.basicConfig(level=parse_logging_lvl(logging_level), format='[%(asctime)s] [%(levelname)s] %(message)s')

    controller = FileController()

    app = falcon.API()

    app.add_route('/api/listworkers', WorkersList(controller))
    app.add_route('/api/liststore', StoreList(controller))
    app.add_route('/api/{store_id}/list', ProjectList(controller))
    app.add_route('/api/{store_id}/{project_id}/list', AssetList(controller))
    app.add_route('/api/{store_id}/{project_id}/listall', AssetListAll(controller))
    app.add_route('/api/{store_id}/create', ProjectCreate(controller))
    app.add_route('/api/{store_id}/{project_id}/create', AssetCreate(controller))
    app.add_route('/api/{store_id}/{project_id}/{asset_id}/meta', MetaEdit(controller))
    app.add_route('/api/{store_id}/{project_id}/{asset_id}/upload', AssetUpload(controller))
    app.add_route('/api/{store_id}/{project_id}/{asset_id}/createUpload', AssetCreateUpload(controller))

    app.add_static_route("/", os.getcwd() + "/static/")

    return app
