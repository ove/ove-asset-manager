import logging
from importlib import import_module
from typing import Callable, Set

from common.errors import ValidationError


def parse_logging_lvl(lvl_name: str) -> int:
    if lvl_name:
        lvl_name = lvl_name.strip().upper()
        return logging._nameToLevel.get(lvl_name, logging.INFO)
    else:
        return logging.INFO


def to_bool(value):
    """
    Converts 'something' to boolean. Raises exception if it gets a string it doesn't handle.
    Case is ignored for strings. These string values are handled:
      True: 'True', "1", "TRue", "yes", "y", "t"
      False: "", "0", "faLse", "no", "n", "f"
    Non-string values are passed to bool.
    """
    if isinstance(value, str):
        if value.lower() in ("yes", "y", "true", "t", "1"):
            return True
        if value.lower() in ("no", "n", "false", "f", "0", ""):
            return False
        raise ValidationError(description='Invalid value for boolean conversion: ' + value)
    return bool(value)


def is_empty_str(data: str) -> bool:
    return data is None or len(data.strip()) == 0


def append_slash(path: str) -> str:
    return path if path.endswith("/") else path + "/"


def dynamic_import(full_class_path: str) -> Callable:
    if not full_class_path:
        raise ValueError("Invalid class provided '{}'".format(full_class_path))

    abs_module_path, class_name = full_class_path.rsplit(".", maxsplit=1)
    module_object = import_module(abs_module_path)
    return getattr(module_object, class_name)


def is_public(path: str, public_paths: Set[str]) -> bool:
    return any(path.startswith(item) for item in public_paths)
