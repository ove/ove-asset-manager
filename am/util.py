import logging


def parse_logging_lvl(lvl_name: str) -> int:
    if lvl_name:
        lvl_name = lvl_name.strip().upper()
        return logging._nameToLevel.get(lvl_name, logging.INFO)
    else:
        return logging.INFO


# todo; figure out if we need this
def is_empty(any_structure):
    if any_structure:
        return False
    else:
        return True
