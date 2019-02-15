import logging
import os

import falcon

from am.consts import DEFAULT_CONFIG
from am.errors import handle_exceptions
from am.fileStoreInterpret import FileController
from am.fileStoreInterpret import FileController
from am.middleware import RequireJSON, CORSComponent
from am.routes import AssetCreateUpload, AssetCreate, AssetList, AssetUpload, AssetUpdate
from am.routes import WorkersEdit, StoreList, MetaEdit, ProjectCreate, ProjectList, ObjectEdit, ProjectValidateName, TagEdit
from common.util import parse_logging_lvl


def setup_app(logging_level: str = "debug", config_file: str = DEFAULT_CONFIG,
              proxy_url: str = "***REMOVED***") -> falcon.API:
    logging.basicConfig(level=parse_logging_lvl(logging_level), format='[%(asctime)s] [%(levelname)s] %(message)s')

    controller = FileController(config_file=config_file, proxy_url=proxy_url)

    app = falcon.API(middleware=[RequireJSON(), CORSComponent()])

    app.add_route('/api/workers', WorkersEdit(controller))
    app.add_route('/api/list', StoreList(controller))
    app.add_route('/api/{store_id}/list', ProjectList(controller))
    app.add_route('/api/{store_id}/validate', ProjectValidateName(controller))
    app.add_route('/api/{store_id}/create', ProjectCreate(controller))
    app.add_route('/api/{store_id}/{project_id}/list', AssetList(controller))
    app.add_route('/api/{store_id}/{project_id}/create', AssetCreate(controller))
    # had to redo the routes because the falcon parser cannot parse routes with the same prefix
    app.add_route('/api/{store_id}/{project_id}/object/{object_id}', ObjectEdit(controller))
    app.add_route('/api/{store_id}/{project_id}/meta/{asset_id}', MetaEdit(controller))
    app.add_route('/api/{store_id}/{project_id}/upload/{asset_id}', AssetUpload(controller))
    app.add_route('/api/{store_id}/{project_id}/update/{asset_id}', AssetUpdate(controller))
    app.add_route('/api/{store_id}/{project_id}/createUpload/{asset_id}', AssetCreateUpload(controller))
    app.add_route('/api/{store_id}/{project_id}/tags/{asset_id}', TagEdit(controller))

    app.add_static_route("/", os.getcwd() + "/static/")

    app.add_error_handler(Exception, handle_exceptions)

    return app
