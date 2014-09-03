
from collections import namedtuple
from contextlib import contextmanager
import json
import re
import time
from .exceptions import AISParseError, AISBehaviorError
from .dialog import Dialog


Operation = namedtuple('Operation', ('target', 'method', 'args'))


Update = namedtuple('Update', ('dialog', 'target', 'method', 'args'))


#: The known :class:`Operation` methods.
known_operations = {
    'webui': { 'startApp', 'confirmBox', 'messageBox', 'abortBox',
               'fileUpload', 'fileXUpload', 'editDoc', 'shellExec',
               'showHelp' },
    'dm': { 'openMainDialog', 'openDialog', 'closeDialog' },
}


# Regexes for parsing AIS JavaScript
_onload_re = re.compile(r'^window\.setTimeout\("WebUI_init\(\\"([^"\\]+)\\", \\"ais\\", \\"ais\/webui2\\"\)", 1\)$')
_functions_re = re.compile(r'\nfunction (\w+)')
_var_re = re.compile(r'^var \w+;\s*')
_trycatch_re = re.compile(r'^try {\s*|\s*} *catch *\(e\) *{ *(return;)? *}$')
_multiline_res = [
    re.compile(r'if *\( *dm\(\) *!= *null *\) *{ *\n *dm\(\)\.checkDialogStacksEmpty\(\);? *\n *}'),
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
    re.compile(r'^dm\(\)\.setActiveDialogName\(\'\w+\'\)$'),
    re.compile(r'^\w+\.getDialogJSObject\(\)\.setFocusedComponent\("\w+"\)$'),
]
_main_re = re.compile(r'^function main0?\(\) \{$')
_operation_re = re.compile(r'^(webui|dm)\(\)\.(\w+)\((.*)\)$')
_update_re = re.compile(r'^f\(\)\.getEnsuredJSOById\("(\w+)", *(\w+)\)\.(\w+)\((.*)\)$')


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

    functions = [m.group(1) for m in _functions_re.finditer(script)]
    if ','.join(functions) != 'webui,f,dm,isResponseIdle,main0,main':
        raise AISParseError("Unexpected script in result frame response")

    in_main = False

    for r in _multiline_res:
        script = r.sub('', script)

    for line in script.split('\n'):
        line = line.strip()
        line = _var_re.sub('', line)
        line = _trycatch_re.sub('', line)
        line = line.strip(';')

        if not line: continue
        if any(r.match(line) for r in _useless_res): continue

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
        AISBehaviorError: Raised if the methods don't match.
    '''
    real_methods = [op.method for op in operations]
    expected_methods = list(expected_methods)
    if real_methods != expected_methods:
        raise AISBehaviorError(
            "We expected %r but AIS did something different: %r" %
            (expected_methods, operations))


class Application:
    '''An opened AIS application. (That is, a "browser window".)

    Instances cannot be created directly. Use :meth:`open` if you know the full
    URL (e.g. from the :mod:`~aisikl.portal`), or :meth:`start_app` when
    opening an application from another one.

    Attributes:
        ctx: The :class:`~aisikl.context.Context`.
        dialogs: The dict of open :class:`~aisikl.dialog.Dialog`\ s.
        dialog_stack:
            The ordered list of open :class:`~aisikl.dialog.Dialog`\ s. Its
            last item is the currently active dialog.
    '''

    @classmethod
    def open(cls, ctx, url):
        '''Opens a new application.

        Returns an ``(app, ops)`` tuple containing the new Application instance
        and the initial list of operations caused by the "INIT" event. This
        list must be processed as usual -- see :meth:`collect_operations`. For
        example, if the application should only open a main dialog, use ``dlg =
        app.awaited_open_main_dialog(ops)``. (If the user isn't authorized,
        ``ops`` will probably contain a message box saying so.)

        Args:
            ctx: The :class:`~aisikl.context.Context` to use.
            url: The main app URL. Can be relative to the server root.
        Returns:
            An `(app, ops)` tuple with the new instance and the initial list of
            operations.
        '''
        app = super().__new__(cls)
        ops = app._open(ctx, url)
        return app, ops

    def __init__(self):
        # This is because open() needs to return two values, and __init__ can't
        # change the return value. __new__ could, but we want normal pickling.
        raise Exception(
            "The Application constructor is private, use open() instead")

    def _open(self, ctx, url):
        '''Actually opens the new instance created by :meth:`open`.'''
        self.ctx = ctx
        self.serial = 0
        self.dialogs = {}
        self.dialog_stack = []
        self.collector = None

        match = re.search(r'appClassName=([a-zA-Z0-9_\.]*)', url)
        self.ctx.log('operation', 'Opening application {}'.format(
            match.group(1) if match else '(unknown)'), url)

        app_soup = self.ctx.request_html(url)
        if not app_soup.find(id='webuiProperties'):
            raise AISParseError("AIS2 application didn't open")

        onload = app_soup.body['onload']
        onload_match = _onload_re.match(onload)
        if not onload_match:
            raise AISParseError("Couldn't get app ID from <body> onload")
        self.app_id = onload_match.group(1)

        if app_soup.find(id='initScript').get_text() != '<!---->':
            raise AISParseError("initScript is not supported")

        rq = ("<events><ev><event class='avc.ui.event.AVCComponentEvent'>"
              "<command>INIT</command></event></ev></events>\n")
        with self.collect_operations() as ops:
            self._do_request(rq)
        return ops

    @property
    def active_dialog(self):
        '''The currently active dialog. Equal to `app.dialog_stack[-1]`.'''
        return self.dialog_stack[-1] if self.dialog_stack else None

    d = active_dialog

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
                dlg.someButton.click()

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

        params = { 'appId': self.app_id, 'antiCache': time.time() }
        data = params.copy()
        data['xml_spec'] = xml_spec

        self.ctx.log('http', 'Sending WebUIServlet request', xml_spec)

        # WebUIServlet needs charset set in Content-Type. Normal POST requests
        # don't have it, but request.html manually sets it, so we do the same.
        headers = {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'}
        return self.ctx.request_html('/ais/servlets/WebUIServlet',
            method='POST', params=params, data=data, headers=headers)

    def _process_response(self, soup):
        self.ctx.log('http', 'Received response', str(soup))
        operations, updates = parse_response(soup)
        body = soup.body

        if operations:
            for operation in operations:
                self.ctx.log('operation',
                    'Received operation {}'.format(operation.method),
                    operation)

            if self.collector is None:
                exc = AISBehaviorError(
                    "AIS did an unexpected operation: {}".format(operations))
                exc.operations = operations
                raise exc

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

    def send_events(self, *events):
        '''Sends the given events to AIS, if AIS is listening to them.

        :param \*events: the events to send.
        '''
        body = ''.join(e.xml for e in events if e.listening)
        if not body: return
        self._do_request('<events>' + body + '</events>' +
                         self.collect_component_changes())

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

    def start_app(self, url, params):
        '''Opens a new application in response to the startApp
        :class:`Operation`.

        Returns:
            An `(app, ops)` tuple, just like :meth:`open`.
        '''
        url = ('/ais/servlets/WebUIServlet?appClassName={}{}&'
               'antiCache={}').format(url, params, time.time())
        return self.open(self.ctx, url)

    def open_main_dialog(self, name, title, code, x, y, min_width, min_height,
                         width, height, resizeable, minimizeable, closeable,
                         hide_title_bar):
        '''Opens the main dialog in response to the openMainDialog
        :class:`Operation`.

        Returns:
            The opened :class:`aisikl.dialog.Dialog`.
        '''
        # We ignore webui's useDialogFrame, so we just call open_dialog.
        return self.open_dialog(
            name, title, code, None, False, True, 0, 0, width, height,
            resizeable, minimizeable, closeable, hide_title_bar, min_width,
            min_height, None, None, False)

    def open_dialog(self, name, title, code, parent_dialog_name, modal,
                    is_main_dialog, x, y, width, height, resizeable,
                    minimizeable, closeable, hide_title_bar, min_width,
                    min_height, for_control_of_parent, purl, is_native):
        '''Opens a new dialog in response to the openDialog :class:`Operation`.

        Returns:
            The opened :class:`aisikl.dialog.Dialog`.
        '''
        if is_native:
            # Current theory: isNative probably means the dialog body contains
            # custom HTML instead of Components. We haven't seen one yet.
            # (NativeDialog, i.e. MessageBox and the rest, is something else.)
            raise AISParseError("openDialog() with isNative is not supported")

        if self.dialog_stack and not modal and not is_main_dialog:
            # See webui's openDialog_().
            #
            # Webui's modal dialogs are implemented with DialogStacks. In
            # a stack, only the topmost dialog can be active. But the user can
            # switch between different stacks. A modal dialog only restricts
            # access to others in its own stack.
            #
            # Multiple stacks seem to be uncommon in practice, so we ignore the
            # whole thing for the moment to make the code simpler.
            raise AISParseError("Multiple dialog stacks are not supported yet")

        self.ctx.log('operation', 'Opening dialog {} "{}"'.format(name, title))

        # Ignore arguments that only affect position and size: x, y, width,
        # height, resizeable, min_width, min_height, and for_control_of_parent.
        # (And minimizeable, which actually isn't used in webui at all.)
        dialog = Dialog(name, title, code, parent_dialog_name, modal,
                        is_main_dialog, closeable, hide_title_bar, self)
        self.dialog_stack.append(dialog)
        self.dialogs[name] = dialog

        url = purl or ('/ais/servlets/WebUIServlet?appId={}&form={}&'
                       'antiCache={}').format(self.app_id, name, time.time())
        dialog._init(url)

        return dialog

    def close_dialog(self, name, is_native=False):
        if is_native:
            raise AISParseError("closeDialog() with isNative is not supported")

        dialog = self.dialogs.get(name)
        if not dialog:
            return True
        if dialog != self.active_dialog:
            return False

        self.ctx.log('operation', 'Closing dialog {}'.format(name))

        self.dialog_stack.pop()
        del self.dialogs[name]
        return True

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
        self._do_request(
            '<changedProps><changedProperties><propertyValues>' +
            '<nameValue><name>confirmResult</name>' +
            '<value>' + str(option_index) + '</value>' +
            '</nameValue></propertyValues></changedProperties></changedProps>'
        )

    def awaited_start_app(self, ops):
        '''Combines :func:`assert_ops` and :meth:`start_app` in one step.

        If ``ops`` really contains a single startApp :class:`Operation` as
        expected, opens the application. Throws otherwise.
        '''
        assert_ops(ops, 'startApp')
        return self.start_app(*ops[0].args)

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

    def awaited_close_dialog(self, ops):
        '''Combines :func:`assert_ops` and :meth:`close_dialog` in one step.

        If ``ops`` really contains a single closeDialog :class:`Operation` as
        expected, closes the dialog. Throws otherwise.
        '''
        assert_ops(ops, 'closeDialog')
        return self.close_dialog(*ops[0].args)

