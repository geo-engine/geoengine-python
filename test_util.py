import urllib3
from json import dumps
from unittest.mock import patch


class UrllibMocker:
    def __enter__(self):
        self._matchers = []
        self._mock_context = patch("openapi_client.rest.urllib3.PoolManager.request")
        mock_request = self._mock_context.__enter__()
        mock_request.side_effect = self._handle_request
        return self

    def _handle_request(self, method, url, *args, **kwargs):
        for matcher in self._matchers:
            if matcher["method"] == method and matcher["url"].startswith(url) and (
                    matcher["requestHeaders"] is None or
                    matcher["requestHeaders"].items() <= kwargs["headers"].items()):
                return urllib3.response.HTTPResponse(
                    status=200,
                    reason="OK",
                    body=matcher["body"]
                )
        raise KeyError(f'No handler found for {method} {url}')

    def register_uri(self, method, url, request_headers=None, json=None):
        matcher = {
            "method": method,
            "url": url,
            "requestHeaders": request_headers,
            "body": b''
        }
        if json is not None:
            matcher["body"] = dumps(json).encode('utf-8')

        self._matchers.append(matcher)

    def get(self, url, **kwargs):
        self.register_uri("GET", url, **kwargs)

    def post(self, url, **kwargs):
        self.register_uri("POST", url, **kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._mock_context.__exit__(exc_type, exc_val, exc_tb)
