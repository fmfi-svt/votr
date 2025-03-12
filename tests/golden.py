#!/usr/bin/env python3

import argparse
import json
import re
import sys
import traceback
from aisikl.context import Context, Logger
from fladgejt.hybrid import HybridClient
from fladgejt.login import create_client
from fladgejt.webui import WebuiClient
from tests.testutils import LogEntry, MockRunner
from votrfront.rpc import encode_result


def p(msg):
    print(msg, flush=True)


class LogTester:
    def __init__(self, *, old_log, fail_fast, verbose_pass):
        self.old_log = old_log
        self.fail_fast = fail_fast
        self.verbose_pass = verbose_pass

        self.client = None
        self.login_is_old = False

    def test_request(self, entries):
        start = entries[0]
        prefix = start.message[:-len(' started')]

        if start.type == 'login':
            if self.old_log and entries[1].message != 'Creating client':
                p('  SKIP: old login version')
                if any(
                    isinstance(entry.data, str) and
                    entry.data.startswith('{"status":"OK",')
                    for entry in entries
                ):
                    self.client = HybridClient(Context(
                        ais_url=MockRunner.FAKE_AIS_URL,
                        rest_url=MockRunner.FAKE_REST_URL,
                    ))
                else:
                    self.client = WebuiClient(Context(
                        ais_url=MockRunner.FAKE_AIS_URL,
                    ))
                self.login_is_old = True
                return True

            def inner():
                Logger().log('login', 'Creating client', entries[1].data)
                logintype = entries[1].data['type']
                if (m := re.match(
                        r'^Requesting GET (http\S+/)ais/', entries[2].message)):
                    ais_url = m.group(1)
                else:
                    # Happens with type == 'cookie'.
                    ais_url = MockRunner.FAKE_AIS_URL
                server = dict(
                    login_types=(logintype,),
                    ais_url=ais_url,
                    ais_cookie='JSESSIONID',
                )
                params = dict(
                    type=logintype,
                    username='fake_value',
                    password='fake_value',
                    my_entity_id='fake_value',
                    andrvotr_api_key='fake_value',
                    andrvotr_authority_token='fake_value',
                    ais_cookie='fake_value',
                    rest_cookie='fake_value',
                )
                self.client = create_client(server, params)
                return entries[-1].data
        elif start.type == 'logout':
            if self.login_is_old:
                p('  SKIP: old logout version')
                return True
            def inner():
                self.client.logout()
                self.client = None
        elif start.type == 'front':
            def inner():
                self.client.check_connection()
        elif start.type == 'rpc':
            def inner():
                _, name = prefix.split(' ')
                self.client.prepare_for_rpc()
                method = getattr(self.client, name)
                return encode_result(method(*start.data))

        def body():
            Logger().log(start.type, start.message, start.data)
            try:
                result = inner()
                Logger().log(start.type, f'{prefix} finished', result)
            except Exception as e:
                if start.type == 'rpc':
                    self.client.last_rpc_failed = True
                Logger().log(start.type, f'{prefix} failed with {type(e).__name__}', traceback.format_exc())

        printed = []

        ok = MockRunner().run(
            body, entries, print=printed.append,
            old_log=self.old_log, fail_fast=self.fail_fast)

        if ok and not self.verbose_pass:
            p(f'  PASS: {entries[-1].message}')
        else:
            p(f'  {'PASS' if ok else 'FAIL'}: {prefix} ' + '{{{')
            for msg in printed:
                p('    ' + msg)
            p('  }}}')

        return ok


def test_log(name, lines, *, old_log, fail_fast, verbose_pass):
    p(f'PROGRESS: testing {name}')

    try:
        tester = LogTester(old_log=old_log, fail_fast=fail_fast, verbose_pass=verbose_pass)

        entries = [LogEntry(*json.loads(line)) for line in lines]

        closes_apps_after_failure = False

        for entry in entries:
            if entry.type == 'flashback':
                p('  SKIP: log file is just a flashback')
                return
            if entry.message == 'Closing all open apps because of previous RPC error':
                closes_apps_after_failure = True

        last_start = None
        failed_test = False
        failed_rpc = False

        for i, entry in enumerate(entries):
            if entry.type in ('login', 'logout', 'front', 'rpc') and entry.message.endswith(' started'):
                if last_start is not None:
                    p('  ERROR: skipping bad log structure - request interrupted by another')
                    p(f'  ... {last_start+1}: {json.dumps(entries[last_start])}')
                    p(f'  ... {i+1}: {json.dumps(entry)}')
                    return
                last_start = i
            elif entry.type in ('login', 'logout', 'front', 'rpc') and (entry.message.endswith(' finished') or ' failed with ' in entry.message):
                if last_start is None:
                    p('  ERROR: skipping bad log structure - end without start')
                    p(f'  ... {i+1}: {json.dumps(entry)}')
                    return
                if entry.type != entries[last_start].type or not entry.message.startswith(entries[last_start].message[:-len('started')]):
                    p('  ERROR: skipping bad log structure - end does not match start')
                    p(f'  ... {last_start+1}: {json.dumps(entries[last_start])}')
                    p(f'  ... {i+1}: {json.dumps(entry)}')
                    return
                if fail_fast and failed_test:
                    p(f'  SKIP: skipping after failed test: {json.dumps(entries[last_start].message)}')
                elif old_log and failed_rpc and not closes_apps_after_failure and entry.type == 'rpc':
                    p(f'  SKIP: skipping after failed rpc: {json.dumps(entries[last_start].message)}')
                else:
                    if not tester.test_request(entries[last_start:i + 1]):
                        failed_test = True
                    if entry.type == 'rpc' and ' failed with ' in entry.message:
                        failed_rpc = True
                last_start = None
            else:
                if last_start is None:
                    p(f'  WARNING: ignoring loose line {i+1}: {json.dumps(entry)}')

        if last_start is not None:
            p('  WARNING: skipping bad log structure - request did not finish, reached EOF')
            p(f'  ... {last_start+1}: {json.dumps(entries[last_start])}')
            p(f'  ... {len(entries)-1+1}: {json.dumps(entries[-1])}')

    except Exception:
        p(f'ERROR: uncaught exception in {name}')
        p(traceback.format_exc())


def test_file(filename, *, old_log, fail_fast, verbose_pass):
    if '.tar.' in filename:
        import tarfile
        first = last = None
        if '@@' in filename:
            filename, ranges = filename.split('@@')
            first, last = ranges.split('..')
        with tarfile.open(filename, 'r:*') as tar:
            for info in tar:
                if not info.isreg():
                    p(f'WARNING: tar file entry has bad type: {info!r}')
                    continue
                if first and info.name.split('/')[-1][:len(first)] < first:
                    continue
                if last and info.name.split('/')[-1][:len(last)] > last:
                    break
                with tar.extractfile(info) as f:
                    test_log(f'{filename}:{info.name}', list(f),
                        old_log=old_log, fail_fast=fail_fast,
                        verbose_pass=verbose_pass)
    elif filename.endswith('.gz'):
        import gzip
        with gzip.open(filename, 'rb') as f:
            test_log(filename, list(f),
                old_log=old_log, fail_fast=fail_fast, verbose_pass=verbose_pass)
    elif filename.endswith('.xz'):
        import lzma
        with lzma.open(filename, 'rb') as f:
            test_log(filename, list(f),
                old_log=old_log, fail_fast=fail_fast, verbose_pass=verbose_pass)
    else:
        with open(filename, 'rb') as f:
            test_log(filename, list(f),
                old_log=old_log, fail_fast=fail_fast, verbose_pass=verbose_pass)


def main(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('log_filename', nargs='+', help=
        'Input log file(s) to test. Can be compressed. ' +
        'For tar archives, "file.tar.xz@@aaa..bbb" ' +
        'can be used to only test sessids from aaa* to bbb*.')
    parser.add_argument('--old-log', action='store_true', help=
        'Allow some known differences in log content ' +
        'between old Votr and current Votr')
    parser.add_argument('--fail-fast', action='store_true', help=
        'End each log on the first error/warning, do not try to continue')
    parser.add_argument('--verbose-pass', action='store_true', help=
        'Show full details for RPCs/requests which pass')

    options = parser.parse_args(args)

    for filename in options.log_filename:
        test_file(filename, old_log=options.old_log,
            fail_fast=options.fail_fast, verbose_pass=options.verbose_pass)


if __name__ == '__main__':
    main(sys.argv[1:])
