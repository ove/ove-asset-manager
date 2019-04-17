import json
import urllib
from typing import Dict, Any, List, Union

import falcon
import urllib3

from common.util import append_slash


class BackendClient:
    def __init__(self, backend_url: str):
        self.backend_url = append_slash(backend_url)
        self._http = urllib3.PoolManager()

    def head(self, api_url: str, headers: Dict = None) -> bool:
        response = self._http.request(method="HEAD", url=self.backend_url + api_url, headers=_fix_headers(headers))
        return 200 <= response.status < 300

    def get(self, api_url: str, params: Dict = None, headers: Dict = None) -> Union[Dict, List, None]:
        return self.request(method="GET", api_url=api_url, params=params, headers=headers)

    def post(self, api_url: str, data: Dict = None, params: Dict = None, headers: Dict = None) -> Union[Dict, List, None]:
        return self.request(method="POST", api_url=api_url, data=data, params=params, headers=headers)

    def put(self, api_url: str, data: Dict = None, params: Dict = None, headers: Dict = None) -> Union[Dict, List, None]:
        return self.request(method="PUT", api_url=api_url, data=data, params=params, headers=headers)

    def delete(self, api_url: str, data: Dict = None, params: Dict = None, headers: Dict = None) -> Union[Dict, List, None]:
        return self.request(method="DELETE", api_url=api_url, data=data, params=params, headers=headers)

    def request(self, method: str, api_url: str, data: Dict = None, params: Dict = None, headers: Dict = None) -> Union[Dict, List, None]:
        response = self._http.request(method=method, url=_url(self.backend_url, api_url, params), headers=_fix_headers(headers), timeout=10.0,
                                      body=json.dumps(data).encode('utf-8') if data is not None else None)
        if 200 <= response.status < 300:
            result = response.data
            if result is not None:
                return json.loads(result.decode('utf-8'))
            else:
                return None
        else:
            result = response.data
            e = json.loads(result.decode('utf-8')) if result is not None else {}
            raise falcon.HTTPInternalServerError(title=e.get("title", "Error"),
                                                 description=e.get("description", "Error while calling '{}'".format(api_url)))

    def upload(self, api_url: str, stream: Any, method: str = "POST", params: Dict = None, headers: Dict = None) -> Union[Dict, List, None]:
        response = self._http.request(method=method, url=_url(self.backend_url, api_url, params), headers=headers, body=stream.read())
        if 200 <= response.status < 300:
            result = response.data
            if result is not None:
                return json.loads(result.decode('utf-8'))
            else:
                return None
        else:
            result = response.data
            e = json.loads(result.decode('utf-8')) if result is not None else {}
            raise falcon.HTTPInternalServerError(title=e.get("title", "Error"),
                                                 description=e.get("description", "Error while calling '{}'".format(api_url)))


def _fix_headers(headers: Dict = None) -> Dict:
    if headers is None:
        return {'Content-Type': 'application/json'}
    else:
        headers['Content-Type'] = 'application/json'
        return headers


def _url(backend_url: str, api_url: str, params: Dict = None) -> str:
    url = backend_url + urllib.parse.quote(api_url)
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    return url
