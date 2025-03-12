import base64
from collections import deque, namedtuple
import json
import re
import time
from types import SimpleNamespace
from urllib.parse import urljoin
from requests import HTTPError, Session
from aisikl.context import Logger


LogEntry = namedtuple('LogEntry', ('timestamp', 'type', 'message', 'data'))


_IGNORE_DETAILS = '[{_IGNORE_DETAILS}]'


class MockRunner:
    FAKE_AIS_URL = 'https://ais.invalid/'
    FAKE_REST_URL = 'https://rest.invalid/'

    def run(self, body, expected_logs, *, print, old_log, fail_fast):
        self.expected_logs = deque(_preprocess_expected_logs(
            expected_logs, old_log))
        self.responses = deque(_prepare_http_responses(self.expected_logs))
        self.print = print
        self.old_log = old_log
        self.fail_fast = fail_fast
        self.synced = True
        self.ok = True
        self.now = self.expected_logs[0].timestamp

        original_time_time = time.time
        original_send_log = Logger.send_log
        original_session_request = Session.request

        try:
            time.time = self._mock_time
            Logger.send_log = self._mock_send_log
            Session.request = self._mock_request
            body()
        except _FailFast:
            count = len(self.expected_logs)
            if count:
                self.print(
                    f'INFO: skipping remaining {count} expected log entries')
        finally:
            time.time = original_time_time
            Logger.send_log = original_send_log
            Session.request = original_session_request

        if self.ok and self.expected_logs:
            self.ok = False
            self.print('ERROR: log ended too early')
            self.print(f'... expected: {json.dumps(self.expected_logs[0])}')

        return self.ok

    def _mock_time(self):
        return self.now

    def _mock_request(self, *args, **kwargs):
        # This doesn't check if the request url or any other args match. It just
        # returns the original responses in the given order.
        # This can lead to confusing output if we diverge too much from the
        # original log. In general only the first reported error/warning can be
        # fully trusted.
        return self.responses.popleft()()

    def _mock_send_log(self, atimestamp, atype, amessage, adata):
        self._mock_send_log_match(atimestamp, atype, amessage, adata)

        if self.fail_fast and not self.ok:
            raise _FailFast()

        if self.expected_logs:
            self.now = self.expected_logs[0].timestamp

            # Handle BrokenPipeError. If the original user's HTTP connection
            # broke, Votr usually finds out when Logger.log() calls send_log()
            # after it wrote to disk, and it raises BrokenPipeError. So if the
            # log file contains a normal entry followed by "... failed with
            # BrokenPipeError", we assume the send_log() call raised it, and
            # raise one too.
            if self.expected_logs[0].message.endswith(
                    ' failed with BrokenPipeError'):
                raise BrokenPipeError(
                    re.search(
                        r'\nBrokenPipeError: (.*\S)\n*$',
                        self.expected_logs[0].data,
                    ).group(1))

    def _mock_send_log_match(self, atimestamp, atype, amessage, adata):
        if atype == 'benchmark':
            return

        ajson = json.dumps([atimestamp, atype, amessage, adata])

        if not self.synced:
            self.print(f'INFO: after desync: {ajson}')
            return

        if not self.expected_logs:
            self.print('ERROR: log continues after expected end')
            self.print(f'... actual:   {ajson}')
            self.ok = False
            self.synced = False
            return

        etimestamp, etype, emessage, edata = self.expected_logs[0]
        ejson = json.dumps([etimestamp, etype, emessage, edata])

        # This log call was added in ddcb88f15a (2025-02-28).
        # Hack: Assume every tree component id ends with "Tree".
        if (
            self.old_log and
            atype == 'action' and
            amessage.endswith('Tree') and
            etype == 'http'
        ):
            self.print(f'INFO: ignoring tree action log: {ajson}')
            return

        # This log call was added in 188d762a8a (2025-03-12).
        if (
            self.old_log and
            atype == 'operation' and
            amessage == 'Closing pooled application' and
            etype == 'operation' and
            emessage == 'Closing all dialogs'
        ):
            self.print(f'INFO: ignoring pool log: {ajson}')
            return

        self.expected_logs.popleft()

        def fail(message, *, desync):
            self.ok = False
            if desync:
                self.synced = False
            hint = ''.join(
                ('.' if ech == ach else '^') for ech, ach in zip(ejson, ajson))
            self.print(('ERROR: ' if desync else 'WARNING: ') + message)
            self.print(f'... expected: {ejson}')
            self.print(f'... actual:   {ajson}')
            self.print(f'... hint:     {hint}')

        if atimestamp != etimestamp:
            fail('wrong timestamp', desync=True)
            return

        if atype != etype:
            fail('wrong type', desync=True)
            return

        if amessage != emessage:
            fail('wrong message', desync=False)
            return

        # Check perfect equality of Python values.
        # (Both "match perfect" and "match json" are perfectly acceptable. They
        # are distinguished here just for fun.)
        if adata == edata:
            self.print(f'INFO: match perfect: {ajson}')
            return

        # Check equality after JSON serialization. Happens with:
        # - "Loaded {} rows in {}" because of dict with int keys becoming str
        # - "Updating {} components" because of namedtuples
        # - "Found {} columns in {}" because of namedtuples
        if ajson == ejson:
            self.print(f'INFO: match json: {ajson}')
            return

        # For some exceptions it's hard to mock the exact details including
        # the chain.
        if (
            ' failed with ' in amessage and
            (_IGNORE_DETAILS in adata or _IGNORE_DETAILS in edata)
        ):
            self.print(f'INFO: match exception ignoring details: {ajson}')
            return

        # Smooth away some known minor differences.
        # Even if they still don't match, show canonicalized data in the error.
        ajson = _canonicalize(ajson, self.old_log)
        ejson = _canonicalize(ejson, self.old_log)
        if ajson == ejson:
            self.print(f'INFO: match canonical: {ajson}')
            return

        fail('wrong data', desync=False)


def _preprocess_expected_logs(entries, old_log):
    skip = 0

    for i in range(len(entries)):
        # Match the old pre-SAML aisikl.app.check_connection() implementation.
        # But not aisikl.porta.get_modules(), which requests the same URL.
        if (
            skip == 0 and
            old_log and
            entries[i].type == 'http' and
            entries[i].message == 'Requesting GET /ais/portal/changeTab.do' and
            not (i and entries[i-1].message == 'Opening main menu')
        ):
            url1 = '/ais/rest/apps/get-access-token'
            yield LogEntry(
                timestamp=entries[i].timestamp,
                type='http',
                message=f'Requesting GET {url1}',
                data=[url1, None],
            )

            if not (
                i+1 < len(entries) and
                entries[i+1].type == 'http' and
                entries[i+1].message == 'Received response'
            ):
                skip = 1
            elif (
                i+2 < len(entries) and
                entries[i+2].message.endswith(' failed with LoggedOutError')
            ):
                skip = 3
                yield LogEntry(
                    timestamp=entries[i+2].timestamp,
                    type=entries[i+2].type,
                    message=entries[i+2].message,
                    data=('\nrequests.exceptions.HTTPError: 401 fake\n' +
                        _IGNORE_DETAILS),
                )
            else:
                skip = 2
                yield LogEntry(
                    timestamp=entries[i+1].timestamp,
                    type='http',
                    message='Received response (binary data)',
                    data=None,
                )
                url2 = '/ais/rest/apps/check-session/check-light'
                yield LogEntry(
                    timestamp=entries[i+1].timestamp,
                    type='http',
                    message=f'Requesting GET {url2}',
                    data=[url2, None],
                )
                yield LogEntry(
                    timestamp=entries[i+1].timestamp,
                    type='http',
                    message='Received response (binary data)',
                    data=None,
                )

        if skip:
            skip -= 1
            continue

        yield entries[i]


def _prepare_http_responses(entries):
    for i in range(1, len(entries)):
        responder = _prepare_http_response(
            entries[i - 1], entries[i], entries[-1])
        if responder:
            yield responder


def _prepare_http_response(request_entry, response_entry, final_entry):
    # Match normal successful text responses for Context.request_ais() or
    # Context.request_json().
    if (
        request_entry.type == 'http' and
        request_entry.message.startswith('Requesting ') and
        response_entry.type == 'http' and
        response_entry.message == 'Received response'
    ):
        return lambda: SimpleNamespace(
            # This is only used when request_ais() checks if
            # response.headers.get('content-type', '').startswith('text').
            headers={ 'content-type': 'text/fake' },
            text=response_entry.data,
            raise_for_status=lambda: None,
            # This is only used when request_json() checks if
            # response.url.startswith(self.rest_url) to see if login expired.
            # Hack: Assume that JSON is logged in and HTML is logged out.
            url=(MockRunner.FAKE_REST_URL if response_entry.data.startswith('{')
                else ''),
        )

    # Match successful binary responses for aisikl.app.check_connection().
    if (
        request_entry.type == 'http' and
        request_entry.message in (
            'Requesting GET /ais/rest/apps/get-access-token',
            'Requesting GET /ais/rest/apps/check-session/check-light',
        ) and
        response_entry.type == 'http' and
        response_entry.message == 'Received response (binary data)'
    ):
        return lambda: SimpleNamespace(
            # check_connection() only requires that this header is not empty.
            headers={ 'AISAuth': 'fake' },
            text=None,
            raise_for_status=lambda: None,
            # check_connection() does not try to read `content`.
        )

    # Match successful binary responses for PDF files in get_informacny_list().
    # Hack: Context.request_ais() doesn't log the response, but we can find it
    # in the RPC return value.
    if (
        request_entry.type == 'http' and
        request_entry.message.startswith('Requesting GET /ais/files/') and
        response_entry.type == 'http' and
        response_entry.message == 'Received response (binary data)' and
        final_entry.type == 'rpc' and
        final_entry.message == 'RPC get_informacny_list finished'
    ):
        return lambda: SimpleNamespace(
            headers={},
            text=None,
            content=base64.b64decode(final_entry.data),
            raise_for_status=lambda: None,
        )

    # Hack: For other binary responses the content most likely doesn't matter.
    # (E.g. if get_informacny_list failed with BrokenPipeError or similar.)
    if response_entry.message == 'Received response (binary data)':
        return lambda: SimpleNamespace(
            headers={},
            text=None,
            content=b'fake_binary_response',
            raise_for_status=lambda: None,
        )

    # Match HTTPError for Context.request_ais() or Context.request_json().
    # They call raise_for_status() directly, before logging the response, so
    # "Requesting ..." is directly followed by "... failed with ...".
    # The HTTPError may cause another exception, e.g. in check_connection().
    if (
        request_entry.type == 'http' and
        request_entry.message.startswith('Requesting ') and
        response_entry is final_entry and
        ' failed with ' in final_entry.message and
        (m := re.search(r'\nrequests.exceptions.HTTPError: ((\d+) [^\n]+)',
            final_entry.data))
    ):
        error_message = m.group(1)
        status_code = int(m.group(2))
        def raise_for_status():
            # check_connection() needs the response attribute.
            raise HTTPError(error_message, response=error_response)
        error_response = SimpleNamespace(
            # check_connection() needs the status_code attribute.
            status_code=status_code,
            raise_for_status=raise_for_status,
        )
        return lambda: error_response

    # Match ConnectionError or SSLError for Context.request_ais() or
    # Context.request_json(). They are raised directly from Session.request(),
    # not raise_for_status(). The traceback contains a chain of causes. Instead
    # of faithfully replicating it, we ignore it in _mock_send_log_match().
    if (
        request_entry.type == 'http' and
        request_entry.message.startswith('Requesting ') and
        response_entry is final_entry and
        final_entry.message.endswith(
            (' failed with ConnectionError', ' failed with SSLError'))
    ):
        def raise_error():
            if final_entry.message.endswith(' failed with ConnectionError'):
                raise ConnectionError(_IGNORE_DETAILS)
            else:
                raise SSLError(_IGNORE_DETAILS)
        return raise_error

    # Match text responses for fladgejt.login._send_request().
    # _send_request() logs the response before calling raise_for_status(), so
    # this matches both successes and HTTP errors.
    if (
        request_entry.type == 'http' and
        (m1 := re.match(r'^Requesting \w+ (\S+)$', request_entry.message)) and
        (m2 := re.match(r'^Received HTTP (\d+) response$',
            response_entry.message))
    ):
        url = m1.group(1)
        status_code = int(m2.group(1))

        # Hack: This response log format was meant for human consumption.
        # Hack: The real headers dict is case insensitive. This assumes that
        # login.py always uses lowercase when reading.
        headers_str, _, body = response_entry.data.partition('\n---\n')
        headers_list = [line.split(': ') for line in headers_str.split('\n')]
        headers_dict = { k.lower(): v for k, v in headers_list }

        def raise_for_status():
            if status_code >= 400:
                # Hack: The log contains the HTTP status code, but not status
                # text, so we must extract it from the final entry.
                error_match = re.search(
                    r'(^|\n)requests.exceptions.HTTPError: (\d+ [^\n]+)',
                    final_entry.data)
                raise HTTPError(error_match.group(2))
        return lambda: SimpleNamespace(
            status_code=status_code,
            headers=headers_dict,
            text=body,
            raise_for_status=raise_for_status,

            # _send_request() reads response.content for responses without
            # 'content-type'.
            content=body.encode(),

            # _redact_response() and _send_request_chain() read
            # response.is_redirect. FYI: the real Response.is_redirect also
            # checks if 'location' is present.
            is_redirect=(status_code in (301, 302, 303, 307, 308)),

            # _redact_response() calls response.raw.headers.items() for logging.
            raw=SimpleNamespace(
                headers=SimpleNamespace(
                    items=lambda: headers_list,
                ),
            ),

            # _send_request_chain() reads response.url.
            url=url,

            # _send_request_chain() reads response.next.url. This implementation
            # might not perfectly match real Requests, but it's good enough.
            next=SimpleNamespace(
                url=urljoin(url, headers_dict.get('location')),
            ),
        )


def _canonicalize(jsonstr, old_log):
    # json.dumps + json.loads also implicitly creates a deep copy so we can
    # modify `data` without affecting the original log() argument.
    timestamp, type, message, data = json.loads(jsonstr)

    # For exceptions, compare messages but ignore tracebacks.
    if ' failed with ' in message and isinstance(data, str):
        data = re.sub(
            r'(^|\n)(Traceback [^\n]+)(\n  [^\n]+)+',
            r'\1\2\n  [traceback redacted]', data)

    # For GET requests, redact the antiCache query string parameter.
    # Votr uses time.time() as the value.
    def url_remove_anticache(s):
        return re.sub(r'(&antiCache=)\d+\.\d+', r'\1[antiCache redacted]', s)
    if message.startswith('Requesting GET '):
        data[0] = url_remove_anticache(data[0])
    if message.startswith('Opening application '):
        data = url_remove_anticache(data)

    if message == 'Requesting POST /ais/servlets/WebUIServlet':
        # For POST requests, redact the antiCache POST parameter.
        # Votr uses time.time() as the value.
        data[1]['antiCache'] = '[antiCache redacted]'

        if old_log:
            # The order of <embObjChProps> and <editedCells> was random until
            # 1a4eb12115 (2025-03-07).
            data[1]['xml_spec'] = _sort_xml(
                data[1]['xml_spec'], 'embObjChProps', 'changedProperties')
            data[1]['xml_spec'] = _sort_xml(
                data[1]['xml_spec'], 'editedCells', 'cell')

    # This log call was changed in 1a4eb12115 (2025-03-07).
    if old_log and message == 'Detected a local storage page':
        data = '[local storage page redacted]'

    # hodn_key was removed in 5bd5624070 (2023-01-14).
    if old_log and message in (
        'RPC get_hodnotenia finished',
        'RPC get_prehlad_kreditov finished',
    ):
        for hodnotenie in data[0]:
            hodnotenie['hodn_key'] = '[hodn_key redacted]'

    return json.dumps([timestamp, type, message, data])


def _sort_xml(xml_spec, parent, item):
    pattern1 = r'(<{p}>\n*)(<{i}[ >].*</{i}>)(\n*</{p}>)'.format(
        p=re.escape(parent), i=re.escape(item))
    pattern2 = r'(?=<{i}[ >])'.format(i=re.escape(item))
    def replacer(m):
        group2 = ''.join(sorted(re.split(pattern2, m.group(2))))
        return f'{m.group(1)}[xml sorted]{group2}[/xml sorted]{m.group(3)}'
    return re.sub(pattern1, replacer, xml_spec, flags=re.DOTALL)


class SSLError(Exception): pass
class ConnectionError(Exception): pass
class _FailFast(BaseException): pass
