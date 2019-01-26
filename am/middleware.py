import falcon

_HTTP_IGNORE_METHODS = {'CONNECT', 'HEAD', 'OPTIONS', 'TRACE'}
_HTTP_READ_METHODS = {'GET'}
_HTTP_WRITE_METHODS = {'DELETE', 'PATCH', 'POST', 'PUT'}


class RequireJSON(object):
    # Note: This is practical because we don't need to replicate the routing logic
    # This will not work for proxy requests, but it's not our current case
    def process_resource(self, req: falcon.Request, _resp: falcon.Response, resource, _params):
        if not req.client_accepts_json:
            raise falcon.HTTPNotAcceptable(description="This API only supports responses encoded as 'application/json'")

        if req.method in _HTTP_WRITE_METHODS:
            # check if this is special resource with a custom content-type, i.e. upload file
            content_type = getattr(resource, 'content_type', 'application/json')
            if content_type and content_type not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(description="This API only supports requests encoded as '" + content_type + "'")
