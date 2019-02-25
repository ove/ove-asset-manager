import re
import tempfile
from typing import Callable

import falcon

from common.util import is_empty


def parse_filename(req: falcon.Request) -> str:
    if req.get_header('content-disposition'):
        filename = re.findall("filename=(.+)", req.get_header('content-disposition'))
        if is_empty(filename):
            raise falcon.HTTPInvalidHeader("No filename specified in header", 'content-disposition')

        filename = filename[0]
        filename = (filename.encode('ascii', errors='ignore').decode()).strip('\"').strip('\'').strip()
        if is_empty(filename):
            raise falcon.HTTPInvalidHeader("No valid filename specified in header", 'content-disposition')

        if filename == '.ovemeta':
            raise falcon.HTTPForbidden(title="Invalid filename", description="This is a reserved filename and is not allowed as an asset name")

        return filename
    else:
        raise falcon.HTTPBadRequest(title="Invalid filename", description="No filename specified - this should be in the content-disposition header")


def save_filename(save_fn: Callable, req: falcon.Request):
    with tempfile.NamedTemporaryFile() as cache:
        cache.write(req.stream.read())
        cache.flush()
        save_fn(upload_filename=cache.name)
