from typing import Any

import falcon

from am.errors import MissingParameterError, InvalidDataError
from am.errors import InvalidNameError


def validate_not_null(req: falcon.Request, field: str):
    if not req.media.get(field, None):
        raise MissingParameterError(name=field)


def validate_no_slashes(req: falcon.Request, field: str):
    if "/" in req.media.get(field):
        raise InvalidNameError(name=field)


def validate_list(data: Any):
    if not isinstance(data, list) or not all(isinstance(elem, str) for elem in data):
        raise InvalidDataError()
