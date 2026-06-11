from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aisikl.context import Context


class BaseClient:
    def __init__(self, context: Context) -> None:
        self.context = context

    def check_connection(self) -> None:
        pass

    def prepare_for_rpc(self) -> None:
        self.last_rpc_failed = False

    def logout(self) -> None:
        pass

    fake_time_msec: int | None = None

    last_rpc_failed = False
