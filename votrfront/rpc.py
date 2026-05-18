"""
## Cancellation

There are 6 known cases of cancellation. Let's give them these names:

- C1: Normal rpc_inner() completion (on success or normal error)
- C2: Client disconnected - received "http.disconnect"
- C3: Client disconnected - send() raised an error
- C4: (not implemented yet)
- C5: Timed out by our RequestTimeoutMiddleware
- C6: The web server is shutting down

Types C1-C4 cancel `main_nursery`: control flow continues after its `async with
open_nursery()` block. Types C5-C6 cancel some outer scope: from rpc.py's point
of view, it's an uncaught Cancelled exception.


## Disconnects

The ASGI spec has two ways to tell you the client has disconnected. One is
receiving a "http.disconnect" message:

> Once you have received this event, you should expect future calls to `send()`
> to raise an exception, as described above. However, if you have highly
> concurrent code, you may find calls to `send()` erroring slightly before you
> receive this event.

The other is OSError raised by send(). It was added in ASGI>=2.4, which is not
yet implemented by any ASGI server as of this writing, but we're ready for it.

> Applications may catch this exception and do cleanup work before re-raising
> it or returning with no exception.

Either way, in all ASGI servers: Once the client has disconnected, it doesn't
matter if you end by reraising the OSError or by returning None; it doesn't
matter if you [already sent / will send] a `"more_data": False` event or not;
it doesn't matter if you continue calling send() or avoid it.


## Error handling

Errors in rpc.py are logged to up to four destinations:

- To the user's session log, as JSON `[time, "rpc", "RPC ... failed with ...",
  traceback]`. This is done even if cancelled. But not if the error happens too
  early or too late (e.g. couldn't load/save the session).

- To access.log. The HTTP status code for /rpc is always 200 because we send it
  before calling the actual RPCs. That's not very useful for debugging. Instead
  we use a custom field, `request.state["votr_log_status"]`, which can change
  during the request. anycorn_config.py reads and logs its final value.

- To error.log, via Python `logging`, for especially weird errors.

- Sent to the client in up to 2 JSON messages: `{ "log": "rpc", "message": "RPC
  ... failed with ..." }` which is only displayed in the navbar and log viewer,
  and `{ "error": "..." }` which opens the error UI modal.

BaseExceptions other than Cancelled (see above) are mostly not handled.
KeyboardInterrupt might happen in development, but isn't too likely during an
RPC, and SIGKILL is an option if we get too stuck. In production, SIGTERM is
handled as a cancellation (called C6 here).

It is assumed that the environment is reasonable, e.g. `logging` calls can't
fail. That's of course not quite true, but it's sufficiently true.
"""

from aisikl.exceptions import LoggedOutError
import json
import logging
import traceback
import trio
from starlette.exceptions import HTTPException
from starlette.routing import Route
from starlette.requests import Request
from votrfront import sessions
from votrfront.utils import check_header

pylogger = logging.getLogger(__name__)


def encode_result(thing: object) -> object:
    if isinstance(thing, tuple) and hasattr(thing, '_asdict'):
        thing = thing._asdict()

    if isinstance(thing, (list, tuple)):
        return [encode_result(item) for item in thing]
    if isinstance(thing, dict):
        return { key: encode_result(value) for key, value in thing.items() }
    return thing


def serialize(json_object: object) -> bytes:
    payload = json.dumps(json_object).encode('ascii') + b'\n'
    return b"%010d%s" % (len(payload), payload)


async def rpc_inner(send, request, names, argss, session, cancel_main_nursery):
    async def send_json(json_object: object) -> None:
        # Check for cancellation. We use cancellation as a general "don't call
        # send() anymore" flag. This checkpoint might not be strictly necessary,
        # but let's do it just in case, because 1) Trio might not always raise
        # Cancelled immediately, and 2) although send() will make its own check
        # for cancellation, who knows if it does so right away.
        await trio.lowlevel.checkpoint()

        body = serialize(json_object)

        try:
            await send({
                "type": "http.response.body",
                "body": body,
                "more_body": True,
            })
        except Exception as exc:
            # In ASGI>=2.4, send() may raise OSError on client disconnects. We
            # react by cancelling main_nursery, which neatly prevents all
            # further send() calls; except for the final send() in rpc_asgi(),
            # which will probably raise OSError again, but that's ok.

            # BaseException is not caught here. There's no reason to: we have
            # nothing better to do with them than to just reraise them.

            if not isinstance(exc, OSError):
                # If it's not OSError, something is probably very broken, but
                # let's just log it and then use the same logic as for OSError.
                # Preventing further send() calls is a good reaction either way.
                pylogger.exception("send() raised a non-OSError?! WTF")

            exc_message = ''.join(traceback.format_exception_only(exc)).strip()
            cancel_main_nursery(f'send failed: {exc_message}')  # C3
            await trio.sleep_forever()  # actually raises Cancelled

    async def send_log(timestamp, type, message, data):
        await send_json({'log': type, 'message': message, 'time': timestamp})

    if not (client := session.get('client')):
        request.state['votr_log_status'] = 'rpc:session_error'
        await send_json({'error': 'LoggedOutError: Session is logged out'})
        return

    if request.headers.get('X-CSRF-Token') != session['csrf_token']:
        request.state['votr_log_status'] = 'rpc:session_error'
        await send_json({'error': 'CsrfTokenError: Bad X-CSRF-Token value'})
        return

    current = request.state['settings'].announcement_html
    if current != session.get('last_announcement', None):
        await send_json({ 'announcement_html': current })
        session['last_announcement'] = current

    client.context.logger.send_log = send_log

    for i, (name, args) in enumerate(zip(names, argss, strict=True)):

        request.state['votr_log_status'] = f'rpc:{i}:wtf'

        # This is the "inner try/except". It handles most RPC exceptions.
        #
        # It catches BaseException, but really, we only expect Cancelled and
        # Exception. Other BaseExceptions have low effort handling, and carry
        # some risk of getting masked, e.g. by Cancelled in send_log.
        #
        # Exception groups are not likely here. They're most commonly raised
        # by open_nursery(), which isn't called inside this try block.
        try:
            # Ackchyually, logging this *inside* the try block is not perfect.
            # log() will 1) write to the log file, 2) send_log(). Step 1 should
            # arguably happen outside the try block, because of the possibility
            # that writing "RPC started" to the log file fails, but writing "RPC
            # failed" to the log file succeeds. However, that's very unlikely.
            # It's more likely that step 1 of "RPC started" works, but step 2 of
            # "RPC started" raises Cancelled, in which case we'll want to catch
            # it and write "RPC failed with Cancelled" to the log file.
            await client.context.log('rpc', f'RPC {name} started', args)

            await client.prepare_for_rpc()
            method = getattr(client, name)
            result = encode_result(await method(*args))

        except BaseException as exc:
            client.last_rpc_failed = True

            exc_name = type(exc).__name__
            exc_trace = traceback.format_exc()
            request.state['votr_log_status'] = f'rpc:{i}:error:{exc_name}'

            # If exc is Cancelled, log() will probably raise another Cancelled,
            # but that's ok.
            await client.context.log(
                'rpc', f'RPC {name} failed with {exc_name}', exc_trace)

            if isinstance(exc, Exception):
                await send_json({ 'error': exc_trace })
                return
            else:
                raise

        # If writing this to log_file fails, we'll end up with an unmatched "RPC
        # started". And if this send_json fails, log_file will look like a
        # complete success. But oh well.
        await client.context.log('rpc', f'RPC {name} finished', result)

        await send_json({ 'result': result })

    request.state['votr_log_status'] = 'rpc:ok'


async def rpc_asgi(scope, receive, send):
    # Phase 1: Read request body and do basic checks. Errors in this phase are
    # dealt with normally - by raising a HTTPException. It is then caught and
    # handled by our `exception_handlers`.

    request = Request(scope, receive)

    request.state['votr_log_status'] = 'rpc:early_error'

    check_header(request, 'Sec-Fetch-Site', { 'same-origin' })
    check_header(request, 'Sec-Fetch-Mode', { 'cors' })
    check_header(request, 'Sec-Fetch-Dest', { 'empty' })

    # Read `names` and `argss`. `names` are sent in the query string (not in the
    # request body) because it's nice to see them in access logs.
    try:
        names = request.query_params['names'].split(',')
        argss = await request.json()
    except HTTPException:
        # Just in case. RequestBodyLimitMiddleware might raise this, maybe.
        raise
    except Exception as exc:
        exc_message = ''.join(traceback.format_exception_only(exc)).strip()
        raise HTTPException(400, exc_message) from exc

    if not isinstance(argss, list) or len(argss) != len(names):
        raise HTTPException(400, 'argss length does not match names length')

    # --------------------------------------------------------------------------
    #
    # Phase 2: Start sending the response now.
    #
    # We should not raise HTTPException after this point. (Both because it's
    # pointless, and because ExceptionMiddleware would complain.)

    # If this first send() raises OSError in ASGI>=2.4 because the client
    # disconnected just now, just let it propagate. No cleanup needed.
    await send({
        'type': 'http.response.start',
        'status': 200,
        'headers': [
            (b'content-type', b'text/plain'),
            # Prevent https://code.google.com/p/chromium/issues/detail?id=2016
            # (onprogress only happening after the client receives 1024 bytes)
            # See also: ShouldSniffContent(), kMaxBytesToSniff
            (b'x-content-type-options', b'nosniff'),
        ],
    })

    request.state['votr_log_status'] = 'rpc:setup_wtf'

    last_chunk = b''

    async def listen_for_disconnect() -> None:
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                break

        main_nursery.cancel_scope.cancel('received http.disconnect')  # C2

    # This is the "outer try/except". In theory, it catches e.g. unexpected
    # errors when loading/saving sessions. In practice, it should rarely if ever
    # catch anything, and arguably it might not really need to exist.
    #
    # Uses `except* Exception` because open_nursery() generally wraps everything
    # in groups. It catches bare Exceptions, ExceptionGroups, and the non-base
    # members of mixed BaseExceptionGroups.
    #
    # It won't catch:
    #   - Cancelled bound for an outer cancel scope (happens in cases C5, C6)
    #   - BaseExceptionGroup containing Cancelled (same as above)
    #   - other BaseExceptions or groups containing them (purely theoretical)
    # In those cases, the response stays unfinished => the ASGI server forcibly
    # closes the HTTP stream (e.g. in hypercorn & anycorn: StreamClosed without
    # EndBody) => our reverse proxy preserves that => the client surfaces it as
    # a network error (e.g. curl 18, XHR onerror). The end result is similar to
    # sending JSON {"error":...}, but displays a less specific error message in
    # the UI. That's not perfect (e.g. for C5), but it's good enough.
    try:
        async with trio.open_nursery() as main_nursery:
            main_nursery.start_soon(listen_for_disconnect)

            transaction_started = False
            try:
                async with sessions.logged_transaction(request) as session:
                    transaction_started = True
                    await rpc_inner(
                        send, request, names, argss, session,
                        main_nursery.cancel_scope.cancel)
            except LoggedOutError:
                # Catch expected session loading errors: "Invalid sessid",
                # "Session cookie not found", "Votr session does not exist".
                if not transaction_started:
                    request.state['votr_log_status'] = 'rpc:session_error'
                    last_chunk = serialize({'error': traceback.format_exc()})
                else:
                    raise

            main_nursery.cancel_scope.cancel()  # C1

        # If we get here, we might not know whether rpc_inner finished, or got
        # cancelled partway through, but either way the remaining cleanup is the
        # same.

    except* Exception as excgroup:
        request.state['votr_log_status'] += (
            ':outer_wtf:'
            + ','.join(type(exc).__name__ for exc in excgroup.exceptions))

        pylogger.exception('RPC fatal error WTF')

        last_chunk = serialize({'error': traceback.format_exc()})

    # --------------------------------------------------------------------------
    #
    # Phase 3: Close the response.
    #
    # In ASGI>=2.4, this send() might raise OSError. If it does, just let it
    # propagate through our middlewares (which will do nothing) to the server
    # (which swallows it). We could instead remember a flag that the client has
    # disconnected (C2, C3), in which case we'd skip the send() and just return,
    # but there's no benefit to doing that.
    #
    # A send() call in an except block can be dangerous (the OSError could mask
    # another error), but this one is not. Any exceptions we caught are already
    # logged; `last_chunk` is a nice-to-have.

    await send({
        'type': 'http.response.body',
        'body': last_chunk,
        'more_body': False,
    })


async def rpc_endpoint(request):
    return rpc_asgi


routes = [
    Route('/rpc', methods=['POST'], endpoint=rpc_endpoint),
]
