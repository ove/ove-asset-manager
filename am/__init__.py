import logging

import falcon

from am.controller import FileController
from am.managers import WorkerManager
from am.middleware import RequireAuthGroups
from am.routes import AssetCreate, AssetList, AssetUpload, WorkersStatusRoute, ObjectInfo, AuthRoute, UserEdit, UserInfo, GroupsInfo, ProjectAccessMetaEdit, WorkerQueue
from am.routes import WorkersEdit, StoreList, AssetMetaEdit, ProjectCreate, ProjectList, ObjectEdit, TagEdit, ProjectMetaEdit, FileList, ProjectVersion
from common.auth import AuthManager
from common.consts import DEFAULT_CREDENTIALS_CONFIG, DEFAULT_AUTH_CONFIG, DEFAULT_WORKER_CONFIG
from common.errors import handle_exceptions
from common.middleware import RequireJSON, CORSComponent, AuthMiddleware
from common.util import parse_logging_lvl


def setup_app(logging_level: str = "debug", credentials_config: str = DEFAULT_CREDENTIALS_CONFIG, auth_config: str = DEFAULT_AUTH_CONFIG,
              worker_config: str = DEFAULT_WORKER_CONFIG) -> falcon.API:
    logging.basicConfig(level=parse_logging_lvl(logging_level), format='[%(asctime)s] [%(levelname)s] %(message)s')

    file_controller = FileController(config_file=credentials_config)
    worker_manager = WorkerManager(config_file=worker_config, controller=file_controller)

    auth = AuthManager(config_file=auth_config)

    app = falcon.API(middleware=[RequireJSON(), CORSComponent(), AuthMiddleware(auth=auth, public_paths={"/api/auth"}), RequireAuthGroups(controller=file_controller)])

    app.add_route('/api/auth', AuthRoute(auth=auth))
    app.add_route('/api/user', UserEdit(auth=auth))
    app.add_route('/api/user/groups', GroupsInfo(auth=auth))
    app.add_route('/api/user/info', UserInfo(auth=auth))
    app.add_route('/api/workers', WorkersEdit(worker_manager=worker_manager))
    app.add_route('/api/workers/status', WorkersStatusRoute(worker_manager=worker_manager))
    app.add_route('/api/workers/queue', WorkerQueue(controller=file_controller, worker_manager=worker_manager))
    app.add_route('/api/list', StoreList(controller=file_controller))
    app.add_route('/api/{store_id}/list', ProjectList(controller=file_controller))
    app.add_route('/api/{store_id}/create', ProjectCreate(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/version', ProjectVersion(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/list', AssetList(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/create', AssetCreate(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/projectMeta', ProjectMetaEdit(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/projectAccessMeta', ProjectAccessMetaEdit(controller=file_controller))
    # had to redo the routes because the falcon parser cannot parse routes with the same prefix
    app.add_route('/api/{store_id}/{project_id}/object/{object_id}', ObjectEdit(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/object/{object_id}/info', ObjectInfo(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/files/{asset_id}', FileList(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/meta/{asset_id}', AssetMetaEdit(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/upload/{asset_id}', AssetUpload(controller=file_controller))
    app.add_route('/api/{store_id}/{project_id}/tags/{asset_id}', TagEdit(controller=file_controller))

    app.add_error_handler(Exception, handle_exceptions)

    return app
