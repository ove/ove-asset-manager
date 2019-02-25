import falcon

from common.middleware import HTTP_WRITE_METHODS


class ContentTypeValidator:
    def process_resource(self, req: falcon.Request, _resp: falcon.Response, resource, _params):
        if req.method in HTTP_WRITE_METHODS:
            content_type = getattr(resource, 'content_type', 'application/x-www-form-urlencoded')
            if content_type and content_type not in req.content_type:
                raise falcon.HTTPUnsupportedMediaType(description="This API only supports requests encoded as '" + content_type + "'")
