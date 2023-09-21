import urllib3
from json import dumps, loads
from unittest.mock import patch
from urllib.parse import urlparse


class UrllibMocker:
    STATUS_CODE_REASON_MAP = {
        200: "OK",
        400: "Bad Request",
        404: "Not Found"
    }

    def __enter__(self):
        self._matchers = []
        self.request_history = []
        self._mock_context = patch("openapi_client.rest.urllib3.PoolManager.request")
        mock_request = self._mock_context.__enter__()
        mock_request.side_effect = self._handle_request
        return self

    def _handle_request(self, method, url, *args, **kwargs):
        self.request_history.append({
            "method": method,
            "url": url,
            **kwargs
        })
        for matcher in self._matchers:
            if matcher["method"] == method and matcher["path"] == urlparse(url).path and (
                matcher["requestHeaders"] is None or matcher["requestHeaders"].items() <= kwargs["headers"].items()
            ) and (
                    matcher["expectedRequestBody"] is None or matcher["expectedRequestBody"] == loads(kwargs["body"])):
                return urllib3.response.HTTPResponse(
                    status=matcher["statusCode"],
                    reason=UrllibMocker.STATUS_CODE_REASON_MAP[matcher["statusCode"]],
                    body=matcher["body"]
                )
        raise KeyError(f'No handler found for {method} {url}')

    def register_uri(self, method, url, request_headers=None, expected_request_body=None, status_code=200, json=None):
        matcher = {
            "method": method,
            "path": urlparse(url).path,
            "requestHeaders": request_headers,
            "expectedRequestBody": expected_request_body,
            "statusCode": status_code,
            "body": b''
        }
        if json is not None:
            matcher["body"] = dumps(json).encode('utf-8')

        self._matchers.append(matcher)

    def get(self, url, **kwargs):
        self.register_uri("GET", url, **kwargs)

    def post(self, url, **kwargs):
        self.register_uri("POST", url, **kwargs)

    def delete(self, url, **kwargs):
        self.register_uri("DELETE", url, **kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._mock_context.__exit__(exc_type, exc_val, exc_tb)
