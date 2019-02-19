import logging

import falcon

from am.controller import FileController
from am.managers import WorkerManager
from am.routes import AssetCreateUpload, AssetCreate, AssetList, AssetUpload, AssetUpdate, WorkerSchedule, WorkersStatusRoute
from am.routes import WorkersEdit, StoreList, MetaEdit, ProjectCreate, ProjectList, ObjectEdit, ProjectValidateName, TagEdit
from common.consts import DEFAULT_CONFIG
from common.errors import handle_exceptions
from common.middleware import RequireJSON, CORSComponent
from common.util import parse_logging_lvl


def setup_app(logging_level: str = "debug", config_file: str = DEFAULT_CONFIG) -> falcon.API:
    logging.basicConfig(level=parse_logging_lvl(logging_level), format='[%(asctime)s] [%(levelname)s] %(message)s')

    file_controller = FileController(config_file=config_file)
    worker_manager = WorkerManager()

    app = falcon.API(middleware=[RequireJSON(), CORSComponent()])

    app.add_route('/api/workers', WorkersEdit(worker_manager=worker_manager))
    app.add_route('/api/workers/status', WorkersStatusRoute(worker_manager=worker_manager))
    app.add_route('/api/list', StoreList(controller=file_controller))
    app.add_route('/api/{store_id}/list', ProjectList(controller=file_controller))
    app.add_route('/api/{store_id}/validate', ProjectValidateName(controller=file_controller))
    app.add_route('/api/{store_id}/create', ProjectCreate(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/list', AssetList(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/create', AssetCreate(controller=file_controller))
    # had to redo the routes because the falcon parser cannot parse routes with the same prefix
    app.add_route('/api/{store_id}/{project_id}/object/{object_id}', ObjectEdit(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/meta/{asset_id}', MetaEdit(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/upload/{asset_id}', AssetUpload(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/update/{asset_id}', AssetUpdate(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/createUpload/{asset_id}', AssetCreateUpload(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/process/{asset_id}', WorkerSchedule(controller=file_controller, worker_manager=worker_manager))
    app.add_route('/api/{store_id}/{project_id}/tags/{asset_id}', TagEdit(controller=file_controller))

    app.add_error_handler(Exception, handle_exceptions)

    return app
