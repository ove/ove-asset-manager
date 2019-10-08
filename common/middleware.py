import logging
from typing import Union

import falcon

from common.auth import AuthManager
from common.consts import FIELD_AUTH_TOKEN
from common.entities import DbAccessMeta
from common.util import is_public

HTTP_IGNORE_METHODS = {'CONNECT', 'HEAD', 'OPTIONS', 'TRACE'}
HTTP_READ_METHODS = {'GET'}
HTTP_WRITE_METHODS = {'DELETE', 'PATCH', 'POST', 'PUT'}


class RequireJSON:
    # Note: This is practical because we don't need to replicate the routing logic
    # This will not work for proxy requests, but it's not our current case
    def process_resource(self, req: falcon.Request, _resp: falcon.Response, resource, _params):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable(description="This API only supports responses encoded as 'application/json'")

        if req.method in HTTP_WRITE_METHODS:
            # check if this is special resource with a custom content-type, i.e. upload file
            content_type = getattr(resource, 'content_type', 'application/json')
            if content_type and content_type not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(description="This API only supports requests encoded as '" + content_type + "'")


class CORSComponent:
    # This has been taken straight out the falcon tutorial and allows all requests
    def process_response(self, req, resp, _resource, req_succeeded):
        resp.set_header('Access-Control-Allow-Origin', '*')

        if req_succeeded and req.method == 'OPTIONS' and req.get_header('Access-Control-Request-Method'):
            # NOTE(kgriffs): This is a CORS preflight request. Patch the response accordingly.
            allow = resp.get_header('Allow')
            resp.delete_header('Allow')

            allow_headers = req.get_header('Access-Control-Request-Headers', default='*')

            resp.set_headers((
                ('Access-Control-Allow-Methods', allow),
                ('Access-Control-Allow-Headers', allow_headers),
                ('Access-Control-Max-Age', '86400'),  # 24 hours
            ))


class AuthMiddleware:
    def __init__(self, auth: AuthManager, public_paths: set = None):
        self.auth = auth
        self.public_paths = public_paths if public_paths else set()

    def process_request(self, req: falcon.Request, _resp: falcon.Response):
        if is_public(req.path, self.public_paths):
            logging.debug("This is a public resource which does not need a valid token")
            return

        token = self.auth.decode_token(_get_token(req, field=FIELD_AUTH_TOKEN))
        _check_access(method=req.method, token=token)

        req.auth_user = token.user
        req.auth_groups = token.groups or []
        req.auth_write_access = token.write_access
        req.auth_admin_access = token.admin_access


def _check_access(method: str, token: Union[DbAccessMeta, None]):
    if method in HTTP_IGNORE_METHODS:
        return
    elif method in HTTP_READ_METHODS and not token:
        raise falcon.HTTPUnauthorized(title='Access token required for READ operation',
                                      description='Please provide a valid access token as part of the request.')
    elif method in HTTP_WRITE_METHODS and not (token and token.write_access):
        raise falcon.HTTPUnauthorized(title='Access token required for WRITE operation',
                                      description='Please provide a valid access token as part of the request.')


def _get_token(req: falcon.Request, field: str) -> Union[str, None]:
    token = req.get_header(field, None)
    if token is not None:
        return token

    token = req.params.get(field, None)
    if token is not None:
        return token

    # Because every time you lose something, you always find it in the very last place you would look.
    return req.cookies.get(field, None)
