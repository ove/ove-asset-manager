import falcon

from am.errors import MissingParameterError


def validate_not_null(req: falcon.Request, field: str):
    if not req.media.get(field, None):
        raise MissingParameterError(name=field)
