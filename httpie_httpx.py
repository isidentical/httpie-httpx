from contextlib import ExitStack
from http import HTTPStatus

from httpcore import ConnectionPool, Request
from httpie.plugins import TransportPlugin
from httpx._config import Timeout, create_ssl_context
from requests.adapters import HTTPAdapter
from urllib3.response import HTTPResponse
from urllib3.util import parse_url

HTTP_MAPPING = {
    "HTTP/0.9": 9,
    "HTTP/1.0": 10,
    "HTTP/1.1": 11,
    "HTTP/2": 20,
}


class FileLike:
    def __init__(self, bytestream):
        self._bytestream = iter(bytestream)
        self.closed = False

    def read(self, amt: int = None):
        return next(self._bytestream, b"")

    def close(self):
        self._bytestream.close()
        self.closed = True


class StreamLike:
    def __init__(self, filelike):
        self._filelike = filelike

    def __iter__(self):
        chunk = self._filelike.read(4096)
        while chunk:
            yield chunk
            chunk = self._filelike.read(4096)

    def close():
        pass


class HTTPCoreAdapter(HTTPAdapter):
    def __init__(self):
        self._contexts = ExitStack()

    def send(
        self,
        request,
        stream=False,
        timeout=None,
        verify=True,
        cert=None,
        proxies=None,
    ):
        file_like = hasattr(request.body, "read")
        if file_like:
            content = StreamLike(request.body)
        elif isinstance(request.body, str):
            content = request.body.encode("utf-8")
        else:
            content = request.body

        headers = request.headers.copy()
        if "host" not in headers:
            headers["host"] = parse_url(request.url).netloc

        extensions = {}
        if timeout:
            extensions["timeout"] = Timeout(timeout).as_dict()

        httpcore_request = Request(
            method=request.method,
            url=request.url,
            headers=headers,
            content=content,
            extensions=extensions,
        )

        pool = self._contexts.push(
            ConnectionPool(
                http1=True,
                http2=True,
                ssl_context=create_ssl_context(
                    cert=cert, verify=verify, http2=True
                ),
            )
        )
        response = pool.handle_request(httpcore_request)

        http_version = response.extensions["http_version"].decode()
        reason_phrase = response.extensions.get("reason_phrase")

        # HTTP/2 does not include a reason phrase, so for
        # the sake of simplicity I just get it from the default store.
        if reason_phrase:
            reason_phrase = reason_phrase.decode("ascii")
        else:
            reason_phrase = HTTPStatus(response.status).phrase

        urllib3_response = HTTPResponse(
            body=FileLike(response.stream),
            headers=[
                (key.decode("ascii"), val.decode("ascii"))
                for key, val in response.headers
            ],
            status=response.status,
            reason=reason_phrase,
            version=HTTP_MAPPING[http_version],
            preload_content=False,
        )
        return self.build_response(request, urllib3_response)

    def close(self):
        self._contexts.close()


class HTTPXTransport(TransportPlugin):
    prefix = "https://"

    def get_adapter(self):
        return HTTPCoreAdapter()
