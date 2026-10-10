# pyright: reportUninitializedInstanceVariable=none

from httpx2 import HTTPStatusError
from inspect import iscoroutinefunction
import json
import re
import time
import urllib.parse
from aisikl.exceptions import AISParseError, AISBehaviorError, AISApplicationClosedError, LoggedOutError
from aisikl.dialog import Dialog
from aisikl.operations import CloseApplicationOp, MessageBoxOp, OpenDialogOp, Operations, ServerCloseApplicationOp, known_operations
from aisikl.typeutils import ct, nn
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from aisikl.context import Context
    from aisikl.events import Event
    from bs4 import BeautifulSoup


#: The default value for :attr:`Application.ignored_messages`
DEFAULT_IGNORED_MESSAGES = [
    'Činnosť úspešne dokončená.',
    'Podmienkam nevyhovuje žiadny záznam.',
    'Používate nepodporovaný prehliadač ',
]


# Regexes for parsing AIS JavaScript
_alert_re = re.compile(r'^function main\(\) { alert\((\'.*\')\); }$')
_app_properties_re = re.compile(r'(?:^|\n)var appProperties=(.*);\s*$')
_functions_re = re.compile(r'\nfunction (\w+)')
_var_re = re.compile(r'^var \w+;\s*')
_trycatch_re = re.compile(r'^try {\s*|\s*} *catch *\(e\) *{ *(return;)? *}$')
_multiline_res = [
    re.compile(r'if *\( *dm\(\) *!= *null *\) *{\s*\n\s*dm\(\)\.checkDialogStacksEmpty\(\);?\s*\n\s*}'),
]
_useless_res = [
    re.compile(r'^function [^{]*\{[^}]*\}$'),
    re.compile(r'^if \(isResponseIdle\(\d+\)\) { return; }$'),
    re.compile(r'^webui\(\)\.noteLastDoneRequest\(\d+\)$'),
    re.compile(r'^window\.parent\.Logger_log'),
    re.compile(r'^webui\(\)\.prepareUpdatingDialogs\(\)$'),
    re.compile(r'^webui\(\)\.enableApplication\(\)$'),
    re.compile(r'^main0?\(\)$'),
    re.compile(r'^\w+=dm\(\)\.getDialog\(\'\w+\'\)\.getDialogContext\(\)$'),
    re.compile(r'^if \(dm\(\)!=null\) \w+=dm\(\)\.getDialog\(\'\w+\'\)$'),
    re.compile(r'^if \(\w+!=null\) \w+=\w+\.getDialogContext\(\)$'),
    re.compile(r'^if \(\w+!=null\) \w+\.tryAutosize\(\)$'),
    re.compile(r'^var componentsProperties = \{\}$'),
    re.compile(r'^dm\(\)\.setActiveDialogName\(\'\w+\'\)$'),
    # TODO: Perhaps we should handle setActiveDialogName, or at least check if
    # it's the same as the current active dialog.
    re.compile(r'^dm\(\)\.prepareBrowserForDialogsOpen\(showDlgProperties\)$'),
]
_main_re = re.compile(r'^function main0?\(\) \{$')
_operation_re = re.compile(r'^(webui|dm)\(\)\.(\w+)\((.*)\)$')
_update_re = re.compile(r'^f\(\)\.getControlById\("(\w+)", *(\w+)\)\.(\w+)\((.*)\)$')
_dialog_update_re = re.compile(r'^(\w+)\.getDialogJSObject\(\)\.(\w+)\((.*)\)$')
_access_token_re = re.compile(r'retrieveAccessToken\(\)\s*\{[^{}]*setRequestHeader\("([^\\"]+)",\s*"([^\\"]+)"\)')


def _parse_args(args_str: str) -> list[object]:
    # args_str are WebUI's arguments for a JavaScript function call. We want to
    # parse it with our JSON parser. But WebUI needlessly escapes apostrophes,
    # and `\'` is not a valid escape in JSON. So we replace `\'` with `'`. But
    # we don't want to touch `\\'`, because that's a valid escape sequence
    # followed by a normal apostrophe. We solve this by temporarily replacing
    # `\\` with an invalid character, ensuring that `\'` is captured correctly.
    args_str = (args_str
        .replace('\\\\', '\x00')
        .replace('\\\'', '\'')
        .replace('\x00', '\\\\'))
    return json.loads('[' + args_str + ']')


class Application[D]:
    r'''An opened AIS application. (That is, a "browser window".)

    Instances cannot be created directly. Use :meth:`open` if you know the full
    URL (e.g. from the :mod:`~aisikl.portal`), or
    :meth:`aisikl.operations.StartAppOp.perform` when opening an application
    from another one.

    Attributes:
        ctx: The :class:`~aisikl.context.Context`.
        dialogs: The dict of open :class:`~aisikl.dialog.Dialog`\ s.
        dialog_stack:
            The ordered list of open :class:`~aisikl.dialog.Dialog`\ s.
        active_dialog: The currently active dialog.
        d: The currently active dialog.
        last_response_time: When did this app last receive a WebUI response.
        ignored_messages: List of ignored message patterns. When the application
            receives a :class:`~aisikl.operations.MessageBoxOp` operation whose
            message contains any of the patterns, the operation will be ignored:
            it won't be returned in :class:`~aisikl.operations.Operations`, and
            won't cause exceptions if left uncollected. This attribute can be
            modified.
    '''

    ctx: Context
    dialogs: dict[str, Dialog]
    dialog_stack: list[Dialog]
    active_dialog: Dialog | None
    last_response_time: float
    ignored_messages: list[str]

    @classmethod
    async def open(cls, ctx: Context, url: str, ignored_messages: list[str] | None=None) -> tuple[Application[D], Operations]:
        '''Opens a new application.

        Returns an ``(app, ops)`` tuple containing the new Application instance
        and the initial list of operations caused by the "INIT" event. This
        list must be handled as usual -- see
        :class:`~aisikl.operations.Operation`. For example, use
        ``await ops.expect_one(OpenDialogOp).perform()`` if you expect the
        application to contain one dialog.

        Args:
            ctx: The :class:`~aisikl.context.Context` to use.
            url: The main app URL. Can be relative to the server root.
            ignored_messages: The initial value for :attr:`ignored_messages`.
                Defaults to :data:`DEFAULT_IGNORED_MESSAGES`.
        Returns:
            An `(app, ops)` tuple with the new instance and the initial list of
            operations.
        '''
        app = super().__new__(cls)
        ops = await app._open(ctx, url, ignored_messages)
        return app, ops

    def __init__(self) -> None:
        # This is because open() needs to return two values, and __init__ can't
        # change the return value. __new__ could, but we want normal pickling.
        raise Exception(
            "The Application constructor is private, use open() instead")

    async def _open(self, ctx: Context, url: str, ignored_messages: list[str] | None=None) -> Operations:
        '''Actually opens the new instance created by :meth:`open`.'''
        self.ctx = ctx
        self.serial = 0
        self.req_index = 0
        self.dialogs = {}
        self.dialog_stack = []
        self.active_dialog = None
        self.ignored_messages = (
            ignored_messages or DEFAULT_IGNORED_MESSAGES).copy()

        match = re.search(r'appClassName=([a-zA-Z0-9_\.]*)', url)
        self.class_name = match.group(1) if match else None
        await self.ctx.log('operation', f'Opening application {self.class_name}', url)

        app_soup = await self.ctx.parse_html(await self.ctx.request_ais(url))
        if not app_soup.find(id='webuiProperties'):
            alert_match = _alert_re.match(
                app_soup.script.get_text().strip() if app_soup.script else '')
            if alert_match:
                raise AISBehaviorError("AIS2 application didn't open: %s" %
                    alert_match.group(1))
            raise AISParseError("AIS2 application didn't open")

        onload = nn(app_soup.body)['onload']
        if onload != 'window.setTimeout("WebUI_init()", 1)':
            raise AISParseError("Unexpected <body> onload")
        first_script = nn(app_soup.script.string) if app_soup.script else ''
        properties_match = _app_properties_re.search(first_script)
        if not properties_match:
            raise AISParseError("Couldn't get app ID from appProperties")
        properties: dict[str, object] = json.loads(properties_match.group(1))
        if not (properties.get('appContext') == 'ais' and
                properties.get('webuiContext') == 'ais/webui2'):
            raise AISParseError("Unexpected values in appProperties")
        self.app_id = ct(str, properties['appId'])

        if nn(app_soup.find(id='initScript')).get_text() != '<!---->':
            raise AISParseError("initScript is not supported")

        rq = ("<events><ev><event class='avc.ui.event.AVCComponentEvent'>"
              "<command>INIT</command></event></ev></events>\n" +
              self._collect_component_changes())
        ops = await self._do_request(rq, return_ops=True)

        if (
            ops.has_types(
                ServerCloseApplicationOp, MessageBoxOp, CloseApplicationOp)
            and ct(MessageBoxOp, ops[1]).message == 'Neautorizovaný prístup!'
        ):
            # First two op types don't need perform(). Third is a no-op.
            await ct(CloseApplicationOp, ops[2]).perform()

            # If access is denied just because the session expired, raise
            # LoggedOutError. If access is really denied for this user, return
            # the three ops, and the caller can deal with it.
            await check_connection(self.ctx)

        return ops

    @property
    def d(self) -> D:
        return cast(D, nn(self.active_dialog))

    def activate_dialog(self, name: str) -> None:
        '''Activates a dialog. This is like clicking a dialog in WebUI.

        Aisikl doesn't prevent you from accessing inactive dialogs, but it's
        recommended for users of aisikl to only use ``app.active_dialog``
        (``app.d``) and call this method to change its value when needed.

        However, WebUI only allows changing the active dialog if no modal
        dialogs are open. So far we've never seen multiple open dialogs where
        one wasn't modal. This method exists just for completeness.

        Args:
            name: Name of the dialog to activate.
        Raises:
            ValueError: Raised if a modal dialog is open.
        '''
        if self.active_dialog and self.active_dialog.name == name:
            return
        if any(d.modal for d in self.dialog_stack):
            raise ValueError(
                "Cannot change active dialog while a modal dialog is open")
        self.active_dialog = self.dialogs[name]

    def _prepare_url_base(self) -> dict[str, str]:
        old_req_index = self.req_index
        self.req_index += 1
        return { 'appId': self.app_id, 'antiCache': str(time.time()),
                 'reqIndex': str(old_req_index), 'viewer': 'web' }

    async def _do_request(self, body: str, *, return_ops: bool) -> Operations:
        '''Sends a POST request to AIS and process the response.

        Usually called from :meth:`send_events`.
        '''
        soup = await self._send_request(body)
        return await self._process_response(soup, return_ops=return_ops)

    async def _send_request(self, body: str) -> BeautifulSoup:
        xml_spec = f'<request> <serial>{self.serial}</serial>\n{body}</request>\n'
        self.serial += 1

        params = self._prepare_url_base()
        data = params.copy()
        data['xml_spec'] = xml_spec

        # WebUIServlet needs charset set in Content-Type. Normal POST requests
        # don't have it, but sendRequestEvent manually sets it, so we do the
        # same.
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        return await self.ctx.parse_html(await self.ctx.request_ais(
            '/ais/servlets/WebUIServlet?' + urllib.parse.urlencode(params),
            method='POST', data=data, headers=headers))

    async def _process_response(self, soup: BeautifulSoup, *, return_ops: bool) -> Operations:
        await self.ctx.log('benchmark', 'Begin response frame processing')
        self.last_response_time = time.time()

        operations = Operations()
        updates: list[tuple[str, str, str, list[object]]] = []

        script_tag = nn(soup.head).script
        if not script_tag or script_tag.get('src'):
            raise AISParseError("Unexpected result frame response")
        script = script_tag.get_text()

        match = _alert_re.match(script.strip())
        if match:
            raise AISBehaviorError('AIS error in result frame response: %s' %
                match.group(1))

        functions = [m.group(1) for m in _functions_re.finditer(script)]
        if ','.join(functions) == 'main' and 'onAppClosedOnServer' in script:
            raise AISApplicationClosedError("Application has already closed")
        if ','.join(functions) != 'webui,f,dm,isResponseIdle,main0,main':
            raise AISParseError("Unexpected script in result frame response")

        in_main = False
        show_dlg_properties = None

        for r in _multiline_res:
            script = r.sub('', script)

        for line in script.split('\n'):
            line = line.strip()
            line = _var_re.sub('', line)
            line = _trycatch_re.sub('', line)
            line = line.strip(';')

            if not line: continue
            if any(r.match(line) for r in _useless_res): continue

            if line.startswith('var showDlgProperties ='):
                if in_main: raise AISParseError("Bad script structure")
                if show_dlg_properties is not None:
                    raise AISParseError("Duplicate showDlgProperties")
                show_dlg_properties: list[dict[str, object]] | None = json.loads(line.partition('=')[2])
                continue

            if _main_re.match(line):
                if in_main: raise AISParseError("Bad script structure")
                in_main = True
                continue

            if line == '}':
                if not in_main: raise AISParseError("Bad script structure")
                in_main = False
                continue

            if not in_main:
                raise AISParseError("Unexpected line out of main() or main0()")

            if line == 'dm().showDialogs(showDlgProperties)':
                if show_dlg_properties is None:
                    raise AISParseError("Missing showDlgProperties")
                for dialog in show_dlg_properties:
                    await self.ctx.log(
                        "operation", f"Received operation openDialog",
                        ["dm", "openDialog", [dialog]])
                    operations.append(OpenDialogOp(dialog, app=self))
                continue

            match = _operation_re.match(line)
            if match:
                target, method, args_str = match.groups()
                args = _parse_args(args_str)
                if (target, method) not in known_operations:
                    raise AISParseError(f"Unknown method {target}().{method}()")
                await self.ctx.log(
                    "operation", f"Received operation {method}",
                    [target, method, args])
                if not (
                    method == 'messageBox'
                    and isinstance(args[0], str)
                    and any(s in args[0] for s in self.ignored_messages)
                ):
                    operations.append(
                        known_operations[(target, method)](*args, app=self))  # pyrefly: ignore [bad-argument-type] # pyright: ignore [reportArgumentType]
                continue

            match = _update_re.match(line)
            if match:
                target, dialog, method, args_str = match.groups()
                args = _parse_args(args_str)
                updates.append((dialog, target, method, args))
                continue

            match = _dialog_update_re.match(line)
            if match:
                target, method, args_str = match.groups()
                args = _parse_args(args_str)
                updates.append((target, target, method, args))
                continue

            raise AISParseError(f"Couldn't parse script line: {line}")

        if operations and not return_ops:
            raise AISBehaviorError(
                f"AIS did an unexpected operation: {operations}")

        body = soup.body

        if updates:
            await self.ctx.log('update',
                f'Updating {len(updates)} components', updates)

        for dialog_name, component_name, method_name, args in updates:
            if (dialog := self.dialogs.get(dialog_name)) is None:
                raise AISParseError(f"Dialog {dialog_name!r} doesn't exist.")

            if (component := dialog.components.get(component_name)) is None:
                if component_name == "HeaderView":
                    continue   # a mysterious non-existent component
                raise AISParseError(f"Component {component_name!r} doesn't exist in {dialog_name!r}.")

            try:
                method = getattr(component, '_ais_' + method_name)
            except AttributeError:
                raise AISParseError("Method %r of %s is not yet implemented." %
                    (method_name, component.__class__.__name__)) from None

            if getattr(method, 'wants_body', False):
                args = args + [body]

            if iscoroutinefunction(method):
                await method(*args)
            else:
                method(*args)

        await self.ctx.log('benchmark', 'End response frame processing')

        for operation in operations:
            operation._arm_warning()  # pyright: ignore [reportPrivateUsage]

        return operations

    async def send_events(self, *events: Event, return_ops: bool) -> Operations:
        r'''Sends the given events to AIS, if AIS is listening to them.

        :param \*events: the events to send.
        '''
        body = ''.join(e.xml for e in events if e.listening)
        if not body:
            return Operations()
        return await self._do_request(
            '<events>' + body + '</events>' + self._collect_component_changes(),
            return_ops=return_ops)

    async def _send_empty_request(self, return_ops: bool) -> Operations:
        '''Sends a request without any events to AIS.'''
        return await self._do_request(self._collect_component_changes(), return_ops=return_ops)

    async def _send_namevalue_request(self, name: str, value: int | str, return_ops: bool) -> Operations:
        '''Helper function for small requests sent by some operations.
        These requests don't contain any events or component changes.
        '''
        return await self._do_request(
            '<changedProps><changedProperties><propertyValues><nameValue>' +
            f'<name>{name}</name><value>{value}</value>' +
            '</nameValue></propertyValues></changedProperties></changedProps>',
            return_ops=return_ops)

    async def force_close(self) -> bool:
        '''Tells the server to close the application.

        Human users usually close applications with the exit button in the main
        dialog. This method disregards open dialogs and just closes everything.
        It's similar to closing the app's browser popup window (in theory). It
        also usually works even if the application is already closed.

        Returns:
            True if the application is successfully closed, or already was.
            False if there was an error, e.g. when the server is still busy with
            an earlier HTTP request.
        '''
        await self._close_all_dialogs()
        await self.ctx.log('operation',
            f'Sending WebUIKillEvent to {self.class_name}')
        soup = await self._send_request(
            "<events><ev><event class='avc.framework.webui.WebUIKillEvent'/>"
            "</ev></events>\n")
        return not soup.script

    def _collect_component_changes(self) -> str:
        '''Returns the <changedProps> string that goes into POST requests.'''
        app_changes = ''
        if self.active_dialog:
            app_changes = (
                '<changedProperties><objName>app</objName><propertyValues>\n' +
                '<nameValue><name>activeDlgName</name><value>' +
                self.active_dialog.name +
                '</value></nameValue>\n' +
                '</propertyValues></changedProperties>\n')

        return ('<changedProps>\n' +
            app_changes +
            ''.join(d.changed_properties() for d in self.dialog_stack) +
            '</changedProps>\n')

    async def is_still_open(self) -> bool:
        '''Checks whether this application is still open.

        The AIS server forgets about open applications after a short period of
        inactivity (much shorter than the session expiring). If that happens,
        the program must stop using this Application and start anew.

        If this application contacted the server recently, we assume it's still
        open. Otherwise, we test it by sending an empty request.

        Returns:
            True if the server still accepts requests from this application.
        '''
        if not self.dialog_stack: return False
        THRESHOLD = 5 * 60
        if time.time() - self.last_response_time > THRESHOLD:
            await self.ctx.log('operation',
                f'Checking if {self.class_name} is still open')
            try:
                await self._send_empty_request(return_ops=False)
            except AISApplicationClosedError:
                await self.ctx.log('operation',
                    f'Server already closed {self.class_name}')
                return False
        return True

    async def _close_all_dialogs(self) -> None:
        if self.dialog_stack:
            await self.ctx.log('operation', 'Closing all dialogs')
        self.dialogs.clear()
        self.dialog_stack.clear()
        self.active_dialog = None


async def check_connection(context: Context) -> None:
    # We used to request /ais/portal/changeTab.do?tab=0, but it switches the
    # user to the old interface. Same with / or /ais/start.do. This should work
    # regardless of old vs new student interface, and preserve the user's
    # preference for next time they log in to AIS directly.

    try:
        # Find the magic header value that must be sent on .../get-access-token.
        # It is mostly stable, but sometimes changes rarely on some AIS updates.
        # It can also be found in an inline script in /ais/start.do, but
        # requesting that would switch the user to the old interface.
        response = await context.request_ais('/ais/apps/student/sk/main.js')
        match = _access_token_re.search(response.text)
        if not match:
            raise AISParseError('Could not find header in main.js code')

        # This request returns 200 with empty body if logged in (and strangely
        # also if no JSESSIONID is sent), or 401 if a JSESSIONID is sent but the
        # session is logged out or expired.
        response = await context.request_ais(
            '/ais/rest/apps/get-access-token',
            headers={match.group(1): match.group(2)})
        aisauth = response.headers.get('AISAuth')
        if not aisauth:
            raise AISParseError('Missing AISAuth header')

        # This returns empty 200 if logged in or empty 401 if logged out.
        # The first request might be sufficient, this one is just to faithfully
        # recreate what AIS is doing.
        # Future note: If we store the aisauth value for a longer time, we
        # should always check if a response contains a new AISAuth header.
        await context.request_ais(
            '/ais/rest/apps/check-session/check-light',
            headers={'AISAuth': aisauth})
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            raise LoggedOutError('AIS login expired.') from e
        else:
            raise e
