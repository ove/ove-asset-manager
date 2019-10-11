import logging
from typing import Set

import falcon

from common.falcon_utils import auth_token
from common.middleware import HTTP_WRITE_METHODS
from common.util import is_public
from ui import BackendController


class ContentTypeValidator:
    def process_resource(self, req: falcon.Request, _resp: falcon.Response, resource, _params):
        if req.method in HTTP_WRITE_METHODS:
            content_type = getattr(resource, 'content_type', 'application/x-www-form-urlencoded')
            if content_type and content_type not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(description="This API only supports requests encoded as '" + content_type + "'")


class LoginValidator:
    def __init__(self, backend: BackendController, login_path: str, public_paths: Set[str] = None):
        self.login_path = login_path
        self.public_paths = public_paths if public_paths else set()
        self.public_paths.add(login_path)

        self._backend = backend

    def process_resource(self, req: falcon.Request, resp: falcon.Response, _resource, _params):
        if is_public(req.path, self.public_paths):
            logging.debug("This is a public resource which does not need a valid token")
            return

        token = auth_token(req)
        if not token:
            raise falcon.HTTPSeeOther(self.login_path)

        resp.auth_user = self._backend.user_info(auth_token=token)
