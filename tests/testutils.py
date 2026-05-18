# pyright: reportUninitializedInstanceVariable=none

import argparse
import base64
from collections import deque
import contextlib
from httpx2 import Headers, Request, Response
import json
import os
import pathlib
import re
import sys
import time
import traceback
import trio
from typing import Any, NamedTuple, NotRequired, TYPE_CHECKING, TypedDict, cast
from urllib.parse import urljoin
from aisikl.context import Context, Logger
from aisikl.typeutils import ct, nn
from fladgejt.login import ParamsDictSamlPassword, ServerDict, create_client
from fladgejt.webui import WebuiClient

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable, Sequence
    from fladgejt.base import BaseClient


class LogEntry(NamedTuple):
    timestamp: float
    type: str
    message: str
    data: object


class HttpResponseData(TypedDict):
    status_code: int
    reason_phrase: str
    headers: list[list[str]]
    body: NotRequired[str]


_IGNORE_DETAILS = '[{_IGNORE_DETAILS}]'


class MockRunner:
    FAKE_AIS_URL = 'https://ais.invalid/'
    FAKE_REST_URL = 'https://rest.invalid/'

    async def run(
        self,
        body: Callable[[], Awaitable[None]],
        expected_logs: Sequence[LogEntry],
        *,
        print: Callable[[str], None],
        old_log: bool,
        fail_fast: bool,
    ) -> bool:
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
        original_request_http = Context.request_http

        try:
            time.time = self._mock_time
            Logger.send_log = self._mock_send_log
            Context.request_http = self._mock_request_http  # pyrefly: ignore [bad-assignment] # pyright: ignore [reportAttributeAccessIssue]
            await body()
        except _FailFast:
            count = len(self.expected_logs)
            if count:
                self.print(
                    f'INFO: skipping remaining {count} expected log entries')
        finally:
            time.time = original_time_time
            Logger.send_log = original_send_log
            Context.request_http = original_request_http

        if self.ok and self.expected_logs:
            self.ok = False
            self.print('ERROR: log ended too early')
            self.print(f'... expected: {json.dumps(self.expected_logs[0])}')

        return self.ok

    def _mock_time(self) -> float:
        return self.now

    async def _mock_request_http(self, *args: object, **kwargs: object) -> object:
        # This doesn't check if the request url or any other args match. It just
        # returns the original responses in the given order.
        # This can lead to confusing output if we diverge too much from the
        # original log. In general only the first reported error/warning can be
        # fully trusted.
        return self.responses.popleft()()

    async def _mock_send_log(
        self, atimestamp: float, atype: str, amessage: str, adata: object,
    ) -> None:
        self._mock_send_log_match(atimestamp, atype, amessage, adata)

        if self.fail_fast and not self.ok:
            raise _FailFast()

        if self.expected_logs:
            self.now = self.expected_logs[0].timestamp

            # Handle Cancelled.
            #
            # Timing note: The real Cancelled may be raised by almost any async
            # function. A given log file tells us that it happened after the
            # last successful log line was written to disk, and before the next
            # one would have been written. MockRunner doesn't try to precisely
            # replicate the timing by parsing the traceback, or such. It always
            # raises a fake Cancelled as soon as possible: at the end of the
            # last successful send_log() call. That should, by definition,
            # produce the same log sequence.
            if self.expected_logs[0].message.endswith(' failed with Cancelled'):
                raise Cancelled(
                    nn(re.search(
                        r'\ntrio.Cancelled: (.*\S)\n*$',
                        ct(str, self.expected_logs[0].data),
                    )).group(1))

            # BrokenPipeError was raised instead of Cancelled before the Trio
            # migration (2026-10-ish).
            if self.old_log and self.expected_logs[0].message.endswith(
                    ' failed with BrokenPipeError'):
                raise BrokenPipeError(
                    nn(re.search(
                        r'\nBrokenPipeError: (.*\S)\n*$',
                        ct(str, self.expected_logs[0].data),
                    )).group(1))

    def _mock_send_log_match(
        self, atimestamp: float, atype: str, amessage: str, adata: object,
    ) -> None:
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

        def fail(message: str, *, desync: bool) -> None:
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
        if ' failed with ' in amessage and (
            _IGNORE_DETAILS in ct(str, adata) or
            _IGNORE_DETAILS in ct(str, edata)
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


def _preprocess_expected_logs(
        entries: Sequence[LogEntry], old_log: bool) -> Iterable[LogEntry]:
    skip = 0

    for i in range(len(entries)):
        if skip:
            skip -= 1
            continue

        # Match the old pre-SAML (2024-12-21, 9ca91c73) implementation of
        # aisikl.app.check_connection().
        # But not aisikl.portal.get_modules(), which requests the same URL.
        if (
            old_log and
            entries[i].type == 'http' and
            entries[i].message == 'Requesting GET /ais/portal/changeTab.do' and
            not (i and entries[i-1].message == 'Opening main menu')
        ):
            url1 = '/ais/apps/student/sk/main.js'
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
                # Next entry is probably a network error.
                continue
            elif (
                i+2 < len(entries) and
                entries[i+2].message.endswith(' failed with LoggedOutError')
            ):
                # Originally it was a 200 response without a username element,
                # meaning the user is logged out. Replace with network error.
                yield LogEntry(
                    timestamp=entries[i+1].timestamp,
                    type='http',
                    message='Received response',
                    data=HttpResponseData(
                        status_code=401,
                        reason_phrase=_IGNORE_DETAILS,
                        headers=[],
                    ),
                )
                # Skip the original "Received response", but keep the
                # "... failed with LoggedOutError" entry.
                skip = 1
                continue
            else:
                # The connection check was a success.
                yield LogEntry(
                    timestamp=entries[i+1].timestamp,
                    type='http',
                    message='Received response',
                    data=HttpResponseData(
                        status_code=200,
                        reason_phrase='',
                        headers=[],
                    ),
                )
                url2 = '/ais/rest/apps/get-access-token'
                yield LogEntry(
                    timestamp=entries[i+1].timestamp,
                    type='http',
                    message=f'Requesting GET {url2}',
                    data=[url2, None],
                )
                yield LogEntry(
                    timestamp=entries[i+1].timestamp,
                    type='http',
                    message='Received response',
                    data=HttpResponseData(
                        status_code=200,
                        reason_phrase='',
                        headers=[['aisauth', 'fake']],
                    ),
                )
                url3 = '/ais/rest/apps/check-session/check-light'
                yield LogEntry(
                    timestamp=entries[i+1].timestamp,
                    type='http',
                    message=f'Requesting GET {url3}',
                    data=[url3, None],
                )
                yield LogEntry(
                    timestamp=entries[i+1].timestamp,
                    type='http',
                    message='Received response',
                    data=HttpResponseData(
                        status_code=200,
                        reason_phrase='',
                        headers=[],
                    ),
                )
                # Skip the original "Received response" entry.
                skip = 1
                continue

        # Match `requests`-based (before 2026-09-ish) responses for
        # fladgejt.login._send_request().
        if (
            old_log and
            entries[i].type == 'http' and
            (m := re.fullmatch(r'Received HTTP (\d+) response',
                entries[i].message))
        ):
            headers_str, sep, body = ct(str, entries[i].data).partition('\n---\n')
            headers = [line.split(': ') for line in headers_str.split('\n')]
            headers = [[k.lower(), v] for k, v in headers]
            if i and '/ais/sso/samlsso' in entries[i-1].message:
                # Hack: This fake header is added in fladgejt/login.py, but
                # previously it wasn't added to the response log.
                headers.append(['content-type', 'text/html; charset=UTF-8'])
            data = HttpResponseData(
                status_code=int(m.group(1)),
                # Hack: reason_phrase is displayed in raise_for_status(). Use
                # that to ignore differences in the raised message.
                reason_phrase=_IGNORE_DETAILS,
                headers=headers,
            )
            if sep: data['body'] = body
            yield LogEntry(
                timestamp=entries[i].timestamp,
                type='http',
                message='Received response',
                data=data,
            )
            continue

        # Match `requests`-based (before 2026-09-ish) HTTP status errors for
        # fladgejt.login._send_request(). In this case, we already logged the
        # response before raise_for_status(), but the exception has changed.
        if (
            old_log and
            i and
            entries[i] is entries[-1] and
            entries[i].message == 'Login failed with HTTPError' and
            re.fullmatch(r'Received HTTP \d+ response', entries[i-1].message)
        ):
            yield LogEntry(
                timestamp=entries[i].timestamp,
                type=entries[i].type,
                message='Login failed with HTTPStatusError',
                # No need to change data. It already contains _IGNORE_DETAILS
                # because of the reason_phrase edit above.
                data=entries[i].data,
            )
            continue

        # Match `requests`-based (before 2026-09-ish) expired REST logins in
        # Context.request_json().
        if (
            old_log and
            entries[i].type == 'http' and
            entries[i].message == 'Received response' and
            isinstance((d1 := entries[i].data), str) and
            'login.uniba.sk' in d1 and  # some Cosign error page
            isinstance((d2 := entries[-1].data), str) and
            'REST login expired' in d2
        ):
            yield LogEntry(
                timestamp=entries[i].timestamp,
                type=entries[i].type,
                message='Received response',
                data=HttpResponseData(
                    status_code=303,
                    reason_phrase='',
                    headers=[['location', '/fake']],
                ),
            )
            continue

        # Match `requests`-based (before 2026-09-ish) successful text responses
        # for Context.request_ais() and Context.request_json().
        if (
            old_log and
            entries[i].type == 'http' and
            entries[i].message == 'Received response' and
            isinstance((body := entries[i].data), str)
        ):
            yield LogEntry(
                timestamp=entries[i].timestamp,
                type=entries[i].type,
                message=entries[i].message,
                data=HttpResponseData(
                    status_code=200,
                    reason_phrase='',
                    # This is only used when request_ais() checks if
                    # response.headers.get('content-type', '').startswith('text').
                    headers=[['content-type', 'text/fake']],
                    body=body,
                ),
            )
            continue

        # Match `requests`-based (before 2026-09-ish) successful binary
        # responses for Context.request_ais(). They will be processed further in
        # _prepare_http_response().
        if (
            old_log and
            entries[i].type == 'http' and
            entries[i].message == 'Received response (binary data)' and
            entries[i].data is None
        ):
            yield LogEntry(
                timestamp=entries[i].timestamp,
                type='http',
                message='Received response',
                data=HttpResponseData(
                    status_code=200,
                    reason_phrase='',
                    # Used in aisikl.app.check_connection().
                    headers=[['aisauth', 'fake']],
                ),
            )
            continue

        # Match `requests`-based (before 2026-09-ish) 401 errors in
        # check_connection() leading to LoggedOutError('AIS login expired.').
        if (
            old_log and
            entries[i] is entries[-1] and
            ' failed with ' in entries[i].message and
            'AIS login expired.' in ct(str, entries[i].data) and
            'requests.exceptions.HTTPError' in ct(str, entries[i].data)
        ):
            yield LogEntry(
                timestamp=entries[i].timestamp,
                type='http',
                message='Received response',
                data=HttpResponseData(
                    status_code=401,
                    reason_phrase=_IGNORE_DETAILS,
                    headers=[],
                ),
            )
            yield entries[i]
            continue

        # Match AISBehaviorError messages that changed in the Operation refactor
        # (2026-10-ish).
        if (
            old_log and
            entries[i].message.endswith(' failed with AISBehaviorError') and
            ("Operation(target='" in ct(str, entries[i].data) or
            "We expected ['" in ct(str, entries[i].data))
        ):
            yield LogEntry(
                timestamp=entries[i].timestamp,
                type=entries[i].type,
                message=entries[i].message,
                data=_IGNORE_DETAILS,
            )
            continue

        # openMainDialog was removed in the Operation refactor (2026-10-ish).
        if (
            old_log and
            entries[i].message == 'Received operation openMainDialog'
        ):
            yield LogEntry(
                timestamp=entries[i].timestamp,
                type=entries[i].type,
                message='Received operation openDialog',
                data=[ct(list, entries[i].data)[0], 'openDialog', ct(list, entries[i].data)[2]],
            )
            continue

        yield entries[i]


def _prepare_http_responses(
        entries: Sequence[LogEntry]) -> Iterable[Callable[[], object]]:
    for i in range(1, len(entries)):
        responder = _prepare_http_response(
            entries[i - 1], entries[i], entries[-1])
        if responder:
            yield responder


def _prepare_http_response(
        request_entry: LogEntry,
        response_entry: LogEntry,
        final_entry: LogEntry,
) -> Callable[[], object] | None:
    # Match successfully-received responses for Context.request_ais(),
    # Context.request_json(), and fladgejt.login._send_request().
    if (
        request_entry.type == 'http' and
        request_entry.message.startswith('Requesting ') and
        response_entry.type == 'http' and
        response_entry.message == 'Received response' and
        isinstance(response_entry.data, dict)
    ):
        _, method, url = request_entry.message.split(' ')
        # url can be relative, but close enough!

        response_data = cast('HttpResponseData',
            cast('object', response_entry.data))

        content = None
        text = None
        if 'body' in response_data:
            # If it's a text response and its body was logged, just use it.
            text = response_data['body']
        elif url == '/ais/apps/student/sk/main.js':
            # This is requested in aisikl.app.check_connection(). The real file
            # is freaking huge, but we only look for this fragment.
            text = 'retrieveAccessToken() { setRequestHeader("foo", "bar"); }'
        elif (
            url.startswith('/ais/files') and
            final_entry.message == 'RPC get_informacny_list finished'
        ):
            # For PDF files in get_informacny_list(), extract the content from
            # the RPC return value.
            content = base64.b64decode(ct(str, final_entry.data))
        else:
            # In other cases, e.g. redirect responses in fladgejt.login, or
            # Cancelled in get_informacny_list, the body shouldn't matter.
            text = ''

        response = Response(
            status_code=response_data['status_code'],
            extensions=dict(
                # For matching the raised message in raise_for_status().
                reason_phrase=response_data['reason_phrase'].encode(),
            ),
            text=text,
            content=content,
            request=Request(method=method, url=url),
        )

        # Set headers afterwards. If 'Content-Encoding' is given to Response
        # constructor, it affects how `content` is interpreted. :C
        response.headers = Headers(
            [(k, v) for k, v in response_data['headers']])

        if response.has_redirect_location:
            response.next_request = Request(
                # Hack: assume the next request is GET.
                method='GET',
                url=urljoin(url, response.headers['location'],
            ))

        return lambda: response

    # Match network errors. The traceback contains a chain of causes. Instead
    # of faithfully replicating it, we ignore it in _mock_send_log_match().
    #
    # Also deal with old exceptions raised by `requests` (before 2026-09-ish).
    # Old HTTP status errors, which used to be raised before the response was
    # logged, are also treated as if they were network errors.
    if (
        request_entry.type == 'http' and
        request_entry.message.startswith('Requesting ') and
        response_entry is final_entry and
        ' failed with ' in final_entry.message and
        (error_class := HTTP_ERRORS.get(final_entry.message.split()[-1]))
    ):
        def raise_error() -> None:
            raise error_class(_IGNORE_DETAILS)
        return raise_error


def _canonicalize(jsonstr: str, old_log: bool) -> str:
    # json.dumps + json.loads also implicitly creates a deep copy so we can
    # modify `data` without affecting the original log() argument.
    data: Any
    timestamp, type, message, data = json.loads(jsonstr)

    # For exceptions, compare messages but ignore tracebacks.
    if ' failed with ' in message and isinstance(data, str):
        data = re.sub(
            r'(^|\n)(Traceback [^\n]+)(\n  [^\n]+)+',
            r'\1\2\n  [traceback redacted]', data)

    # For GET requests, redact the antiCache query string parameter.
    # Votr uses time.time() as the value.
    def url_remove_anticache(s: str) -> str:
        return re.sub(r'(&antiCache=)\d+\.\d+', r'\1[antiCache redacted]', s)
    if message.startswith('Requesting GET '):
        data[0] = url_remove_anticache(data[0])
    if message.startswith('Opening application '):
        data = url_remove_anticache(data)

    if message == 'Requesting POST /ais/servlets/WebUIServlet':
        # For POST requests, redact the antiCache GET and POST parameters.
        # Votr uses time.time() as the value.
        data[0] = url_remove_anticache(data[0])
        data[1]['antiCache'] = '[antiCache redacted]'

        if old_log:
            # The order of <embObjChProps> and <editedCells> was random until
            # 1a4eb12115 (2025-03-07).
            data[1]['xml_spec'] = _sort_xml(
                data[1]['xml_spec'], 'embObjChProps', 'changedProperties')
            data[1]['xml_spec'] = _sort_xml(
                data[1]['xml_spec'], 'editedCells', 'cell')

            # URL parameters were not logged until httpx (2026-09-ish).
            data[0] = data[0].partition('?')[0]

            # reqIndex was int until httpx (2026-09-ish).
            data[1]['reqIndex'] = str(data[1]['reqIndex'])

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


def _sort_xml(xml_spec: str, parent: str, item: str) -> str:
    p = re.escape(parent)
    i = re.escape(item)
    pattern1 = rf'(<{p}>\n*)(<{i}[ >].*</{i}>)(\n*</{p}>)'
    pattern2 = rf'(?=<{i}[ >])'
    def replacer(m: re.Match[str]) -> str:
        group2 = ''.join(sorted(re.split(pattern2, m.group(2))))
        return f'{m.group(1)}[xml sorted]{group2}[/xml sorted]{m.group(3)}'
    return re.sub(pattern1, replacer, xml_spec, flags=re.DOTALL)


class _FailFast(BaseException): pass


class Cancelled(Exception):
    """Fake Cancelled used in tests to emulate the real ``trio.Cancelled``.
    This one has a public constructor and is a normal ``Exception``, to avoid
    having to deal with ``BaseException`` and ``CancelScope`` in test code that
    calls MockRunner.
    """
    __module__ = "trio"


class ConnectError(Exception):
    """Fake network error for ``httpx`` requests."""


class ConnectionError(Exception):
    """Fake network error for old ``requests`` requests."""


class HTTPError(Exception):
    """Fake status error for old ``requests`` requests. For simplicity, it's
    handled like network errors, even though that's not quite how it worked.
    """


class SSLError(Exception):
    """Fake network error for old ``requests`` requests. (``httpx`` does not
    raise SSLError.)
    """


HTTP_ERRORS = {
    'ConnectError': ConnectError,
    'ConnectionError': ConnectionError,
    'HTTPError': HTTPError,
    'SSLError': SSLError,
}


async def _scenario_main_async(
    run: Callable[[BaseClient], Awaitable[None]],
    anonymous: bool,
) -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument('--save', type=pathlib.Path, metavar='FILENAME',
        help='Output log file path')

    live_group = parser.add_argument_group(title='live mode options')
    live_group.add_argument('--ais-url', metavar='URL',
        help='AIS URL or hostname (required)')
    if not anonymous:
        live_group.add_argument('--params', type=pathlib.Path,
            metavar='FILENAME',
            help='Input JSON file with login params, should contain e.g. ' +
            '{"type":"saml_password","username":"...","password":"..."}, ' +
            'or set $AIS_PARAMS to a JSON string, ' +
            'or set $AIS_USERNAME and $AIS_PASSWORD')

    mock_group = parser.add_argument_group(title='mock mode options')
    mock_group.add_argument('--load', type=pathlib.Path, metavar='FILENAME',
        help='Input log file path (required)')
    mock_group.add_argument('--fail-fast', action='store_true',
        help='Do not continue past the first error/warning')

    options = parser.parse_args()

    body_failed = False

    async def body() -> None:
        await client.context.log('scenario', 'Scenario started')
        try:
            result = await run(client)
            await client.context.log('scenario', 'Scenario finished', result)
        except Exception as e:
            await client.context.log('scenario',
                f'Scenario failed with {type(e).__name__}',
                traceback.format_exc())
            nonlocal body_failed
            body_failed = True

    with contextlib.ExitStack() as es:
        if options.ais_url and options.load:
            parser.error('cannot use both --ais-url and --load')

        if not options.ais_url and not options.load:
            parser.error('either --ais-url or --load is required')

        if options.load:
            if not anonymous and options.params:
                parser.error('cannot use both --load and --params')

            with options.load.open() as f:
                entries = [LogEntry(*json.loads(line)) for line in f]

            client = WebuiClient(Context(ais_url=''))

            if options.save:
                client.context.logger.log_file = es.enter_context(
                    options.save.open('w'))

            ok = await MockRunner().run(
                body, entries, print=print,
                old_log=False, fail_fast=options.fail_fast)

            if ok:
                print('PASS')
            else:
                print('FAIL')
                sys.exit(1)

        if options.ais_url:
            if options.fail_fast:
                parser.error('cannot use both --ais-url and --fail-fast')

            ais_url = options.ais_url
            if '/' not in ais_url:
                ais_url = f'https://{ais_url}/'

            if anonymous:
                client = WebuiClient(Context(ais_url=ais_url))
            else:
                if options.params:
                    params = json.loads(options.params.read_text())
                elif (params_env := os.getenv('AIS_PARAMS')):
                    params = json.loads(params_env)
                elif (
                    (username := os.getenv('AIS_USERNAME')) and
                    (password := os.getenv('AIS_PASSWORD'))
                ):
                    params = ParamsDictSamlPassword(
                        type='saml_password',
                        username=username,
                        password=password,
                    )
                else:
                    parser.error('either --params or $AIS_PARAMS or ' +
                        '$AIS_USERNAME + $AIS_PASSWORD is required')

                server = ServerDict(
                    login_types=(params['type'],),
                    ais_url=ais_url,
                    ais_cookie='JSESSIONID',
                )
                client = await create_client(server, params)

            if options.save:
                client.context.logger.log_file = es.enter_context(
                    options.save.open('w'))
            else:
                client.context.logger.log_file = sys.stdout

            time.time = lambda: 0.0

            await body()

            if body_failed:
                sys.exit("Scenario failed")


def scenario_main(
    run: Callable[[BaseClient], Awaitable[None]], *,
    anonymous: bool=False,
) -> None:
    trio.run(_scenario_main_async, run, anonymous)
