
from collections import namedtuple
from contextlib import contextmanager
import json
import re
from requests import HTTPError
import time
import urllib.parse
from .exceptions import (
    AISParseError, AISBehaviorError, AISApplicationClosedError, LoggedOutError)
from .dialog import Dialog


#: Record of a "big" action done by AIS that isn't handled automatically
#: and requires some reaction, such as:
#:
#: - Opening a new application or browser window
#: - Showing a message box or another modal dialog
#: - Opening and closing dialogs
#:
#: You can use :meth:`Application.collect_operations` to express that you
#: expected something to happen and are prepared to handle it, or use
#: :attr:`Application.ignored_messages` to specify that some ``messageBox``
#: Operations can be safely ignored. If an Operation isn't collected or
#: safely ignored, it throws an exception.
#:
#: Attributes:
#:     target: The target JavaScript object. Either "webui" or "dm". Usually,
#:         you just need :attr:`method`.
#:     method: The type of the operation -- the name of the WebUI JavaScript
#:         method being called. See :data:`known_operations` for possible
#:         values.
#:     args: The list of attributes to the JavaScript method. Votr follows the
#:         same signatures as WebUI. For example, if ``op.method ==
#:         "openDialog"``, the Votr call is ``app.open_dialog(*op.args)``.
Operation = namedtuple('Operation', ('target', 'method', 'args'))


#: Record of AIS calling a setter on some component.
#:
#: Attributes:
#:     dialog: The dialog name.
#:     target: The target component name.
#:     method: The setter method that is called. In Votr, this original
#:         method name will be prefixed with ``_ais_``.
#:     args: The list of setter arguments. (Usually a single string.)
Update = namedtuple('Update', ('dialog', 'target', 'method', 'args'))


#: The known :class:`Operation` methods.
known_operations = {
    'webui': { 'serverCloseApplication', 'closeApplication', 'messageBox',
               'confirmBox', 'fileUpload', 'fileXUpload', 'editDoc',
               'abortBox', 'shellExec', 'showHelp', 'startApp' },
    'dm': { 'openMainDialog', 'openDialog', 'closeDialog', 'refreshDialog' },
}


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


def _parse_args(args_str):
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


def parse_response(soup):
    '''Parses the resultFrame content (the response to a POST request).

    Args:
        soup: The HTML structure.
    Returns:
        An ``(operations, updates)`` tuple. ``operations`` is a list of
        :class:`Operation`\ s. ``updates`` is a list of :class:`Update`\ s.
    '''
    operations = []
    updates = []

    script_tag = soup.head.script
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
            show_dlg_properties = json.loads(line.partition('=')[2])
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
                # openMainDialog doesn't exist anymore, but we kept the name
                # because it's convenient for existing fladgejt code.
                method = 'openMainDialog' if dialog['isMain'] else 'openDialog'
                operations.append(Operation('dm', method, [dialog]))
            continue

        match = _operation_re.match(line)
        if match:
            target, method, args_str = match.groups()
            args = _parse_args(args_str)
            if method not in known_operations[target]:
                raise AISParseError("Unknown method {}().{}()".format(
                    target, method))
            operations.append(Operation(target, method, args))
            continue

        match = _update_re.match(line)
        if match:
            target, dialog, method, args_str = match.groups()
            args = _parse_args(args_str)
            updates.append(Update(dialog, target, method, args))
            continue

        match = _dialog_update_re.match(line)
        if match:
            target, method, args_str = match.groups()
            args = _parse_args(args_str)
            updates.append(Update(target, target, method, args))
            continue

        raise AISParseError("Couldn't parse script line: {}".format(line))

    return (operations, updates)


def assert_ops(operations, *expected_methods):
    '''Ensures the list of collected operations contains the methods we expect.

    This is a helper method you can use after calling
    :meth:`~Application.collect_operations`. It just looks at each operation's
    :attr:`~Operation.method` and checks if they match.

    :param operations: The collected operations.
    :param \*expected_methods: A list of method names.
    Raises:
        ~aisikl.exceptions.AISBehaviorError: Raised if the methods don't match.
    '''
    real_methods = [op.method for op in operations]
    expected_methods = list(expected_methods)
    if real_methods != expected_methods:
        raise AISBehaviorError(
            "We expected %r but AIS did something different: %r" %
                (expected_methods, operations),
            expected_methods=expected_methods,
            operations=operations)


class Application:
    '''An opened AIS application. (That is, a "browser window".)

    Instances cannot be created directly. Use :meth:`open` if you know the full
    URL (e.g. from the :mod:`~aisikl.portal`), or :meth:`start_app` when
    opening an application from another one.

    Attributes:
        ctx: The :class:`~aisikl.context.Context`.
        dialogs: The dict of open :class:`~aisikl.dialog.Dialog`\ s.
        dialog_stack:
            The ordered list of open :class:`~aisikl.dialog.Dialog`\ s.
        active_dialog: The currently active dialog.
        d: The currently active dialog.
        last_response_time: When did this app last receive a WebUI response.
        ignored_messages: List of ignored message patterns. When the application
            receives a ``messageBox`` :class:`Operation` whose first argument
            contains any of the patterns, the :class:`Operation` will be
            ignored: it won't be returned by :meth:`collect_operations`, and
            won't cause exceptions if left uncollected. This attribute can be
            modified.
    '''

    @classmethod
    def open(cls, ctx, url, ignored_messages=None):
        '''Opens a new application.

        Returns an ``(app, ops)`` tuple containing the new Application instance
        and the initial list of operations caused by the "INIT" event. This
        list must be processed as usual -- see :meth:`collect_operations`. For
        example, if the application should only open a main dialog, use
        ``app.awaited_open_main_dialog(ops)``. (If the user isn't authorized,
        ``ops`` will probably contain a message box saying so.)

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
        ops = app._open(ctx, url, ignored_messages)
        return app, ops

    def __init__(self):
        # This is because open() needs to return two values, and __init__ can't
        # change the return value. __new__ could, but we want normal pickling.
        raise Exception(
            "The Application constructor is private, use open() instead")

    def _open(self, ctx, url, ignored_messages=None):
        '''Actually opens the new instance created by :meth:`open`.'''
        self.ctx = ctx
        self.serial = 0
        self.req_index = 0
        self.dialogs = {}
        self.dialog_stack = []
        self.active_dialog = self.d = None
        self.collector = None
        self.ignored_messages = (
            ignored_messages or DEFAULT_IGNORED_MESSAGES).copy()

        match = re.search(r'appClassName=([a-zA-Z0-9_\.]*)', url)
        self.class_name = match.group(1) if match else None
        self.ctx.log('operation', 'Opening application {}'.format(
            self.class_name), url)

        app_soup = self.ctx.request_html(url)
        if not app_soup.find(id='webuiProperties'):
            alert_match = _alert_re.match(
                app_soup.script.get_text().strip() if app_soup.script else '')
            if alert_match:
                raise AISBehaviorError("AIS2 application didn't open: %s" %
                    alert_match.group(1))
            raise AISParseError("AIS2 application didn't open")

        onload = app_soup.body['onload']
        if onload != 'window.setTimeout("WebUI_init()", 1)':
            raise AISParseError("Unexpected <body> onload")
        first_script = app_soup.script.string if app_soup.script else ''
        properties_match = _app_properties_re.search(first_script)
        if not properties_match:
            raise AISParseError("Couldn't get app ID from appProperties")
        properties = json.loads(properties_match.group(1))
        if not (properties.get('appContext') == 'ais' and
                properties.get('webuiContext') == 'ais/webui2'):
            raise AISParseError("Unexpected values in appProperties")
        self.app_id = properties['appId']

        if app_soup.find(id='initScript').get_text() != '<!---->':
            raise AISParseError("initScript is not supported")

        rq = ("<events><ev><event class='avc.ui.event.AVCComponentEvent'>"
              "<command>INIT</command></event></ev></events>\n" +
              self.collect_component_changes())
        with self.collect_operations() as ops:
            self._do_request(rq)

        methods = [op.method for op in ops]
        if (methods == ['serverCloseApplication', 'messageBox', 'closeApplication'] and
            ops[1].args[0] == 'Neautorizovaný prístup!'):
            check_connection(self.ctx)

        return ops

    def activate_dialog(self, name):
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
        self.active_dialog = self.d = self.dialogs[name]

    @contextmanager
    def collect_operations(self):
        '''Collects :class:`Operation`\ s done by AIS.

        Calling this function means that you are expecting an Operation to
        happen and are prepared to handle it. Operations happens during this
        function will be returned in a list instead of throwing exceptions.

        You are responsible for checking that the operations are what you
        expected, and responding appropriately. This is usually done by
        calling :func:`assert_ops` and then using the relevant
        :class:`Application` methods. If you're only expecting one Operation,
        you can use one of the ``awaited_*`` methods.

        This function is used with the ``with`` keyword as a context manager::

            with app.collect_operations() as ops:
                app.d.someButton.click()

            assert_ops(ops, 'closeDialog', 'messageBox')
            app.close_dialog(*ops[0].args)
            message_text = ops[1].args[0]
        '''
        if self.collector is not None:
            raise Exception("Already inside another collect_operations()")
        self.collector = []
        try:
            yield self.collector
        finally:
            self.collector = None

    def _prepare_url_base(self):
        old_req_index = self.req_index
        self.req_index += 1
        return { 'appId': self.app_id, 'antiCache': time.time(),
                 'reqIndex': old_req_index, 'viewer': 'web' }

    def _do_request(self, body):
        '''Sends a POST request to AIS and process the response.

        Usually called from :meth:`send_events`.
        '''
        response = self._send_request(body)
        self._process_response(response)

    def _send_request(self, body):
        xml_spec = '<request> <serial>{}</serial>\n{}</request>\n'.format(
            self.serial, body)
        self.serial += 1

        params = self._prepare_url_base()
        data = params.copy()
        data['xml_spec'] = xml_spec

        # WebUIServlet needs charset set in Content-Type. Normal POST requests
        # don't have it, but sendRequestEvent manually sets it, so we do the
        # same.
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        return self.ctx.request_html('/ais/servlets/WebUIServlet',
            method='POST', params=params, data=data, headers=headers)

    def _filter_operations(self, operations):
        return [operation for operation in operations
                if not (operation.method == 'messageBox' and
                        any(pattern in operation.args[0]
                            for pattern in self.ignored_messages))]

    def _process_response(self, soup):
        self.ctx.log('benchmark', 'Begin response frame processing')
        self.last_response_time = time.time()
        operations, updates = parse_response(soup)
        body = soup.body

        for operation in operations:
            self.ctx.log('operation',
                'Received operation {}'.format(operation.method), operation)

        operations = self._filter_operations(operations)

        if operations:
            if self.collector is None:
                raise AISBehaviorError(
                    "AIS did an unexpected operation: {}".format(operations),
                    operations=operations)

            self.collector.extend(operations)

        if updates:
            self.ctx.log('update',
                'Updating {} components'.format(len(updates)), updates)

        for update in updates:
            try:
                dialog = self.dialogs[update.dialog]
            except KeyError:
                raise AISParseError("Dialog %r doesn't exist." %
                    update.dialog) from None

            try:
                component = dialog.components[update.target]
            except KeyError:
                if update.target == "HeaderView":
                    continue   # a mysterious non-existent component
                raise AISParseError("Component %r doesn't exist in %r." %
                    (update.target, update.dialog)) from None

            try:
                method = getattr(component, '_ais_' + update.method)
            except AttributeError:
                raise AISParseError("Method %r of %s is not yet implemented." %
                    (update.method, component.__class__.__name__)) from None

            args = update.args
            if getattr(method, 'wants_body', False):
                args = args + [body]

            method(*args)

        self.ctx.log('benchmark', 'End response frame processing')

    def send_events(self, *events):
        '''Sends the given events to AIS, if AIS is listening to them.

        :param \*events: the events to send.
        '''
        body = ''.join(e.xml for e in events if e.listening)
        if not body: return
        self._do_request('<events>' + body + '</events>' +
                         self.collect_component_changes())

    def send_empty_request(self):
        '''Sends a request without any events to AIS.'''
        self._do_request(self.collect_component_changes())

    def _send_namevalue_request(self, name, value):
        '''Helper function for small requests sent by some operations.
        These requests don't contain any events or component changes.
        '''
        self._do_request(
            '<changedProps><changedProperties><propertyValues><nameValue>' +
            '<name>{}</name><value>{}</value>'.format(name, value) +
            '</nameValue></propertyValues></changedProperties></changedProps>')

    def force_close(self):
        '''Tells the server to close the application.

        Usually, users close applications with the exit button in the main
        dialog. This method disregards open dialogs and just closes everything.
        It also works even if the application is already closed.
        '''
        self.close_all_dialogs()
        self.ctx.log('operation',
            'Sending WebUIKillEvent to {}'.format(self.class_name))
        self._send_request(
            "<events><ev><event class='avc.framework.webui.WebUIKillEvent'/>"
            "</ev></events>\n")

    def collect_component_changes(self):
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

    def is_still_open(self):
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
            self.ctx.log('operation', 'Checking if {} is still open'.format(
                self.class_name))
            try:
                self.send_empty_request()
            except AISApplicationClosedError:
                self.ctx.log('operation', 'Server already closed {}'.format(
                    self.class_name))
                return False
        return True

    def start_app(self, url, params, *, ignored_messages=None):
        '''Opens a new application in response to the startApp
        :class:`Operation`.

        Returns:
            An `(app, ops)` tuple, just like :meth:`open`.
        '''
        url = ('/ais/servlets/WebUIServlet?appClassName={}{}&'
               'antiCache={}').format(url, params, time.time())
        return self.open(self.ctx, url, ignored_messages)

    def open_main_dialog(self, props):
        '''Opens the main dialog in response to the openMainDialog
        :class:`Operation`.

        Returns:
            The opened :class:`aisikl.dialog.Dialog`.
        '''
        return self.open_dialog(props)

    def open_dialog(self, props):
        '''Opens a new dialog in response to the openDialog :class:`Operation`.

        Returns:
            The opened :class:`aisikl.dialog.Dialog`.
        '''
        name = props['id']
        self.ctx.log('operation', 'Opening dialog {} "{}"'.format(
            name, props['title']))

        # Ignore properties that only affect visuals: basedOnTheme, style,
        # isDlgDefaultStyleUsed, x, y, w, h, ra (resizeable), ma (minimizeable),
        # minWidth, minHeight, and forControlOfParent.
        dialog = Dialog(
            name=name, title=props['title'], code=props['code'],
            parent_dialog_name=props.get('parentDlgName'), modal=props['modal'],
            is_main_dialog=props['isMain'], closeable=props['ca'],
            hide_title_bar=props['htb'], app=self)
        self.dialog_stack.append(dialog)
        self.dialogs[name] = dialog

        # The topmost modal dialog will be active. If no modals exist, this
        # dialog will be active.
        modals = [d for d in self.dialog_stack if d.modal]
        self.active_dialog = self.d = modals[-1] if modals else dialog

        url = '/ais/servlets/WebUIServlet?{}&form={}'.format(
            '&'.join('{}={}'.format(k, v)
                     for k, v in self._prepare_url_base().items()),
            name)
        dialog._init(url)

        return dialog

    def refresh_dialog(self, name):
        '''Refreshes a dialog in response to the refreshDialog
        :class:`Operation`.
        '''
        dialog = self.dialogs[name]

        self.ctx.log('operation', 'Refreshing dialog {} "{}"'.format(
            dialog.name, dialog.title))

        url = ('/ais/servlets/WebUIServlet?appId={}&form={}&antiCache={}'.
            format(self.app_id, dialog.name, time.time()))
        dialog._init(url)

    def close_dialog(self, name, is_native=False):
        '''Closes a dialog in response to the closeDialog :class:`Operation`.
        '''
        if is_native:
            raise AISParseError("closeDialog() with isNative is not supported")

        dialog = self.dialogs.get(name)
        if not dialog:
            return

        self.ctx.log('operation', 'Closing dialog {}'.format(name))

        self.dialog_stack.remove(dialog)
        del self.dialogs[name]

        if dialog == self.active_dialog or not self.active_dialog:
            modals = [d for d in self.dialog_stack if d.modal]
            self.active_dialog = self.d = (
                modals or self.dialog_stack or [None])[-1]

    def close_all_dialogs(self):
        '''Closes all dialogs after they have been closed on the server.'''
        if self.dialog_stack:
            self.ctx.log('operation', 'Closing all dialogs')
        self.dialogs.clear()
        self.dialog_stack.clear()
        self.active_dialog = self.d = None

    def confirm_box(self, option_index):
        '''Sends an answer after receiving the confirmBox :class:`~Operation`.

        Possible values of `option_index` are:

        =====  ===========
        Value  Action name
        =====  ===========
            4  Yes to all
            2  Yes
            1  OK
           -1  Cancel
           -2  No
           -4  No to all
        =====  ===========

        Args:
            option_index: webui index of the button to be clicked
        '''
        self.ctx.log('operation', 'Selecting button {} in confirm box'.format(
            option_index))
        self._send_namevalue_request('confirmResult', option_index)

    def abort_box(self, message, title=None):
        '''Waits for AIS in response to the abortBox :class:`~Operation`.'''
        self.ctx.log('operation', 'Waiting for abort box')
        self._send_namevalue_request('confirmResult', -1)

    def shell_exec(self, content_type, file_name, new_window_name, width,
                   height):
        '''Downloads a file in response to the shellExec :class:`Operation`.
        Then sends a request to AIS saying that the shellExec was executed.

        This method only supports the common use of shellExec -- downloading
        files. Technically, shellExec can also run custom JavaScript code. If
        you need that, don't use :meth:`shell_exec`, handle it manually and
        call :meth:`send_shell_exec_result` afterwards.

        Returns:
            The downloaded :class:`requests.Response`.
        '''
        if content_type == 'webui/execCustomFunction':
            raise AISParseError("webui/execCustomFunction is not supported")

        file_name = file_name.rpartition('/')[2]
        url = ('/ais/files/{}?appId={}&contentType={}&antiCache={}&file={}'
            .format(urllib.parse.quote(file_name), self.app_id, content_type,
                    time.time(), urllib.parse.quote(file_name)))

        self.ctx.log('operation', 'Downloading "{}"'.format(file_name))

        response = self.ctx.request_ais(url)

        self.send_shell_exec_result('')

        return response

    def send_shell_exec_result(self, shell_exec_result):
        '''Informs AIS that a shellExec operation was executed.

        Args:
            shell_exec_result: The string value of ``shellExecResult``.
        '''
        self._send_namevalue_request('shellExecResult', shell_exec_result)

    def awaited_start_app(self, ops, ignored_messages=None):
        '''Combines :func:`assert_ops` and :meth:`start_app` in one step.

        If ``ops`` really contains a single startApp :class:`Operation` as
        expected, opens the application. Throws otherwise.
        '''
        assert_ops(ops, 'startApp')
        return self.start_app(*ops[0].args, ignored_messages=ignored_messages)

    def awaited_open_dialog(self, ops):
        '''Combines :func:`assert_ops` and :meth:`open_dialog` in one step.

        If ``ops`` really contains a single openDialog :class:`Operation` as
        expected, opens the new dialog. Throws otherwise.
        '''
        assert_ops(ops, 'openDialog')
        return self.open_dialog(*ops[0].args)

    def awaited_open_main_dialog(self, ops):
        '''Combines :func:`assert_ops` and :meth:`open_main_dialog` in one
        step.

        If ``ops`` really contains a single openMainDialog :class:`Operation`
        as expected, opens the main dialog. Throws otherwise.
        '''
        assert_ops(ops, 'openMainDialog')
        return self.open_main_dialog(*ops[0].args)

    def awaited_refresh_dialog(self, ops):
        '''Combines :func:`assert_ops` and :meth:`refresh_dialog` in one step.

        If ``ops`` really contains a single refreshDialog :class:`Operation` as
        expected, refreshes the dialog. Throws otherwise.
        '''
        assert_ops(ops, 'refreshDialog')
        return self.refresh_dialog(*ops[0].args)

    def awaited_close_dialog(self, ops):
        '''Combines :func:`assert_ops` and :meth:`close_dialog` in one step.

        If ``ops`` really contains a single closeDialog :class:`Operation` as
        expected, closes the dialog. Throws otherwise.
        '''
        assert_ops(ops, 'closeDialog')
        return self.close_dialog(*ops[0].args)

    def awaited_abort_box(self, ops):
        '''Combines :func:`assert_ops` and :meth:`abort_box` in one step.

        If ``ops`` really contains a single abortBox :class:`Operation` as
        expected, waits for the box to close. Throws otherwise.
        '''
        assert_ops(ops, 'abortBox')
        return self.abort_box(*ops[0].args)

    def awaited_shell_exec(self, ops):
        '''Combines :func:`assert_ops` and :meth:`shell_exec` in one step.

        If ``ops`` really contains a single shellExec :class:`Operation` as
        expected, downloads the file. Throws otherwise.
        '''
        assert_ops(ops, 'shellExec')
        return self.shell_exec(*ops[0].args)

    def awaited_close_application(self, ops):
        '''Combines :func:`assert_ops` and :meth:`close_all_dialogs` in one
        step.

        If ``ops`` contains the serverCloseApplication, closeDialog and
        closeApplication operations (which is common when pressing exit buttons
        and such), closes all dialogs and does not send any other requests (the
        server already considers the application closed). Throws otherwise.
        '''
        assert_ops(ops,
                   'serverCloseApplication', 'closeDialog', 'closeApplication')
        self.close_all_dialogs()

def check_connection(context):
    # We used to request /ais/portal/changeTab.do?tab=0, but it switches the
    # user to the old interface. Same with / or /ais/start.do. This should work
    # regardless of old vs new student interface, and preserve the user's
    # preference for next time they log in to AIS directly.

    try:
        # This request returns 200 with empty body if logged in (and strangely
        # also if no JSESSIONID is sent), or 401 if a JSESSIONID is sent but the
        # session is logged out or expired.
        # The header is from https://ais2.uniba.sk/ais/apps/student/sk/main.js
        # (search "accessToken") and from an inline script in /ais/start.do.
        # Let's hope it's stable over time.
        response = context.request_ais(
            '/ais/rest/apps/get-access-token',
            headers={'B5nd8BgAoX': '2llVM1Fl3M'})
        aisauth = response.headers.get('AISAuth')
        if not aisauth:
            raise AISParseError('Missing AISAuth header')

        # This returns empty 200 if logged in or empty 401 if logged out.
        # The first request might be sufficient, this one is just to faithfully
        # recreate what AIS is doing.
        # Future note: If we store the aisauth value for a longer time, we
        # should always check if a response contains a new AISAuth header.
        context.request_ais(
            '/ais/rest/apps/check-session/check-light',
            headers={'AISAuth': aisauth})
    except HTTPError as e:
        if e.response is not None and e.response.status_code == 401:
            raise LoggedOutError('AIS login expired.') from e
        else:
            raise e
