import logging
import os

import falcon

from common.middleware import CORSComponent
from common.util import parse_logging_lvl
from ui.controller import BackendController
from ui.middleware import ContentTypeValidator, LoginValidator
from ui.routes import ProjectEdit, BackendDetailsView, ObjectEditApi, LoginView, LogoutView, ProjectAccessEdit, VersionApi, WorkerQueueView, MetaApi
from ui.routes import ProjectView, ProjectIndexView, IndexView, AssetView, WorkerView, AssetEdit, NotFoundView, handle_api_exceptions
from ui.routes import UploadApi, WorkerApi, ObjectEdit, WorkerDocsView, FilesApi


def setup_ui(logging_level: str = "debug", backend_url: str = "http://localhost:6080") -> falcon.API:
    logging.basicConfig(level=parse_logging_lvl(logging_level), format='[%(asctime)s] [%(levelname)s] %(message)s')

    _controller = BackendController(backend_url=backend_url)
    app = falcon.API(middleware=[ContentTypeValidator(), CORSComponent(), LoginValidator(login_path="/login", backend=_controller)])
    app.req_options.auto_parse_form_urlencoded = True
    app.resp_options.secure_cookies_by_default = False

    app.add_static_route("/favicon.ico", os.getcwd() + "/ui/static/favicon.ico", downloadable=True)
    app.add_static_route("/css", os.getcwd() + "/ui/static/css/", downloadable=True)
    app.add_static_route("/vendors/css", os.getcwd() + "/ui/static/vendors/css/", downloadable=True)
    app.add_static_route("/vendors/css/img", os.getcwd() + "/ui/static/vendors/css/img/", downloadable=True)
    app.add_static_route("/js", os.getcwd() + "/ui/static/js/", downloadable=True)
    app.add_static_route("/vendors/js", os.getcwd() + "/ui/static/vendors/js/", downloadable=True)
    app.add_static_route("/img", os.getcwd() + "/ui/static/img/", downloadable=True)
    app.add_static_route("/vendors/webfonts", os.getcwd() + "/ui/static/vendors/webfonts/", downloadable=True)

    # view/edit routes
    app.add_route('/login', LoginView(controller=_controller))
    app.add_route('/logout', LogoutView())
    app.add_route('/', IndexView(controller=_controller))
    app.add_route('/404', NotFoundView())
    app.add_route('/view/workers/', WorkerView(controller=_controller))
    app.add_route('/view/workers/queue/', WorkerQueueView(controller=_controller))
    app.add_route('/view/store/{store_id}/', ProjectView(controller=_controller))
    app.add_route('/view/store/{store_id}/index', ProjectIndexView(controller=_controller))
    app.add_route('/view/store/{store_id}/project/{project_id}/', AssetView(controller=_controller))
    app.add_route('/view/store/{store_id}/project/{project_id}/edit', ProjectEdit(controller=_controller))
    app.add_route('/view/store/{store_id}/project/{project_id}/access', ProjectAccessEdit(controller=_controller))
    app.add_route('/view/store/{store_id}/project/{project_id}/asset/{asset_id}', AssetEdit(controller=_controller))
    app.add_route('/view/store/{store_id}/project/{project_id}/object/{object_id}', ObjectEdit(controller=_controller))
    app.add_route('/view/backend', BackendDetailsView(controller=_controller))

    # api routes
    app.add_route('/api/store/{store_id}/project/{project_id}/object/{object_id}', ObjectEditApi(controller=_controller))
    app.add_route('/api/store/{store_id}/project/{project_id}/upload', UploadApi(controller=_controller))
    app.add_route('/api/store/{store_id}/project/{project_id}/asset/{asset_id}/upload', UploadApi(controller=_controller))
    app.add_route('/api/store/{store_id}/project/{project_id}/asset/{asset_id}/process/{worker_type}', WorkerApi(controller=_controller))
    app.add_route('/api/store/{store_id}/project/{project_id}/asset/{asset_id}/files', FilesApi(controller=_controller))
    app.add_route('/api/store/{store_id}/project/{project_id}/asset/{asset_id}/meta', MetaApi(controller=_controller))
    app.add_route('/api/store/{store_id}/project/{project_id}/version', VersionApi(controller=_controller))

    # worker docs
    app.add_route('/docs/{worker_doc}', WorkerDocsView(docs_folder=os.getcwd() + "/docs/workers/"))

    app.add_error_handler(Exception, handle_api_exceptions)

    return app
