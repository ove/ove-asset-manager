from typing import Any, Dict

from common.errors import InvalidNameError
from common.errors import MissingParameterError, InvalidDataError


def validate_not_null(data: Dict, field: str):
    if not data or not data.get(field, None):
        raise MissingParameterError(name=field)


def validate_no_slashes(data: Dict, field: str):
    if "/" in data.get(field):
        raise InvalidNameError(name=field)


def validate_list(data: Any):
    if not isinstance(data, list) or not all(isinstance(elem, str) for elem in data):
        raise InvalidDataError()
