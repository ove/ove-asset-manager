import json
import urllib
from typing import Dict, Any, List, Union

import falcon
import urllib3
from urllib3 import HTTPResponse

from common.consts import FIELD_AUTH_TOKEN
from common.util import append_slash


class BackendClient:
    def __init__(self, backend_url: str):
        self.backend_url = append_slash(backend_url)
        self._http = urllib3.PoolManager(headers={"Content-Type": "application/json", "Keep-Alive": "timeout=5, max=1000"})

    def head(self, api_url: str, auth_token: Union[str, None], headers: Dict = None) -> bool:
        response = self._http.request(method="HEAD", url=self.backend_url + api_url, headers=_fix_headers(auth_token=auth_token, headers=headers))
        return 200 <= response.status < 300

    def get(self, api_url: str, auth_token: Union[str, None], params: Dict = None, headers: Dict = None) -> Union[Dict, List, None]:
        return self.request(method="GET", api_url=api_url, params=params, headers=headers, auth_token=auth_token)

    def post(self, api_url: str, auth_token: Union[str, None], data: Dict = None, params: Dict = None, headers: Dict = None) -> Union[Dict, List, None]:
        return self.request(method="POST", api_url=api_url, data=data, params=params, headers=headers, auth_token=auth_token)

    def patch(self, api_url: str, auth_token: Union[str, None], data: Dict = None, params: Dict = None, headers: Dict = None) -> Union[Dict, List, None]:
        return self.request(method="PATCH", api_url=api_url, data=data, params=params, headers=headers, auth_token=auth_token)

    def put(self, api_url: str, auth_token: Union[str, None], data: Dict = None, params: Dict = None, headers: Dict = None) -> Union[Dict, List, None]:
        return self.request(method="PUT", api_url=api_url, data=data, params=params, headers=headers, auth_token=auth_token)

    def delete(self, api_url: str, auth_token: Union[str, None], data: Dict = None, params: Dict = None, headers: Dict = None) -> Union[Dict, List, None]:
        return self.request(method="DELETE", api_url=api_url, data=data, params=params, headers=headers, auth_token=auth_token)

    def request(self, method: str, api_url: str, auth_token: Union[str, None], data: Dict = None, params: Dict = None, headers: Dict = None) -> Union[Dict, List, None]:
        response = self._http.request(method=method, url=_url(self.backend_url, api_url, params), timeout=60.0,
                                      headers=_fix_headers(auth_token=auth_token, headers=headers),
                                      body=json.dumps(data).encode("utf-8") if data is not None else None)
        return _process_response(api_url=api_url, response=response)

    def upload(self, api_url: str, auth_token: Union[str, None], stream: Any, method: str = "POST", params: Dict = None, headers: Dict = None) -> Union[Dict, List, None]:
        response = self._http.request(method=method, url=_url(self.backend_url, api_url, params), body=stream.read(),
                                      headers=_fix_headers(auth_token=auth_token, headers=headers, content_type="application/octet-stream"))
        return _process_response(api_url=api_url, response=response)


def _process_response(api_url: str, response: HTTPResponse) -> Union[Dict, List, None]:
    result = response.data
    if 200 <= response.status < 300:
        return json.loads(result.decode("utf-8")) if result is not None else None
    else:
        e = json.loads(result.decode("utf-8")) if result is not None else {}
        if response.status == 401:
            raise falcon.HTTPUnauthorized(title=e.get("title", "Error"), description=e.get("description", "Error while calling '{}'".format(api_url)))
        else:
            raise falcon.HTTPInternalServerError(title=e.get("title", "Error"), description=e.get("description", "Error while calling '{}'".format(api_url)))


def _fix_headers(auth_token: Union[str, None], headers: Dict = None, content_type: str = "application/json") -> Dict:
    if headers is None:
        headers = {}

    headers["Content-Type"] = content_type
    headers["Keep-Alive"] = "timeout=5, max=1000"
    if auth_token:
        headers[FIELD_AUTH_TOKEN] = auth_token

    return headers


def _url(backend_url: str, api_url: str, params: Dict = None) -> str:
    url = backend_url + urllib.parse.quote(api_url)
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    return url
