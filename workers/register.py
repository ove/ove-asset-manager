import logging
import sys
import time
from multiprocessing import Process
from typing import List

import requests

from common.entities import WorkerData, WorkerType, WorkerStatus


def _register_callback(service_url: str, callback: str, extensions: List, attempts: int, timeout: int):
    data = WorkerData(name=callback, callback=callback, type=WorkerType.ZIP, status=WorkerStatus.READY,
                      extensions=extensions if extensions is not None else [])
    for i in range(attempts):
        logging.info("Register callback timeout %s ms", timeout)
        time.sleep(timeout / 1000)
        try:
            r = requests.post(service_url, json=data.to_json())
            if 200 <= r.status_code < 300:
                logging.info("Registered callback '%s' on server '%s'", callback, service_url)
                return
            else:
                logging.error("Failed to register callback '%s' on server '%s'. Error: %s. %s attempts left ...",
                              callback, service_url, r.text, attempts - i - 1)
        except:
            logging.error("Failed to register callback '%s' on server '%s'. Error: %s. %s attempts left ...",
                          callback, service_url, sys.exc_info()[1], attempts - i - 1)

    logging.error("Failed to register callback '%s' on server '%s'", callback, service_url)


def register_callback(service_url: str, callback: str, extensions: List = None, attempts: int = 5, timeout: int = 1000):
    p = Process(target=_register_callback, name="register_callback", args=(service_url, callback, extensions, attempts, timeout), daemon=True)
    p.start()
