import logging
import os

import falcon

from common.middleware import CORSComponent
from common.util import parse_logging_lvl
from ui.controller import BackendController
from ui.middleware import ContentTypeValidator
from ui.routes import ProjectView, ProjectIndexView, IndexView, AssetView, WorkerView, AssetEdit, NotFoundView, handle_api_exceptions, ProjectEdit
from ui.routes import UploadApi, WorkerApi, ObjectEdit, WorkerDocs, FilesApi


def setup_ui(logging_level: str = "debug", backend_url: str = "http://localhost:6080") -> falcon.API:
    logging.basicConfig(level=parse_logging_lvl(logging_level), format='[%(asctime)s] [%(levelname)s] %(message)s')

    _controller = BackendController(backend_url=backend_url)
    app = falcon.API(middleware=[ContentTypeValidator(), CORSComponent()])
    app.req_options.auto_parse_form_urlencoded = True

    app.add_static_route("/favicon.ico", os.getcwd() + "/ui/static/favicon.ico", downloadable=True)
    app.add_static_route("/css", os.getcwd() + "/ui/static/css/", downloadable=True)
    app.add_static_route("/vendors/css", os.getcwd() + "/ui/static/vendors/css/", downloadable=True)
    app.add_static_route("/vendors/css/img", os.getcwd() + "/ui/static/vendors/css/img/", downloadable=True)
    app.add_static_route("/js", os.getcwd() + "/ui/static/js/", downloadable=True)
    app.add_static_route("/vendors/js", os.getcwd() + "/ui/static/vendors/js/", downloadable=True)
    app.add_static_route("/img", os.getcwd() + "/ui/static/img/", downloadable=True)
    app.add_static_route("/vendors/webfonts", os.getcwd() + "/ui/static/vendors/webfonts/", downloadable=True)

    # view routes
    app.add_route('/', IndexView(controller=_controller))
    app.add_route('/404', NotFoundView())
    app.add_route('/view/workers/', WorkerView(controller=_controller))
    app.add_route('/view/store/{store_name}/', ProjectView(controller=_controller))
    app.add_route('/view/store/{store_name}/index', ProjectIndexView(controller=_controller))
    app.add_route('/view/store/{store_name}/project/{project_name}/', AssetView(controller=_controller))
    app.add_route('/view/store/{store_name}/project/{project_name}/edit', ProjectEdit(controller=_controller))
    app.add_route('/view/store/{store_name}/project/{project_name}/asset/{asset_name}', AssetEdit(controller=_controller))
    app.add_route('/view/store/{store_name}/project/{project_name}/object/{object_name}', ObjectEdit(controller=_controller))

    # api routes
    app.add_route('/api/store/{store_name}/project/{project_name}/upload', UploadApi(controller=_controller))
    app.add_route('/api/store/{store_name}/project/{project_name}/asset/{asset_name}/upload', UploadApi(controller=_controller))
    app.add_route('/api/store/{store_name}/project/{project_name}/asset/{asset_name}/process/{worker_type}', WorkerApi(controller=_controller))
    app.add_route('/api/store/{store_name}/project/{project_name}/asset/{asset_name}/files', FilesApi(controller=_controller))

    # worker docs
    app.add_route('/docs/{worker_doc}', WorkerDocs(docs_folder=os.getcwd() + "/docs/workers/"))

    app.add_error_handler(Exception, handle_api_exceptions)

    return app
