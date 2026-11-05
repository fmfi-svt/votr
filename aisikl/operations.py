"""Operations module.

Operations are records of "big" actions done by AIS that aren't handled by
Aisikl automatically, and need to be taken care of by the caller. For example:

- Opening a new application or browser window
- Showing a message box or another modal dialog
- Opening and closing dialogs

Operations are similar to events, but in the server-to-client direction instead
of client-to-server.

# The ``return_ops`` argument

Various aisikl functions, such as
[`Button.click`][aisikl.components.button.Button.click], have a ``return_ops``
argument.

-   If you expect something to happen, use ``return_ops=True`` to enable
    "operation collecting mode". The function will return an [`Operations`][]
    list. You have to check if the operations are what you expected, and *deal
    with* them. The returned list can be empty if nothing happened.

    ```python
    # This button should open a dialog. If it does something
    # different, or nothing at all, an error is raised.
    ops = await app.d.newDialogOpeningButton.click(return_ops=True)
    await ops.expect_one(OpenDialogOp).perform()
    ```

-   Otherwise (without ``return_ops=True``), it means you don't expect anything
    to happen. The function returns an empty [`Operations`][] list. If something
    happens anyway, it raises an error.

    ```python
    # If this button does anything weird (e.g. shows
    # a message box), an error is raised.
    await app.d.someInnocentButton.click()
    ```

# *Dealing with* operations

When you use ``return_ops=True``, you are making a promise to *deal with*
every [`Operation`][] you get. The way to *deal with* an operation depends on
its type, but usually it is with a method named ``perform``. *Dealing with*
operations is necessary to keep Votr and the AIS server on the same page about
what is going on.

As a developer reminder, ``Operation`` prints a warning if it's
garbage-collected without having been *dealt with*.

Caveat: It's OK to ignore operations when you raise an error -- including, but
not limited to, raising an error because the operations you got aren't what you
expected. The reason why it's OK is that raising an error usually has the
consequence of closing or abandoning this [`Application`][], so it doesn't
matter if any desynchronization happens after that point. But for errors you
raise yourself, you might need to call [`acknowledge`][Operation.acknowledge]
first, to disable the warning.

# Examples of checking operation types

[`Operations`][] has useful methods to check types of its contents.

When you expect a single operation of a known type, e.g. ``OpenDialogOp``:

```python
await ops.expect_one(OpenDialogOp).perform()
```

When you expect two operations of known types, e.g. two ``OpenDialogOp``:

```python
op1, op2 = ops.expect_two(OpenDialogOp, OpenDialogOp)
await op1.perform()
await op2.perform()
```

When you expect that AIS could EITHER do something specific OR do nothing:

```python
if ops:
    await ops.expect_one(OpenDialogOp).perform()
else:
    return ...  # nothing happened
```

When you expect that AIS always does something (e.g. ``CloseDialogOp``), but
might show a confirm box first:

```python
if ops.has_types(ConfirmBoxOp):
    ops = await ops.expect_one(ConfirmBoxOp).reply(
        ConfirmBoxOp.Option.YES, return_ops=True)
    # ^ Reassigns ops.
await ops.expect_one(CloseDialogOp).perform()
```

When you expect one of three or more possible types:

```python
if ops.has_types(OpenDialogOp):
    await ops.expect_one(OpenDialogOp).perform()
    ...
elif ops.has_types(CloseDialogOp):
    await ops.expect_one(CloseDialogOp).perform()
    ...
else:
    await ops.expect_one(AbortBoxOp).perform()
    ...
```
"""

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
    from collections.abc import Iterable
    from httpx2 import Response


@dataclass
class Operation:
    """Base class for operations."""

    app: Application[object] = field(repr=False, kw_only=True)
    _handled: bool = field(default=True, init=False, repr=False)

    def arm_warning(self) -> None:
        """Internal. Enables the "not *dealt with*" warning."""
        self._handled = False

    def acknowledge(self) -> Self:
        """Marks the operation as *dealt with*.

        You can use ``acknowledge()`` to disable the "not *dealt with*" warning,
        expressing that you abstained from calling ``perform()`` intentionally
        and not because you forgot. One such case is before you raise an error.
        """
        self._handled = True
        return self

    def __del__(self) -> None:
        """Prints a warning if the operation is garbage-collected without being
        *dealt with*.
        """
        if not self._handled:
            warn(f"Unhandled operation {self!r}", stacklevel=2, source=self)


@dataclass
class MessageBoxOp(Operation):
    """AIS wants to show a message.

    You don't have to *deal with* this operation type.

    Message boxes matching [`Application.ignored_messages`][] are ignored: they
    won't appear in [`Operations`][], and won't trigger unexpected operation
    errors with ``return_ops=False``.
    """

    message: str
    title: str
    image: str
    detail: str

    @override
    def arm_warning(self) -> None:
        """Internal. Does nothing."""
        pass


@dataclass
class ConfirmBoxOp(Operation):
    """AIS wants to ask a question."""

    message: str
    title: str
    image: str
    buttons: int
    # Not a bitmask. It's complicated. See /ais/webui2/webui/confirmBox.js
    check: int
    check_box_label: str
    detail: str
    default_button: int

    class Option(Enum):
        """Enum of possible confirm box buttons."""
        # See /ais/webui2/web/confirmBox.html
        YES_TO_ALL = 4
        YES = 2
        OK = 1
        CANCEL = -1
        NO = -2
        NO_TO_ALL = -4

    async def reply(
        self, option: Option, *, return_ops: bool = False
    ) -> Operations:
        """Answers the question. *Deals with* this operation."""
        self._handled = True
        await self.app.ctx.log(
            'operation', f'Selecting button {option.value} in confirm box')
        return await self.app.send_namevalue_request(
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
    """AIS wants us to please wait."""

    message: str
    title: str | None = None

    async def perform(self, *, return_ops: bool = False) -> Operations:
        """Waits. *Deals with* this operation."""
        self._handled = True
        await self.app.ctx.log('operation', 'Waiting for abort box')
        return await self.app.send_namevalue_request(
            'confirmResult', -1, return_ops=return_ops)


@dataclass
class EditDocOp(Operation):
    """Never seen yet. Types are guesses. perform() not yet implemented."""

    office_file_name: str


@dataclass
class ShellExecOp(Operation):
    """AIS wants us to download a file (probably)."""

    content_type: str
    file_name: str
    new_window_name: str
    width: int
    height: int

    async def download(self) -> Response:
        """Downloads a file. Then sends a request to AIS saying that the
        shellExec was executed. *Deals with* this operation.

        This method only supports the common use of shellExec -- downloading
        files. In theory, if ``content_type == "webui/execCustomFunction"``,
        then webui.shellExec() can run custom JavaScript code. But this was
        never seen. If you need that, simulate it manually and call
        [`send_result`][] instead of ``download``.
        """
        self._handled = True

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
        """Informs AIS that a shellExec operation was executed. *Deals with*
        this operation.
        """
        self._handled = True
        return await self.app.send_namevalue_request(
            'shellExecResult', shell_exec_result, return_ops=return_ops)


@dataclass
class ShowHelpOp(Operation):
    """AIS wants to open ``url`` in a new window.

    Rare. Seen e.g. in debug info dialogs of tables on ``ais2-beta``.

    There is no ``perform()``. Do something appropriate with the given ``url``
    and call ``acknowledge()``.
    """

    url: str


@dataclass
class StartAppOp(Operation):
    """AIS wants to open a new AIS application (browser window)."""

    url: str
    params: str

    async def perform[D](
        self,
        *,
        ignored_messages: Iterable[str] | None = None,
        hint: type[D] | None = None,
    ) -> tuple[Application[D], Operations]:
        """Opens the application. *Deals with* this operation.

        Args:
            ignored_messages: Same as in [`Application.open`][].
            hint: Dialog type hint for static type checkers. Ignored at runtime.
                (It's a parameter because Python generic functions don't support
                explicit ``func[T](...)`` call syntax.)

        Returns:
            app: Same as in [`Application.open`][].
            ops: Same as in [`Application.open`][] -- see its docs for advice.
        """
        self._handled = True

        from aisikl.app import Application  # Cyclic dependency :(

        url = f'/ais/servlets/WebUIServlet?appClassName={self.url}{self.params}&antiCache={time.time()}'
        return await Application[D].open(self.app.ctx, url, ignored_messages)


@dataclass
class ServerCloseApplicationOp(Operation):
    """AIS wants to tell us that we don't have to send a ``WebUIKillEvent``.

    You don't have to *deal with* this operation type.

    Empirically, this operation is always sent together with
    [`CloseApplicationOp`][], sometimes with [`MessageBoxOp`][] between the two.

    Its original meaning is to enable the ``wasClosedOnServer`` flag, which
    tells webui.js that it shouldn't send a ``WebUIKillEvent`` during cleanup.
    Votr does not implement it exactly. Instead of remembering whether a
    ``ServerCloseApplicationOp`` was received or not, Votr never sends
    ``WebUIKillEvent`` in [`CloseApplicationOp.perform`][] (because of the above
    empirical observation), and always sends it in
    [`Application.force_close`][] (because we don't trust the AIS server that
    much, and sending an extra one is harmless).
    """

    @override
    def arm_warning(self) -> None:
        """Internal. Does nothing."""
        pass


@dataclass
class CloseApplicationOp(Operation):
    """AIS wants to close the application."""

    with_browser: bool

    async def perform(self) -> None:
        """Closes the application. *Deals with* this operation.

        In webui.js, this deletes all DOM elements and closes the browser
        window. In Votr, we can't exactly destroy the [`Application`][] object
        itself, but we can at least close all its dialogs, making it inert.
        """
        self._handled = True
        await self.app.close_all_dialogs()


@dataclass
class OpenDialogOp(Operation):
    """AIS wants to open a dialog."""

    props: dict[str, object]

    async def perform(self) -> Dialog:
        """Opens the dialog. *Deals with* this operation."""
        self._handled = True

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
            f'{k}={v}' for k, v in app.prepare_url_base().items())
        url = f'/ais/servlets/WebUIServlet?{url_params}&form={name}'
        await dialog.init(url)

        return dialog


@dataclass
class CloseDialogOp(Operation):
    """AIS wants to close a dialog."""

    name: str
    is_native: bool = False

    async def perform(self) -> None:
        """Closes the dialog. *Deals with* this operation."""
        self._handled = True

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
    """AIS wants to refresh (i.e. reload the HTML structure of) a dialog."""

    name: str

    async def perform(self) -> None:
        """Refreshes the dialog. *Deals with* this operation."""
        self._handled = True

        dialog = self.app.dialogs[self.name]

        await self.app.ctx.log(
            'operation', f'Refreshing dialog {dialog.name} "{dialog.title}"')

        url = f'/ais/servlets/WebUIServlet?appId={self.app.app_id}&form={dialog.name}&antiCache={time.time()}'
        await dialog.init(url)


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
            aisikl.exceptions.AISBehaviorError: If the types don't match.
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
        [`Operation.acknowledge`][].
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
"""Internal mapping from webui.js (global object name, method name) pairs to
Aisikl operation classes.
"""
