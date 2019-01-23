import logging


def parse_logging_lvl(lvl_name: str) -> int:
    if lvl_name:
        lvl_name = lvl_name.strip().upper()
        return logging._nameToLevel.get(lvl_name, logging.INFO)
    else:
        return logging.INFO
