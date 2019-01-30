import falcon

from am.errors import MissingParameterError
from am.errors import InvalidNameError


def validate_not_null(req: falcon.Request, field: str):
    if not req.media.get(field, None):
        raise MissingParameterError(name=field)


def validate_no_slashes(req: falcon.Request, field: str):
    if "/" in req.media.get(field):
        raise InvalidNameError(name=field)
