"""
## The write() callable

https://peps.python.org/pep-0333/ (the WSGI PEP) says:

> Note: the `write()` callable is provided only to support certain existing
> frameworks' imperative output APIs; it should not be used by new applications
> or frameworks if it can be avoided.

> New WSGI applications and frameworks **should not** use the `write()` callable
> if it is possible to avoid doing so. The `write()` callable is strictly a hack
> to support imperative streaming APIs. In general, applications should produce
> their output via their returned iterable [...].

Votr uses write() anyway. We want dynamic immediate client side logging, because
it's useful for developers, and a little fun for users while they wait for AIS.
But almost every Votr function can log. The "proper" WSGI solution is to use
generators and `yield from` everywhere. The "proper" ASGI solution is to use
`async def` and `await` everywhere. But that's ugly and uncomfortable. So we use
write() instead. Fortunately, despite the warnings, all relevant WSGI servers
and middlewares support it.

## Error handling

We want to log both normal Exceptions and BaseExceptions. The most important
BaseException is SystemExit, because we use gunicorn's sync worker, which calls
sys.exit(1) in Worker.handle_abort() if a request times out. In this scenario we
want to log it and exit ASAP because the arbiter will probably SIGKILL us soon.
My guess is that file and local socket I/O is probably OK, but network I/O could
block or be too slow.

Less importantly, KeyboardInterrupt can happen when the dev server is Ctrl+C'd.
The other BaseExceptions are handled the same way, but they shouldn't happen.

Errors are logged to up to four destinations:

- To the user's session log, as JSON `[time, "rpc", "RPC ... failed with ...",
  traceback]`. (But not if the error happens too early or too late. The sessid
  must be known and the log file must be open.)

- To access.log. The HTTP status for /rpc is always 200 because it's sent before
  the actual RPC is called. That's not very useful for debugging. Instead we use
  a custom field `environ['votr.log_status']` and our gunicorn.conf.py is set up
  to read it with `%({votr.log_status}e)s` in `access_log_format`.

- To error.log, via `environ['wsgi.errors']`. (Mostly as a fallback for errors
  which couldn't be logged to the session log. See the code for details.)

- Sent to the client in up to 2 JSON messages. `{ "log": "rpc", ... }` which is
  only displayed in the navbar and log viewer, and `{ "error": ... }` which
  opens the error UI modal. (But not BaseExceptions and not if the client
  connection is already closed.)

## Known limits of error handling

Despite all this effort, it's not perfect.

I tried to handle all cases where at most 1 thing goes wrong. But if an error
happens while an earlier error is handled (while we're writing the first error
to the log, closing the log or session or lock, writing it to error.log, sending
JSON, etc.), it can sometimes be a problem (e.g. some logging might be skipped,
the lock might not be deleted, maybe the session or log could be corrupted).

If the first exception is a SystemExit, raising a second exception in some
`except ...:` or `finally:` block could override it and the program might not
actually exit.

Handling SystemExit is always a roll of the dice. They can happen anywhere and
leave the program in all kinds of unexpected states. Luckily, in practice there
is not much variety. Most happen in Context.request_ais() while waiting for AIS.
See also: https://docs.python.org/3/library/signal.html#handlers-and-exceptions
"""

import json
import traceback
from werkzeug.routing import Rule
from aisikl.exceptions import LoggedOutError
from votrfront import sessions
from votrfront.utils import check_header


def encode_result(thing):
    if isinstance(thing, tuple) and hasattr(thing, '_asdict'):
        thing = thing._asdict()

    if isinstance(thing, (list, tuple)):
        return [encode_result(item) for item in thing]
    if isinstance(thing, dict):
        return { key: encode_result(value) for key, value in thing.items() }
    return thing


class RpcHandler:
    def __init__(self, request):
        self.request = request
        self.write = None
        self.error_happened = False
        self.stop_sending_json = False
        self.capture_log = False
        self.captured_log = None
        self.stage = 'veryearly'

    def seen_error(self, e):
        self.error_happened = True
        if not isinstance(e, Exception):
            self.stop_sending_json = True

    def send_json(self, json_object):
        # Don't send anything to the client if a) an earlier send_json failed,
        # which probably means the client connection was closed, OR b) any
        # BaseException was raised and caught, which probably means we must exit
        # ASAP and it's safer to avoid network I/O (see file comment).
        if self.stop_sending_json: return

        try:
            payload = json.dumps(json_object).encode('ascii') + b'\n'
            header = ('%010d' % len(payload)).encode('ascii')
            self.write(header + payload)
        except Exception as e:
            # It's most likely an OSError (the client connection was closed).
            # Whether or not, don't try to send any JSON to the client again.
            self.stop_sending_json = True

            # If this is the first time something went wrong, reraise it. But
            # don't log it to wsgi.errors.
            # If we're already handling a previous exception, ignore this one.
            # It means we tried to tell the client about the original error, but
            # another error happened during that. The original error is more
            # important -- its type matters more in `except:` clauses, logging
            # of `type(e).__name__`, etc.
            if not self.error_happened:
                e.votr_rpc_dont_log_to_wsgi_errors = True
                raise
        # BaseException is not caught here. They should be reraised regardless
        # of error_happened, always be logged to wsgi.errors, and always stop
        # sending json (seen_error deals with that). So no need to catch them.

    def send_log(self, timestamp, type, message, data):
        json_object = { 'log': type, 'message': message, 'time': timestamp }
        if self.capture_log:
            self.capture_log = False
            self.captured_log = json_object
        else:
            self.send_json(json_object)

    def __call__(self, environ, start_response):
        try:
            # See the file comment about access.log. This initial value should
            # never be printed because it's overwritten below both on success
            # and on failure. If things are so bad/stuck/broken that neither of
            # them are executed, then the gunicorn code that writes to
            # access.log probably can't run either.
            environ['votr.log_status'] = 'rpc:wtf'

            # See the file comment about the write() callable.
            self.write = start_response('200 OK', [
                ('Content-Type', 'text/plain'),
                # Prevent https://code.google.com/p/chromium/issues/detail?id=2016
                # (onprogress only happening after the client receives 1024 bytes)
                # See also: ShouldSniffContent(), kMaxBytesToSniff
                ('X-Content-Type-Options', 'nosniff'),
            ])

            self.stage = 'early'

            with sessions.logged_transaction(self.request) as session:
                if self.request.headers.get('X-CSRF-Token') != session['csrf_token']:
                    raise ValueError('Bad X-CSRF-Token value')

                # 'names' is sent in the query string (not in the request body)
                # because it's nice to see them in web server logs.
                names = self.request.args['names'].split(',')
                argss = self.request.json

                if not isinstance(argss, list) or len(argss) != len(names):
                    raise ValueError('argss length does not match names length')

                current = self.request.app.settings.announcement_html
                if current != session.get('last_announcement', None):
                    self.send_json({ 'announcement_html': current })
                    session['last_announcement'] = current

                session['client'].context.logger.send_log = self.send_log

                for i, (name, args) in enumerate(zip(names, argss)):
                    self.stage = str(i+1)

                    # Context.log() calls 1. log_file.write(), 2. send_log().
                    # For this first log "RPC started", 1 should be outside the
                    # `try:` block and 2 inside it. I.e. if writing to log_file
                    # fails, don't write "RPC failed". If sending "RPC started"
                    # to the client fails, log "RPC failed" to log_file.
                    self.capture_log = True
                    session['client'].context.log(
                        'rpc', f'RPC {name} started', args)

                    try:
                        self.send_json(self.captured_log)
                        method = getattr(session['client'], name)
                        result = encode_result(method(*args))
                    except BaseException as e:
                        # See the file comment about catching BaseException too.
                        self.seen_error(e)
                        session['client'].context.log(
                            'rpc',
                            f'RPC {name} failed with {type(e).__name__}',
                            traceback.format_exc())
                        e.votr_rpc_dont_log_to_wsgi_errors = True
                        raise

                    # If writing this to log_file fails, we'll end up with an
                    # unmatched "RPC started". And if this send_json fails,
                    # log_file will look like a complete success. But oh well.
                    session['client'].context.log(
                        'rpc', f'RPC {name} finished', result)

                    self.send_json({ 'result': result })

                self.stage = 'late'

            environ['votr.log_status'] = 'rpc:ok'

        except BaseException as e:
            # See the file comment about catching BaseException too.
            self.seen_error(e)
            is_base_exception = not isinstance(e, Exception)

            # In all cases, write basic info to access.log (see file comment).
            kind = 'errbase' if is_base_exception else 'err'
            e_name = type(e).__name__
            environ['votr.log_status'] = f'rpc:{kind}:{e_name}:{self.stage}'

            # In some rare cases, write the full traceback to error.log.
            log_to_wsgi_errors = (
                # BaseException? Rare and scary. (I might change this later.)
                True if is_base_exception else
                # LoggedOutError? Expected and boring.
                False if isinstance(e, LoggedOutError) else
                # - Already logged to the session log? Don't log it again.
                # - Raised in send_json (e.g. sending announcement_html, result,
                #   or "RPC finished")? Unusual, but still expected and boring.
                not getattr(e, 'votr_rpc_dont_log_to_wsgi_errors', False)
            )
            if log_to_wsgi_errors:
                environ['wsgi.errors'].write(
                    f'RPC error:\n{traceback.format_exc()}')

            # If possible, send the error to the client. This shows the error
            # modal. Do it last, just in case the network I/O blocks or is slow.
            self.send_json({ 'error': traceback.format_exc() })

            # Reraise BaseExceptions such as SystemExit and KeyboardInterrupt.
            if is_base_exception:
                raise

        # Our whole output was written with write(), but WSGI applications
        # are required to return an iterable anyway.
        return []


def handle_rpc(request):
    check_header(request, 'Sec-Fetch-Site', { 'same-origin' })
    check_header(request, 'Sec-Fetch-Mode', { 'cors' })
    check_header(request, 'Sec-Fetch-Dest', { 'empty' })

    return RpcHandler(request)


def get_routes():
    yield Rule('/rpc', methods=['POST'], endpoint=handle_rpc)
