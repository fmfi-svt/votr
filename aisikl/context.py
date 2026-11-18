import json
import sys
import time
from contextlib import AsyncExitStack, contextmanager
from http.cookiejar import CookieJar
from typing import TYPE_CHECKING, Any, Literal, TextIO, TypeIs, override
from urllib.parse import urljoin

import httpcore2
import httpx2
from bs4 import BeautifulSoup
from httpcore2._backends.auto import AutoBackend  # TODO: Replace with public import after https://github.com/pydantic/httpx2/issues/1131

from aisikl.exceptions import LoggedOutError, RESTServerError
from aisikl.typeutils import nn

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Generator, Iterable, Mapping, Sequence
    from http.cookiejar import Cookie


print_logs = False
"""Set this to True -- either by editing the source code, or by running
```python
import aisikl.context; aisikl.context.print_logs = True
```
to print all logs to stderr.
"""


class Context:
    """The common context for an AIS session. When one user opens multiple AIS
    applications, they share the same Context. It manages the HTTP cookie jar,
    performs HTTP requests and deals with logs.
    """

    def __init__(self, *, ais_url: str | None=None, rest_url: str | None=None, dns_overrides: dict[str, str] | None=None,
                 logger: Logger | None=None) -> None:
        self.ais_url = ais_url
        """The AIS server to connect to, e.g. ``"https://ais2.uniba.sk/"``."""
        self.rest_url = rest_url
        """The REST server to connect to."""
        self.dns_overrides = dns_overrides or {}
        """A map of hostname replacements. Given ``{K: V}``, when sending any
        https request to ``K``, the socket will ``connect()`` to ``V`` instead.
        The SNI name and Host header will still be ``K``.

        Mainly used in Votr Beta to optionally replace ``idp.uniba.sk`` with
        ``idp.test.uniba.sk``. These requests have to keep their original Host
        header to pass Andrvotr's Host check. SNI could technically have either
        value, because this server currently happens to have both SANs, but
        matching SNI = Host should be more polite and future-proof.
        """
        self.logger = logger or Logger()
        """Performs logging."""
        self.cookie_jar = _PickleableCookieJar()
        """Contains session cookies for outgoing HTTP requests."""
        self._pool: httpcore2.AsyncConnectionPool | None = None
        """The connection pool, if [`use_connection_pool`][] is active."""

    @contextmanager
    def use_connection_pool(
        self, pool: httpcore2.AsyncConnectionPool | None,
    ) -> Generator[None]:
        """Uses the given HTTP connection pool for the context manager's
        duration. By default, without ``use_connection_pool``, ``Context``
        creates a new TCP connection for each HTTP request.

        The purpose of this design is to allow using an effectively process-wide
        pool for efficiency, but not require it in scripts, notebooks and REPLs.

        If ``dns_overrides`` are enabled, ``use_connection_pool`` has no effect.
        """
        old, self._pool = self._pool, pool
        try:
            yield
        finally:
            self._pool = old

    async def request_http(
        self, *,
        method: str,
        url: str,
        data: Mapping[str, str] | None=None,
        headers: Mapping[str, str] | None=None,
    ) -> httpx2.Response:
        """Sends an HTTP request to an arbitrary absolute URL and returns the
        response. Reads and writes [`cookie_jar`][].

        ``request_http`` does not log the request, follow redirects, or check
        response HTTP status; the caller should take care of that.
        """
        async with AsyncExitStack() as stack:
            if self.dns_overrides:
                backend = _BackendWithDnsOverrides(self.dns_overrides)
                pool = await stack.enter_async_context(
                    httpcore2.AsyncConnectionPool(network_backend=backend))
            elif self._pool:
                pool = self._pool
            else:
                pool = await stack.enter_async_context(
                    httpcore2.AsyncConnectionPool())

            client = await stack.enter_async_context(httpx2.AsyncClient(
                transport=_TransportWithCustomPool(pool),
                # This relies on an undocumented detail: the behavior of
                # AsyncClient(cookies=...) changes depending on argument type.
                # Given `dict[str, str]` or `httpx2.Cookies`, it creates a copy.
                # Given `http.cookiejar.CookieJar` or a subclass, the jar won't
                # be copied, but modified in-place.
                cookies=self.cookie_jar,
            ))

            return await client.request(
                method=method, url=url, data=data, headers=headers,
                follow_redirects=False, timeout=None)

    async def request_ais(
        self, url: str, *,
        method: str="GET",
        data: Mapping[str, str] | None=None,
        headers: Mapping[str, str] | None=None,
        redirects: Literal["raise", "return", "follow"]="raise",
    ) -> httpx2.Response:
        """Sends a request to AIS and returns the response.

        ``url`` can be either absolute or relative to [`ais_url`][].
        """
        while True:
            await self.log("benchmark", "Begin AIS network request")
            await self.log("http", f"Requesting {method} {url.partition('?')[0]}", [url, data])

            url = urljoin(nn(self.ais_url), url)
            response = await self.request_http(
                method=method, url=url, data=data, headers=headers)

            await self._log_response(response)
            await self.log("benchmark", "End AIS network request")

            if response.has_redirect_location and redirects == "follow":
                next_request = nn(response.next_request)
                url = str(next_request.url)
                method = next_request.method
                if method == "GET": data = None
                headers = next_request.headers
                continue
                # Max redirects count is not implemented (not needed so far).
            else:
                break

        if response.has_redirect_location and redirects == "return":
            return response
        else:
            # httpx2.Response.raise_for_status() succeeds only on 2xx. Note this
            # is a difference from `requests`, which raises only on 4xx or 5xx.
            response.raise_for_status()
            return response

    async def parse_html(self, response: httpx2.Response) -> BeautifulSoup:
        await self.log("benchmark", "Begin HTML parsing")
        soup = BeautifulSoup(response.text, "lxml")
        await self.log("benchmark", "End HTML parsing")
        return soup

    async def request_json(self, url: str, **data: str) -> Any:
        """Sends a request to REST API and parses the response as JSON.

        Args:
            url: The URL, either absolute or relative to [`rest_url`][].
            **data: POST form fields.

        Returns:
            A dictionary.
        """
        await self.log("benchmark", "Begin REST network request")
        await self.log("http", f"Requesting POST {url.partition('?')[0]}", [url, data])

        url = urljoin(nn(self.rest_url), url)
        response = await self.request_http(method="POST", url=url, data=data)

        await self._log_response(response)
        await self.log("benchmark", "End REST network request")

        if response.has_redirect_location:
            raise LoggedOutError("REST login expired.")
        response.raise_for_status()
        response = json.loads(response.text)

        if response["status"] != "OK":
            raise RESTServerError(
                f"Status: {response["status"]} Error: {response["error"]}")

        await self.log("http", "Parsed JSON data")
        return response["response"]

    async def _log_response(self, response: httpx2.Response) -> None:
        log_data = {
            "status_code": response.status_code,
            "reason_phrase": response.reason_phrase,
            "headers": [
                [k, v] for k, v in response.headers.multi_items()
                if k.lower() in { "aisauth", "content-type", "location" }
            ],
        }
        if response.has_redirect_location:
            pass
        elif response.headers.get("content-type", "").startswith("text"):
            log_data["body"] = response.text
        else:
            # We could log base64 content here... it would simplify testutils.py
            # slightly... But '/ais/apps/student/sk/main.js' is freaking huge,
            # so let's not.
            pass
        await self.log("http", "Received response", log_data)

    async def log(self, type: str, message: str, data: object=None) -> None:
        """Logs a message.

        Args:
            type: String used to group similar messages together.
            message: The log message. Should be a single line.
            data: A JSON-serializable object containing more details.
        """
        await self.logger.log(type, message, data)


class Logger:
    """Logs messages to various destinations."""

    log_file: TextIO | None = None
    """An open file to write log entries to. Votrfront sets it to a per-session
    log file on every request. The value is not preserved between requests."""

    send_log: Callable[[float, str, str, object], Awaitable[None]] | None = None
    """A function that will be called with (timestamp, type, message, data) for
    every log entry. Votrfront uses it to send JSON logs to the client during a
    RPC request. The value is not preserved between requests."""

    @override
    def __getstate__(self) -> dict[object, object]:
        return {}

    async def log(self, type: str, message: str, data: object=None) -> None:
        timestamp = time.time()

        # 'benchmark' is excluded from log files. It's too verbose.
        if type != "benchmark":
            if self.log_file:
                json_entry = json.dumps(
                    [timestamp, type, message, data], ensure_ascii=False)
                self.log_file.write(json_entry + "\n")

            _log_to_ipython(type, message, data)

            if print_logs:
                text = f"\033[1;36m{type} \033[1;33m{message}\033[0m"
                if data is not None:
                    text = f"{text} {json.dumps(data, ensure_ascii=False)}"
                print(text, file=sys.stderr)

        if self.send_log:
            await self.send_log(timestamp, type, message, data)
    log.__doc__ = Context.log.__doc__


# Miscellaneous notes on `httpx`:
#
# PICKLING:
#   The httpx API is unfortunately very obstinate about pickling. We want to
#   store cookies in our `Context` and save them in Votr sessions, but this is
#   needlessly difficult. `httpx2.Client` represents both a connection pool and
#   a cookie jar in one object. Constructing and wiring the underlying pool and
#   jar objects manually is nontrivial - see `_TransportWithCustomPool`. And the
#   default cookie jar is not pickleable, anyway - see `_PickleableCookieJar`.
#   *shakes fist*
#
# NURSERIES:
#   JFYI: The reason httpx/httpcore's API does not need a `trio.open_nursery()`
#   block is that it never does any background work. All pool maintenance is
#   done only when it prepares to send a request. At that time, the pool scans
#   all connections, and closes: 1. sockets that were idle for longer than
#   `keepalive_expiry`, 2. sockets where the server sent us an EOF. (JFYI: it
#   detects EOF indirectly by checking if it's idle and `is_socket_readable`,
#   because EOF also counts as readable, and the pool assumes the server won't
#   send anything else.) Notice that this arrangement means sockets could stay
#   open for arbitrarily long - `keepalive_expiry` is not applied immediately.
#   But in practice, with our usage patterns, socket/fd exhaustion shouldn't be
#   a problem.


class _BackendWithDnsOverrides(AutoBackend):
    """A httpcore network backend that overrides the DNS resolution (i.e. the
    socket connect() address). The original hostname is still used in the Host
    header and SNI name. Used to implement [`Context.dns_overrides`][].
    """

    def __init__(self, dns_overrides: dict[str, str]):
        super().__init__()
        self.dns_overrides = dns_overrides

    @override
    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: float | None = None,
        local_address: str | None = None,
        socket_options: Iterable[httpcore2.SOCKET_OPTION] | None = None,
    ) -> httpcore2.AsyncNetworkStream:
        return await super().connect_tcp(
            host=self.dns_overrides.get(host, host), port=port, timeout=timeout,
            local_address=local_address, socket_options=socket_options)


class _TransportWithCustomPool(httpx2.AsyncBaseTransport):
    """A httpx2 transport that uses the specified httpcore2 pool object."""

    def __init__(self, pool: httpcore2.AsyncConnectionPool):
        super().__init__()
        self._pool = pool

    # Borrow the `handle_async_request` definition from `AsyncHTTPTransport`.
    # It mainly handles translation of `httpx2.Request` to `httpcore2.Request`,
    # and uses `self._pool` to send it.
    #
    # This relies on a private undocumented implementation detail: The method 1)
    # uses an attribute named specifically `self._pool`, and 2) doesn't need any
    # other attributes on `self`.
    handle_async_request = override(
        httpx2.AsyncHTTPTransport.handle_async_request)

    # `__aenter__`, `__aexit__`, `aclose` are intentionally not overridden, i.e.
    # they keep their no-op definitions from `AsyncBaseTransport`. This class
    # doesn't own and doesn't close `self._pool`, unlike `AsyncHTTPTransport`.


class _PickleableCookieJar(CookieJar):
    """A [`CookieJar`][] subclass that can be pickled.

    See also <https://github.com/python/cpython/issues/112144>.
    """

    @override
    def __getstate__(self) -> list[Cookie]:
        return list(self)

    def __setstate__(self, state: list[Cookie]) -> None:
        self.__init__()
        for cookie in state:
            self.set_cookie(cookie)


def _is_dict(data: object) -> TypeIs[Mapping[object, object]]:
    return isinstance(data, dict)


def _is_list_or_tuple(data: object) -> TypeIs[Sequence[object]]:
    return isinstance(data, (list, tuple))


def _repr(obj: object, obj_name: object = None, level: int = 0) -> str:
    if obj_name == "body" and isinstance(obj, str) and "\n" in obj:
        return f'"""\n{obj}\n"""'
    if not (_is_dict(obj) or _is_list_or_tuple(obj)):
        return json.dumps(obj, ensure_ascii=False)
    children = obj.values() if _is_dict(obj) else obj
    if all(not (_is_dict(c) or _is_list_or_tuple(c)) for c in children):
        return json.dumps(obj, ensure_ascii=False)  # also handles empty {} / []
    pad = "  " * level
    inner = "  " * (level + 1)
    if _is_dict(obj):
        body = [
            f"{inner}{json.dumps(str(k))}: {_repr(v, k, level + 1)}"
            for k, v in obj.items()
        ]
        return "{\n" + ",\n".join(body) + "\n" + pad + "}"
    else:
        body = [inner + _repr(v, None, level + 1) for v in obj]
        return "[\n" + ",\n".join(body) + "\n" + pad + "]"


def repr_log_data(data: object) -> str:
    """Returns a JSON-like human-readable representation of ``data``. Intended
    to make Votr log entries in developer tools easier to read.

    Lists and dicts are printed compactly if all children are primitives,
    otherwise indented. The dict key "body" (presumably a HTTP response body) is
    printed literally, without string escaping.
    """
    return _repr(data)


try:
    __IPYTHON__  # pyrefly: ignore [unknown-name] # pyright: ignore [reportUndefinedVariable, reportUnusedExpression]
except NameError:

    def _log_to_ipython(type: str, message: str, data: object) -> None:
        pass
else:
    from IPython.display import display  # pyrefly: ignore [missing-import] # pyright: ignore [reportMissingImports, reportUnknownVariableType]
    from markupsafe import Markup

    def _log_to_ipython(type: str, message: str, data: object) -> None:
        html = Markup('<span style="background:#FF8"><b>{}</b> {}</span>').format(type, message)
        if data is not None:
            html = Markup("<details><summary>{}</summary><pre>{}</pre></details>").format(html, repr_log_data(data))
        else:
            # Wrap in <div> to make Jupyter's margin-bottom CSS more consistent.
            html = Markup("<div>{}</div>").format(html)
        display({"text/plain": f"<{type}> {message}", "text/html": str(html)}, raw=True)
