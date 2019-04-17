import calendar
import logging
import os
from datetime import date
from typing import Dict

import falcon

from proxy.controller import FileController


# Last-Modified →Tue, 09 Oct 2018 22:59:54 GMT

class ResourceStream:
    def __init__(self, controller: FileController):
        self._controller = controller

    def __call__(self, req: falcon.Request, resp: falcon.Response):
        if req.method == "GET":
            parts = req.path.split("/", maxsplit=3)
            if len(parts) == 4:
                # parts[0] should be empty
                _, store_name, project_name, path_name = parts

                stream_meta = self._controller.get_resource_meta(store_name=store_name, project_name=project_name, path_name=path_name)

                resp.content_type = resp.options.static_media_types.get(os.path.splitext(path_name)[1], 'application/octet-stream')
                resp.accept_ranges = "bytes"
                resp.stream_len = stream_meta.get("size", None)
                resp.last_modified = _last_modified(stream_meta)
                resp.stream = self._controller.get_resource(store_name=store_name, project_name=project_name, path_name=path_name)
                resp.status = falcon.HTTP_200
            else:
                logging.warning("Unable to determine the store name, project name and path from %s", req.url)
                raise falcon.HTTPNotFound()
        else:
            raise falcon.HTTPMethodNotAllowed(allowed_methods=["GET"])


def _last_modified(meta: Dict) -> date:
    t = meta.get("last_modified", None)
    timestamp = calendar.timegm(t) if t else 0
    return date.fromtimestamp(timestamp)
