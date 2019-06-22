import tempfile
import urllib
from typing import Callable

import falcon

from common.util import is_empty_str


def unquote_filename(filename: str) -> str:
    if not is_empty_str(filename):
        filename = urllib.parse.quote_plus(filename)
        if is_empty_str(filename):
            raise falcon.HTTPBadRequest(title="Invalid filename", description="No valid filename specified in the query param")

        filename = filename.encode("ascii", errors="ignore").decode().strip('\"').strip('\'').strip()
        if is_empty_str(filename):
            raise falcon.HTTPBadRequest(title="Invalid filename", description="No valid filename specified in the query param")

        if filename == '.ovemeta':
            raise falcon.HTTPForbidden(title="Invalid filename", description="This is a reserved filename and is not allowed as an asset name")

        return filename
    else:
        raise falcon.HTTPBadRequest(title="Invalid filename", description="No filename specified in the query param")


def save_filename(save_fn: Callable, req: falcon.Request):
    with tempfile.NamedTemporaryFile() as cache:
        cache.write(req.stream.read(req.content_length or 0))
        cache.flush()
        save_fn(upload_filename=cache.name)
