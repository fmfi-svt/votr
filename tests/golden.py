#!/usr/bin/env python3

import argparse
from collections import Counter
from dataclasses import dataclass
import json
import re
import sys
import traceback
import trio
from typing import Any, TYPE_CHECKING, cast
from aisikl.context import Context, Logger
from aisikl.typeutils import nn
from fladgejt.hybrid import HybridClient
from fladgejt.login import ServerDict, create_client
from fladgejt.webui import WebuiClient
from tests.testutils import LogEntry, MockRunner
from votrfront.rpc import encode_result

if TYPE_CHECKING:
    from fladgejt.base import BaseClient


@dataclass
class Options:
    old_log: bool
    fail_fast: bool
    verbose_pass: bool
    stats: Counter[str]

    def p(self, *lines: str) -> None:
        kind = nn(re.match(r'^ *([A-Z]+):', lines[0])).group(1)
        self.stats[kind] += 1
        print('\n'.join(lines), flush=True)


class LogTester:
    client: BaseClient | None = None
    login_is_old: bool = False

    async def test_request(self, o: Options, entries: list[LogEntry]) -> bool:
        start = entries[0]
        prefix = start.message[:-len(' started')]

        if start.type == 'login':
            if o.old_log and entries[1].message != 'Creating client':
                o.p('  SKIP: old login version')
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

            async def inner() -> object:
                await Logger().log('login', 'Creating client', entries[1].data)
                logintype: str = cast(Any, entries[1].data)['type']
                if (m := re.match(
                        r'^Requesting GET (http\S+/)ais/', entries[2].message)):
                    ais_url = m.group(1)
                else:
                    # Happens with type == 'cookie'.
                    ais_url = MockRunner.FAKE_AIS_URL
                server = ServerDict(
                    login_types=(logintype,),
                    ais_url=ais_url,
                    ais_cookie='JSESSIONID',
                )
                params: Any = dict(
                    type=logintype,
                    username='fake_value',
                    password='fake_value',
                    my_entity_id='fake_value',
                    andrvotr_api_key='fake_value',
                    andrvotr_authority_token='fake_value',
                    ais_cookie='fake_value',
                    rest_cookie='fake_value',
                )
                self.client = await create_client(server, params)
                return entries[-1].data
        elif start.type == 'logout':
            if self.login_is_old:
                o.p('  SKIP: old logout version')
                return True
            async def inner() -> object:
                await nn(self.client).logout()
                self.client = None
        elif start.type == 'front':
            async def inner() -> object:
                await nn(self.client).check_connection()
        elif start.type == 'rpc':
            async def inner() -> object:
                _, name = prefix.split(' ')
                client = nn(self.client)
                await client.prepare_for_rpc()
                method = getattr(client, name)
                args: Any = start.data
                return encode_result(await method(*args))

        async def body() -> None:
            await Logger().log(start.type, start.message, start.data)
            try:
                result = await inner()
                await Logger().log(start.type, f'{prefix} finished', result)
            except Exception as e:
                if start.type == 'rpc':
                    nn(self.client).last_rpc_failed = True
                await Logger().log(start.type, f'{prefix} failed with {type(e).__name__}', traceback.format_exc())

        printed: list[str] = []

        ok = await MockRunner().run(
            body, entries, print=printed.append,
            old_log=o.old_log, fail_fast=o.fail_fast)

        if ok and not o.verbose_pass:
            o.p(f'  PASS: {entries[-1].message}')
        else:
            o.p(f'  {'PASS' if ok else 'FAIL'}: {prefix} ' + '{{{',
                *('    ' + msg for msg in printed),
                '  }}}')

        return ok


async def test_log(o: Options, name: str, lines: list[bytes]) -> None:
    o.p(f'PROGRESS: testing {name}')

    try:
        tester = LogTester()

        entries = [LogEntry(*json.loads(line)) for line in lines]

        closes_apps_after_failure = False

        for entry in entries:
            if entry.type == 'flashback':
                o.p('  SKIP: log file is just a flashback')
                return
            if entry.message == 'Closing all open apps because of previous RPC error':
                closes_apps_after_failure = True

        last_start = None
        failed_test = False
        failed_rpc = False

        for i, entry in enumerate(entries):
            if entry.type in ('login', 'logout', 'front', 'rpc') and entry.message.endswith(' started'):
                if last_start is not None:
                    o.p('  ERROR: skipping bad log structure - request interrupted by another',
                        f'  ... {last_start+1}: {json.dumps(entries[last_start])}',
                        f'  ... {i+1}: {json.dumps(entry)}')
                    return
                last_start = i
            elif entry.type in ('login', 'logout', 'front', 'rpc') and (entry.message.endswith(' finished') or ' failed with ' in entry.message):
                if last_start is None:
                    o.p('  ERROR: skipping bad log structure - end without start',
                        f'  ... {i+1}: {json.dumps(entry)}')
                    return
                if entry.type != entries[last_start].type or not entry.message.startswith(entries[last_start].message[:-len('started')]):
                    o.p('  ERROR: skipping bad log structure - end does not match start',
                        f'  ... {last_start+1}: {json.dumps(entries[last_start])}',
                        f'  ... {i+1}: {json.dumps(entry)}')
                    return
                if o.fail_fast and failed_test:
                    o.p(f'  SKIP: skipping after failed test: {json.dumps(entries[last_start].message)}')
                elif o.old_log and failed_rpc and not closes_apps_after_failure and entry.type == 'rpc':
                    o.p(f'  SKIP: skipping after failed rpc: {json.dumps(entries[last_start].message)}')
                else:
                    if not await tester.test_request(o, entries[last_start:i + 1]):
                        failed_test = True
                    if entry.type == 'rpc' and ' failed with ' in entry.message:
                        failed_rpc = True
                last_start = None
            else:
                if last_start is None:
                    o.p(f'  WARNING: ignoring loose line {i+1}: {json.dumps(entry)}')

        if last_start is not None:
            o.p('  WARNING: skipping bad log structure - request did not finish, reached EOF',
                f'  ... {last_start+1}: {json.dumps(entries[last_start])}',
                f'  ... {len(entries)-1+1}: {json.dumps(entries[-1])}')

    except Exception:
        o.p(f'ERROR: uncaught exception in {name}',
            traceback.format_exc())


async def test_file(o: Options, filename: str) -> None:
    if '.tar.' in filename:
        import tarfile
        first = last = None
        if '@@' in filename:
            filename, ranges = filename.split('@@')
            if '..' in ranges:
                first, last = ranges.split('..')
            else:
                first = last = ranges
            first = first.split('/')[-1]
            last = last.split('/')[-1]
        with tarfile.open(filename, 'r:*') as tar:
            for info in tar:
                if not info.isreg():
                    o.p(f'WARNING: tar file entry has bad type: {info!r}')
                    continue
                if first and info.name.split('/')[-1][:len(first)] < first:
                    continue
                if last and info.name.split('/')[-1][:len(last)] > last:
                    break
                with nn(tar.extractfile(info)) as f:
                    await test_log(o, f'{filename}:{info.name}', list(f))
    elif filename.endswith('.gz'):
        import gzip
        with gzip.open(filename, 'rb') as f:
            await test_log(o, filename, list(f))
    elif filename.endswith('.xz'):
        import lzma
        with lzma.open(filename, 'rb') as f:
            await test_log(o, filename, list(f))
    else:
        with open(filename, 'rb') as f:
            await test_log(o, filename, list(f))


async def main(args: list[str]) -> None:
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

    o = Options(
        old_log=options.old_log,
        fail_fast=options.fail_fast,
        verbose_pass=options.verbose_pass,
        stats=Counter(),
    )

    for filename in options.log_filename:
        await test_file(o, filename)

    success = all(k in ('PROGRESS', 'PASS', 'SKIP') for k, v in o.stats.items() if v)
    print(
        'overall stats:',
        ', '.join(f'{v}x {k}' for k, v in sorted(o.stats.items()) if v),
        (' -->  success :D' if success else ' -->  failure :C'))
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    trio.run(main, sys.argv[1:])
