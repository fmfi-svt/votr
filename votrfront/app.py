import logging
from anycorn.middleware import ProxyFixMiddleware
from contextlib import asynccontextmanager
from http import HTTPStatus
from markupsafe import Markup
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import Response, HTMLResponse
from starlette.routing import BaseRoute, Mount
from starlette.staticfiles import StaticFiles
from votrfront import login, front, rpc, report
from votrfront.base import ROOT_PATH, Settings, VotrState
import trio
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlencode

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator
    from starlette.types import ASGIApp, Message, Receive, Scope, Send

pylogger = logging.getLogger(__name__)


EXCEPTION_PAGE = Markup("""\
<!doctype html>
<html lang=en>
<title>%(status_code)s - %(phrase)s</title>
<style>
body { margin: 1em; margin-top: 30vh; font-family: sans-serif; text-align: center; }
a { color: darkred; }
</style>
<h1>%(status_code)s - %(phrase)s</h1>
<p>%(other_detail)s</p>
<p><a href="%(root_url)s">Back to main page</a></p>
""")


async def handle_http_exception(request: Request, exc: Exception) -> Response:
    assert isinstance(exc, HTTPException)

    # Special case copied from
    # starlette.middleware.exceptions.ExceptionMiddleware.http_exception().
    if exc.status_code in (204, 304):
        return Response(status_code=exc.status_code, headers=exc.headers)

    try:
        phrase = HTTPStatus(exc.status_code).phrase
    except Exception:
        phrase = "Unknown Status"

    body = EXCEPTION_PAGE % dict(
        status_code=exc.status_code,
        phrase=phrase,
        other_detail=(exc.detail if exc.detail != phrase else ""),
        root_url=(request.state["settings"].root_url or request.base_url),
    )

    return HTMLResponse(body, status_code=exc.status_code, headers=exc.headers)


class SessionCookieMiddleware:
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        self.app = app
        self.settings = settings

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        cookie_prefix = '__Host-' if request.url.is_secure else ''
        cookie_name = f'{cookie_prefix}{self.settings.instance_id}_csession'
        cookie_str = request.cookies.get(cookie_name)
        try:
            qs = parse_qs(cookie_str or '', keep_blank_values=True)
            cookie_dict = {k: v[0] for k, v in qs.items()}
        except Exception:
            cookie_dict: dict[str, str] = {}
        cookie_dict_copy = cookie_dict.copy()
        scope["state"]["votr_cookie_value"] = cookie_dict

        async def new_send(message: Message) -> None:
            new_cookie_dict = scope["state"]["votr_cookie_value"]
            if message["type"] == "http.response.start" and (
                new_cookie_dict is not cookie_dict
                or new_cookie_dict != cookie_dict_copy
            ):
                fake_response = Response()
                fake_response.set_cookie(
                    cookie_name,
                    urlencode(new_cookie_dict) if new_cookie_dict else "",
                    max_age=(None if new_cookie_dict else 0),
                    expires=(None if new_cookie_dict else 0),
                    secure=request.url.is_secure, httponly=True, samesite="lax")
                assert fake_response.raw_headers[-1][0] == b"set-cookie"
                message["headers"] = [
                    *message["headers"],
                    fake_response.raw_headers[-1],
                ]

            await send(message)

        await self.app(scope, receive, new_send)


class CheckRootUrlMiddleware:
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        self.app = app
        self.settings = settings

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] == "http" and self.settings.root_url:
            request = Request(scope)
            if str(request.base_url) != self.settings.root_url:
                pylogger.warning(
                    "CheckRootUrlMiddleware: expected %r, got %r",
                    self.settings.root_url, str(request.base_url))
                exc = HTTPException(421)
                response = await handle_http_exception(request, exc)
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)


# This is a ridiculous timeout, but some AIS requests are really slow. The
# primary intended mechanism for handling them is that rpc.py checks for client
# disconnects. So if a user wants to wait, they can wait, and if not, they
# don't. This timeout is a mostly theoretical last line of defense, because it
# seems reasonable to have one.
REQUEST_TIMEOUT = 3 * 60


class RequestTimeoutMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        with trio.fail_after(REQUEST_TIMEOUT):
            await self.app(scope, receive, send)

        # What happens if the timeout expires:
        # 1. The currently running Trio primitive function raises Cancelled.
        # 2. Cancelled bubbles up to here.
        # 3. ExceptionMiddleware doesn't catch it, because it's a BaseException
        #    and also because our exception_handlers only have HTTPException.
        # 4. fail_after() catches this exact Cancelled and raises TooSlowError.
        # 5. ServerErrorMiddleware catches the TooSlowError.
        # 6. If "http.response.start" was already sent, ServerErrorMiddleware
        #    does nothing and just reraises the TooSlowError. Else, it sends a
        #    plain 500 "Internal Server Error" page, and reraises it anyway.
        # 7. Anycorn catches and logs the TooSlowError.
        # 8. If the ASGI response is unfinished (i.e. "http.response.start" was
        #    already sent, but a "http.response.body" with more_body=False was
        #    not), Anycorn focibly closes the HTTP stream (StreamClosed without
        #    EndBody). Our reverse proxy preserves this. HTTP clients will
        #    surface this as a network error (e.g. curl 18, XHR onerror).
        #
        # This is overall reasonable:
        # - A specific error message might be nicer, but isn't worth the effort.
        # - Letting unfinished responses be legibly unfinished is good.
        #   So let's not e.g. artificially send a final more_body=False chunk.
        # - Timeout logs are not too useful on their own, but they could
        #   sometimes help with debugging.


def build_app(
    *,
    settings: Settings | None = None,
    debug: bool = False,
    static: bool = False,
    proxy_fix: bool = False,
) -> Starlette:
    if settings is None:
        import votrfront.local_settings as settings

    routes: list[BaseRoute] = [
        *login.routes,
        *front.routes,
        *rpc.routes,
        *report.routes,
    ]
    if static:
        static_dir = ROOT_PATH / "votrfront/static"
        routes.append(Mount("/static", app=StaticFiles(directory=static_dir)))

    middleware = [
        Middleware(SessionCookieMiddleware, settings),
        Middleware(CheckRootUrlMiddleware, settings),
        Middleware(RequestTimeoutMiddleware),
    ]
    if proxy_fix:
        # mode="modern" has bad fallback behavior and doesn't parse quotes.
        middleware.insert(
            0, Middleware(ProxyFixMiddleware, mode="legacy", trusted_hops=1))

    @asynccontextmanager
    async def lifespan(_app: Starlette) -> AsyncGenerator[VotrState]:
        yield VotrState(
            settings=settings,
            saml_settings=login.build_saml_settings(settings),
        )

    return Starlette(
        debug=debug,
        routes=routes,
        middleware=middleware,
        exception_handlers={HTTPException: handle_http_exception},
        lifespan=lifespan,
        max_body_size=16 * 1024 * 1024,
    )
