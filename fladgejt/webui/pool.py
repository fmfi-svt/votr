from functools import wraps
from typing import Any, TYPE_CHECKING, Unpack

if TYPE_CHECKING:
    from aisikl.app import Application
    from aisikl.context import Context
    from collections.abc import Awaitable, Callable


OPEN_APP_LIMIT = 10


def pooled_app[S, D, *A](
    original_method: Callable[[S, Unpack[A]], Awaitable[Application[D]]]
) ->                 Callable[[S, Unpack[A]], Awaitable[Application[D]]]:
    '''Decorator for methods that return an :class:`~aisikl.app.Application`.

    Generally, we don't want to open an application if we've already opened it.
    We want to store and reuse opened applications. But if an application
    doesn't make any request for about 15 minutes, WebUI closes it and any
    further requests will fail. So if we don't use an application for some
    time, we need to check if it's still open, and if not, reopen it.

    Worse, WebUI only allows you to have 10 open applications at once. If we
    already have that many, we need to close some to make space. But we
    shouldn't close the applications used by the current request.

    This decorator handles both of the above issues. ``original_method`` should
    accept only ``self`` and positional arguments, and use them to return an
    :class:`~aisikl.app.Application` instance. The decorated method will only
    call the original if there is no open application with the same arguments.
    And if we've reached the limit of open applications, it will close one, so
    that the original method can open a new application without an error.

    Args:
        original_method: The method to decorate.
    Returns:
        The decorated method.
    '''
    @wraps(original_method)
    async def wrapper(self: Any, *args: Unpack[A]) -> Application[D]:
        app_pool: Pool = self.app_pool
        open_apps: dict[object, Application[object]] = app_pool.open_apps
        active_keys: set[object] = app_pool.active_keys
        app_key = (original_method.__name__, args)

        if app_key in open_apps and not await open_apps[app_key].is_still_open():
            del open_apps[app_key]
            active_keys.discard(app_key)

        if app_key not in open_apps:
            await app_pool.reserve(1)
            open_apps[app_key] = await original_method(self, *args)

        active_keys.add(app_key)
        return open_apps[app_key]  # pyrefly: ignore [bad-return] # pyright: ignore [reportReturnType]

    return wrapper


class Pool:
    def __init__(self, context: Context) -> None:
        self.context = context
        self.open_apps: dict[object, Application[object]] = {}
        self.active_keys: set[object] = set()

    async def reserve(self, count: int) -> None:
        sorted_keys = sorted(
            self.open_apps,
            key=lambda k: self.open_apps[k].last_response_time)

        for key in sorted_keys:
            if len(self.open_apps) + count <= OPEN_APP_LIMIT:
                break
            if key in self.active_keys:
                continue

            await self.context.log('operation', 'Closing pooled application', key)
            app = self.open_apps.pop(key)
            if not await app.force_close():
                # force_close() can fail if the AIS server is still busy, e.g.
                # if an earlier Votr RPC timed out. The app still counts towards
                # OPEN_APP_LIMIT, but right now it's in an unusable state for
                # us. We can try again next time.
                for i in range(len(sorted_keys)):
                    new_key = ('_failed_to_close', key, i)
                    if new_key not in self.open_apps:
                        self.open_apps[new_key] = app
                        break

    async def prepare_for_rpc(self, last_rpc_failed: bool) -> None:
        self.active_keys = set()

        if last_rpc_failed and self.open_apps:
            await self.context.log('operation',
                'Closing all open apps because of previous RPC error')
            await self.reserve(OPEN_APP_LIMIT)
