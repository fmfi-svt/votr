# pyright: reportPrivateUsage=none

from aisikl.exceptions import AISBehaviorError, AISParseError
from aisikl.typeutils import ct, ct_none
from dataclasses import dataclass, field
from enum import Enum
import time
from typing import cast, override, Self, TYPE_CHECKING
from warnings import warn
import urllib.parse

if TYPE_CHECKING:
    from aisikl.app import Application
    from aisikl.dialog import Dialog
    from httpx2 import Response


@dataclass
class Operation:
    """Record of a "big" action done by AIS that isn't handled automatically
    and requires some reaction, such as:

    - Opening a new application or browser window
    - Showing a message box or another modal dialog
    - Opening and closing dialogs

    Various aisikl functions, e.g. ``Button.click()``, have a ``return_ops``
    argument:

    - If you expect something to happen, use ``return_ops=True`` to enable
      "operation collecting mode". It will return an :class:`Operations` list.
      You then have to check if the operations are what you expected, and deal
      with them, usually by calling ``perform()``. The returned list can be
      empty if nothing happened.

    - Otherwise (without ``return_ops=True``), it means you don't expect
      anything to happen. If something happens anyway, an error is raised. The
      function returns an empty :class:`Operations` list.

    Example::

        # If this shows a message box, an error is raised.
        await app.d.someInnocentButton.click()

        # This button should open a dialog. If it does anything else, or
        # nothing, an error is raised.
        ops = await.d.newDialogOpeningButton.click()
        await ops.expect_one(OpenDialogOp).perform()
    """

    app: Application[object] = field(repr=False, kw_only=True)
    handled: bool = field(default=True, init=False, repr=False)

    def _arm_warning(self) -> None:
        self.handled = False

    def acknowledge(self) -> Self:
        """Marks the operation as dealt with.

        As a developer aid, operation objects print a warning if you forget to
        handle them. You can use ``acknowledge()`` to disable this warning,
        expressing that you abstained from calling ``perform()`` intentionally
        and not because you forgot. One such case is if you raise some error
        before the ``perform()`` call.
        """
        self.handled = True
        return self

    def __del__(self) -> None:
        if not self.handled:
            warn(f"Unhandled operation {self!r}", stacklevel=2, source=self)


@dataclass
class MessageBoxOp(Operation):
    """A message box.

    You don't have to ``perform()`` or ``acknowledge()`` this operation type.

    Message boxes matching :attr:`aisikl.app.Application.ignored_messages` are
    ignored: they won't appear in :class:`Operations`, and won't trigger
    unexpected operation errors with ``return_ops=False``.
    """

    message: str
    title: str
    image: str
    detail: str

    @override
    def _arm_warning(self) -> None:
        pass


@dataclass
class ConfirmBoxOp(Operation):
    """Blocking modal dialog with multiple buttons. Handle with ``reply()``."""

    message: str
    title: str
    image: str
    buttons: int
    check: int
    check_box_label: str
    detail: str
    default_button: int

    class Option(Enum):
        YES_TO_ALL = 4
        YES = 2
        OK = 1
        CANCEL = -1
        NO = -2
        NO_TO_ALL = -4

    async def reply(
        self, option: Option, *, return_ops: bool = False
    ) -> Operations:
        self.handled = True
        await self.app.ctx.log(
            'operation', f'Selecting button {option.value} in confirm box')
        return await self.app._send_namevalue_request(
            'confirmResult', option.value, return_ops=return_ops)


@dataclass
class CalendarBoxOp(Operation):
    """Never seen yet. Types are guesses. perform() not yet implemented."""

    for_control_of_parent: str | None
    time_ms: int
    min_date_ms: int
    max_date_ms: int


@dataclass
class FileUploadOp(Operation):
    """Never seen yet. Types are guesses. perform() not yet implemented."""

    upload_file_local_name: str
    title: str


@dataclass
class FileXUploadOp(Operation):
    """Never seen yet. Types are guesses. perform() not yet implemented."""

    local_dir: str
    title: str
    filter: str
    init_dir: str
    multi_select: bool
    all_files_max_sum_size: int
    one_file_max_size: int


@dataclass
class AbortBoxOp(Operation):
    message: str
    title: str | None = None

    async def perform(self, *, return_ops: bool = False) -> Operations:
        self.handled = True
        await self.app.ctx.log('operation', 'Waiting for abort box')
        return await self.app._send_namevalue_request(
            'confirmResult', -1, return_ops=return_ops)


@dataclass
class EditDocOp(Operation):
    """Never seen yet. Types are guesses. perform() not yet implemented."""

    office_file_name: str


@dataclass
class ShellExecOp(Operation):
    content_type: str
    file_name: str
    new_window_name: str
    width: int
    height: int

    async def download(self) -> Response:
        """Downloads a file. Then sends a request to AIS saying that the
        shellExec was executed.

        This method only supports the common use of shellExec -- downloading
        files. Technically, shellExec can also run custom JavaScript code. If
        you need that, handle it manually and call :meth:`send_result`
        afterwards.
        """
        self.handled = True

        if self.content_type == 'webui/execCustomFunction':
            raise AISParseError("webui/execCustomFunction is not supported")

        file_name = self.file_name.rpartition('/')[2]
        url = (
            f'/ais/files/{urllib.parse.quote(file_name)}'
            f'?appId={self.app.app_id}&contentType={self.content_type}'
            f'&antiCache={time.time()}&file={urllib.parse.quote(file_name)}')

        await self.app.ctx.log('operation', f'Downloading "{file_name}"')

        response = await self.app.ctx.request_ais(url)

        await self.send_result('', return_ops=False)

        return response

    async def send_result(
        self, shell_exec_result: str, *, return_ops: bool = False
    ) -> Operations:
        """Informs AIS that a shellExec operation was executed.

        Args:
            shell_exec_result: The string value of ``shellExecResult``.
        """
        self.handled = True
        return await self.app._send_namevalue_request(
            'shellExecResult', shell_exec_result, return_ops=return_ops)


@dataclass
class ShowHelpOp(Operation):
    """Opens ``url`` in a new window. Never actually seen yet.

    There is no ``perform()``. Do something appropriate with the given ``url``
    and call ``acknowledge()``.
    """

    url: str


@dataclass
class StartAppOp(Operation):
    url: str
    params: str

    async def perform[D](
        self,
        *,
        ignored_messages: list[str] | None = None,
        hint: type[D] | None = None,
    ) -> tuple[Application[D], Operations]:
        self.handled = True

        from aisikl.app import Application  # Cyclic dependency :(

        url = f'/ais/servlets/WebUIServlet?appClassName={self.url}{self.params}&antiCache={time.time()}'
        return await Application[D].open(self.app.ctx, url, ignored_messages)


@dataclass
class ServerCloseApplicationOp(Operation):
    """Usually (in practice, always) occurs together with CloseApplicationOp.
    Its original meaning is to enable the wasClosedOnServer flag, which tells
    the client that it shouldn't send a WebUIKillEvent during cleanup. Votr does
    not implement it exactly. Instead, CloseApplicationOp.perform() never sends
    WebUIKillEvent, and Application.force_close() always sends WebUIKillEvent,
    whether a ServerCloseApplicationOp was received or not.

    You don't have to ``perform()`` or ``acknowledge()`` this operation type.
    """

    @override
    def _arm_warning(self) -> None:
        pass


@dataclass
class CloseApplicationOp(Operation):
    """Removes DOM elements and closes the window."""

    with_browser: bool

    async def perform(self) -> None:
        self.handled = True
        await self.app._close_all_dialogs()


@dataclass
class OpenDialogOp(Operation):
    props: dict[str, object]

    async def perform(self) -> Dialog:
        self.handled = True

        from aisikl.dialog import Dialog  # Cyclic dependency :(

        app = self.app
        props = self.props

        name = ct(str, props['id'])
        await app.ctx.log(
            'operation', f'Opening dialog {name} "{props['title']}"')

        if props['isMain'] != (len(app.dialog_stack) == 0):
            raise AISBehaviorError(
                f"Unexpected dialog with isMain = {props["isMain"]!r}")

        # Ignore properties that only affect visuals: basedOnTheme, style,
        # isDlgDefaultStyleUsed, x, y, w, h, ra (resizeable), ma (minimizeable),
        # minWidth, minHeight, and forControlOfParent.
        dialog = Dialog(
            name=name,
            title=ct(str, props['title']),
            code=ct(str, props['code']),
            parent_dialog_name=ct_none(str, props.get('parentDlgName')),
            modal=ct(bool, props['modal']),
            is_main_dialog=ct(bool, props['isMain']),
            closeable=ct(bool, props['ca']),
            hide_title_bar=ct(bool, props['htb']),
            app=app,
        )
        app.dialog_stack.append(dialog)
        app.dialogs[name] = dialog

        # The topmost modal dialog will be active. If no modals exist, this
        # dialog will be active.
        modals = [d for d in app.dialog_stack if d.modal]
        app.active_dialog = modals[-1] if modals else dialog

        url_params = '&'.join(
            f'{k}={v}' for k, v in app._prepare_url_base().items())
        url = f'/ais/servlets/WebUIServlet?{url_params}&form={name}'
        await dialog._init(url)

        return dialog


@dataclass
class CloseDialogOp(Operation):
    name: str
    is_native: bool = False

    async def perform(self) -> None:
        self.handled = True

        if self.is_native:
            raise AISParseError("closeDialog() with isNative is not supported")

        app = self.app
        name = self.name
        dialog = app.dialogs.get(name)
        if not dialog:
            return

        await app.ctx.log('operation', f'Closing dialog {name}')

        app.dialog_stack.remove(dialog)
        del app.dialogs[name]

        if dialog == app.active_dialog or not app.active_dialog:
            modals = [d for d in app.dialog_stack if d.modal]
            app.active_dialog = (modals or app.dialog_stack or [None])[-1]

        # Just for completeness. In practice, WebUI has not been observed to
        # call closeDialog on the last dialog.
        if not app.dialog_stack:
            await app.force_close()


@dataclass
class RefreshDialogOp(Operation):
    name: str

    async def perform(self) -> None:
        self.handled = True

        dialog = self.app.dialogs[self.name]

        await self.app.ctx.log(
            'operation', f'Refreshing dialog {dialog.name} "{dialog.title}"')

        url = f'/ais/servlets/WebUIServlet?appId={self.app.app_id}&form={dialog.name}&antiCache={time.time()}'
        await dialog._init(url)


class Operations(list[Operation]):
    """A list of operations."""

    def expect_one[T: Operation](self, expected_type: type[T]) -> T:
        """Checks there is exactly one operation and it has the given type. Then
        returns it.
        """
        self.expect_types(expected_type)
        return cast("T", self[0])

    def expect_two[T1: Operation, T2: Operation](
        self, expected_type1: type[T1], expected_type2: type[T2]
    ) -> tuple[T1, T2]:
        """Checks there are exactly two operations and they have the given
        types. Then returns them.
        """
        self.expect_types(expected_type1, expected_type2)
        return cast("tuple[T1, T2]", tuple(self))

    def has_types(self, *expected_types: type[Operation]) -> bool:
        """Returns True if the contained operations have exactly the expected
        types.

        Type checkers doesn't understand it, so you'll still have to use
        ``ct()`` or ``cast()``.
        """
        return list(expected_types) == [type(op) for op in self]

    def expect_types(self, *expected_types: type[Operation]) -> None:
        r"""Ensures the contained operations are of exactly the given types.

        Type checkers doesn't understand it, so you'll still have to use
        ``ct()`` or ``cast()``.

        Raises:
            ~aisikl.exceptions.AISBehaviorError: if the types don't match.
        """
        real_types = [type(op) for op in self]
        expected_types_list = list(expected_types)
        if real_types != expected_types_list:
            self.acknowledge_all()
            expected_names = ", ".join(t.__name__ for t in expected_types)
            raise AISBehaviorError(
                f"We expected [{expected_names}] but AIS did something different: {self!r}")

    def acknowledge_all(self) -> None:
        """Suppresses the unhandled warning on all contained operations. See
        :meth:`Operation.acknowledge`.
        """
        for op in self:
            op.acknowledge()


known_operations = {
    ("webui", "messageBox"): MessageBoxOp,
    ("webui", "confirmBox"): ConfirmBoxOp,
    ("webui", "calendarBox"): CalendarBoxOp,
    ("webui", "fileUpload"): FileUploadOp,
    ("webui", "fileXUpload"): FileXUploadOp,
    ("webui", "abortBox"): AbortBoxOp,
    ("webui", "editDoc"): EditDocOp,
    ("webui", "shellExec"): ShellExecOp,
    ("webui", "showHelp"): ShowHelpOp,
    ("webui", "startApp"): StartAppOp,
    ("webui", "serverCloseApplication"): ServerCloseApplicationOp,
    ("webui", "closeApplication"): CloseApplicationOp,
    ("dm", "closeDialog"): CloseDialogOp,
    ("dm", "refreshDialog"): RefreshDialogOp,
}
