
from collections import namedtuple
from contextlib import contextmanager
import json
import re
import time
from .exceptions import AISParseError, AISBehaviorError
from .dialog import Dialog


Operation = namedtuple('Operation', ('target', 'method', 'args'))
Operation.__doc__ = (
    '''Record of a "big" action done by AIS that isn't handled automatically
    and requires the user's (or in Votr's case, program's) reaction, such as:

    - Opening a new application or browser window
    - Showing a message box or another modal dialog
    - Opening and closing dialogs
    ''')

Update = namedtuple('Update', ('dialog', 'target', 'method', 'args'))
Update.__doc__ = '''Record of AIS calling a setter on some component.'''


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
]
_main_re = re.compile(r'^function main0?\(\) \{$')
_operation_re = re.compile(r'^(webui|dm)\(\)\.(\w+)\((.*)\)$')
_update_re = re.compile(r'^f\(\)\.getEnsuredJSOById\("(\w+)", *(\w+)\)\.(\w+)\((.*)\)$')


def parse_response(soup):
    '''Parse the resultFrame content (the response to a POST request).

    :param soup: the HTML structure.
    :return: an (operations, updates) tuple.
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
            args = json.loads('[' + args_str + ']')
            if method not in known_operations[target]:
                raise AISParseError("Unknown method {}().{}()".format(
                    target, method))
            operations.append(Operation(target, method, args))
            continue

        match = _update_re.match(line)
        if match:
            target, dialog, method, args_str = match.groups()
            args = json.loads('[' + args_str + ']')
            updates.append(Update(dialog, target, method, args))
            continue

        raise AISParseError("Couldn't parse script line: {}".format(line))

    return (operations, updates)


def assert_ops(operations, *expected_methods):
    '''Ensure the list of operations contains the methods we expect.

    This is a helper method you can use after calling collect_operations.

    :param operations: the collected operations.
    :param \*expected_methods: a list of method names.
    '''
    real_methods = [op.method for op in operations]
    expected_methods = list(expected_methods)
    if real_methods != expected_methods:
        raise AISBehaviorError(
            "We expected %r but AIS did something different: %r" %
            (expected_methods, operations))


class Application:
    '''An opened AIS application. (That is, a "browser window".)

    :param ctx: the :class:`~aisikl.context.Context` to use.
    '''

    @classmethod
    def open(cls, ctx, url):
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

    @contextmanager
    def collect_operations(self):
        '''Collect operations done by AIS -- big actions like opening new
        applications, dialogs, browser windows or modal boxes. These usually
        require a reaction from your part, or signify an error of some sort.
        By calling this, you're expressing you expected it to happen. If an
        :class:`Operation` happens but isn't collected, an error is thrown.

        Use it with the ``with`` keyword as a context manager::

            with my_app.collect_operations() as ops:
                my_dialog.someButton.click()

            print(ops[0])   # TODO: replace with better example
        '''
        if self.collector is not None:
            raise Exception("Already inside another collect_operations()")
        self.collector = []
        try:
            yield self.collector
        finally:
            self.collector = None

    def _do_request(self, body):
        '''Send a POST request to AIS and process the response.

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

        return self.ctx.request_html('/ais/servlets/WebUIServlet',
            method='POST', params=params, data=data)

    def _process_response(self, soup):
        operations, updates = parse_response(soup)
        body = soup.body

        if operations:
            if self.collector is None:
                exc = AISBehaviorError(
                    "AIS did an unexpected operation: {}".format(operations))
                exc.operations = operations
                raise exc

            self.collector.extend(operations)

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
        '''Send the given events to AIS, if AIS is listening to them.

        :param \*events: the events to send.
        '''
        body = ''.join(e.xml for e in events if e.listening)
        if not body: return
        self._do_request('<events>' + body + '</events>' +
                         self.collect_component_changes())

    def collect_component_changes(self):
        '''Return the <changedProps> string that goes into POST requests.'''
        app_changes = ''
        if self.dialog_stack:
            app_changes = (
                '<changedProperties><objName>app</objName><propertyValues>\n' +
                '<nameValue><name>activeDlgName</name><value>' +
                self.dialog_stack[-1].name +
                '</value></nameValue>\n' +
                '</propertyValues></changedProperties>\n')

        return ('<changedProps>\n' +
            app_changes +
            ''.join(d.changed_properties() for d in self.dialog_stack) +
            '</changedProps>\n')

    def start_app(self, url, params):
        url = ('/ais/servlets/WebUIServlet?appClassName={}{}&'
               'antiCache={}').format(url, params, time.time())
        return self.open(self.ctx, url)

    def open_main_dialog(self, name, title, code, x, y, min_width, min_height,
                         width, height, resizeable, minimizeable, closeable,
                         hide_title_bar):
        '''Do the dm().openMainDialog() operation and open the main dialog.'''
        # We ignore webui's useDialogFrame, so we just call open_dialog.
        return self.open_dialog(
            name, title, code, None, False, True, 0, 0, width, height,
            resizeable, minimizeable, closeable, hide_title_bar, min_width,
            min_height, None, None, False)

    def open_dialog(self, name, title, code, parent_dialog_name, modal,
                    is_main_dialog, x, y, width, height, resizeable,
                    minimizeable, closeable, hide_title_bar, min_width,
                    min_height, for_control_of_parent, purl, is_native):
        '''Do the dm().openDialog() operation and open a dialog.'''
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

    # TODO: Closing dialogs (from DialogManager)

    def awaited_start_app(self, ops):
        assert_ops(ops, 'startApp')
        return self.start_app(*ops[0].args)

    def awaited_open_dialog(self, ops):
        assert_ops(ops, 'openDialog')
        return self.open_dialog(*ops[0].args)

    def awaited_open_main_dialog(self, ops):
        assert_ops(ops, 'openMainDialog')
        return self.open_main_dialog(*ops[0].args)

